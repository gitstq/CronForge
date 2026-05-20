"""
CronForge - 任务调度引擎模块

基于时间轮询的任务调度引擎，支持任务的启用/禁用、
立即执行、重叠检测和优雅停止。
"""

import threading
import time
import logging
from datetime import datetime
from typing import Dict, Optional, Callable, List

from cronforge.cron_parser import CronExpression
from cronforge.task import Task
from cronforge.executor import TaskExecutor, ExecutionResult
from cronforge.logger import TaskLogger
from cronforge.notify import WebhookNotifier, create_notifier

logger = logging.getLogger("cronforge")


class SchedulerState:
    """调度器状态枚举"""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"


class Scheduler:
    """
    任务调度引擎。

    基于时间轮询方式检查和执行定时任务，
    支持多线程执行、重叠检测和优雅停止。

    Attributes:
        tasks: 任务字典 {name: Task}
        state: 调度器当前状态
        executor: 任务执行器
        task_logger: 日志记录器
    """

    def __init__(
        self,
        task_logger: Optional[TaskLogger] = None,
        notifier: Optional[WebhookNotifier] = None,
        poll_interval: float = 1.0,
        overlap_policy: str = "skip",
    ):
        """
        初始化调度引擎。

        Args:
            task_logger: 日志记录器实例
            notifier: 通知器实例
            poll_interval: 轮询间隔（秒）
            overlap_policy: 重叠策略，"skip" 跳过或 "queue" 排队
        """
        self.tasks: Dict[str, Task] = {}
        self.state: str = SchedulerState.STOPPED
        self.executor = TaskExecutor()
        self.task_logger = task_logger
        self.notifier = notifier
        self.poll_interval = poll_interval
        self.overlap_policy = overlap_policy

        # 内部状态
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._cron_cache: Dict[str, CronExpression] = {}
        self._last_run: Dict[str, datetime] = {}
        self._next_run: Dict[str, datetime] = {}
        self._lock = threading.RLock()
        self._task_status: Dict[str, str] = {}  # 任务运行状态

    def add_task(self, task: Task) -> None:
        """
        添加任务到调度器。

        Args:
            task: 任务对象
        """
        with self._lock:
            self.tasks[task.name] = task
            # 预解析Cron表达式
            try:
                self._cron_cache[task.name] = CronExpression(task.cron_expr)
            except Exception:
                pass
            self._task_status[task.name] = "idle"

    def remove_task(self, name: str) -> bool:
        """
        从调度器移除任务。

        Args:
            name: 任务名称

        Returns:
            bool: 是否成功移除
        """
        with self._lock:
            if name in self.tasks:
                del self.tasks[name]
                self._cron_cache.pop(name, None)
                self._last_run.pop(name, None)
                self._next_run.pop(name, None)
                self._task_status.pop(name, None)
                return True
            return False

    def enable_task(self, name: str) -> bool:
        """
        启用任务。

        Args:
            name: 任务名称

        Returns:
            bool: 是否成功
        """
        with self._lock:
            if name in self.tasks:
                self.tasks[name].enabled = True
                return True
            return False

    def disable_task(self, name: str) -> bool:
        """
        禁用任务。

        Args:
            name: 任务名称

        Returns:
            bool: 是否成功
        """
        with self._lock:
            if name in self.tasks:
                self.tasks[name].enabled = False
                return True
            return False

    def start(self, daemon: bool = True) -> None:
        """
        启动调度器。

        Args:
            daemon: 是否以守护线程运行
        """
        if self.state == SchedulerState.RUNNING:
            logger.warning("调度器已在运行中")
            return

        self.state = SchedulerState.RUNNING
        self._stop_event.clear()

        # 计算所有任务的下次执行时间
        self._update_next_runs()

        self._thread = threading.Thread(target=self._run_loop, daemon=daemon)
        self._thread.start()
        logger.info("调度器已启动")

    def stop(self, timeout: float = 30.0) -> None:
        """
        优雅停止调度器。

        Args:
            timeout: 等待超时时间（秒）
        """
        if self.state != SchedulerState.RUNNING:
            return

        logger.info("正在停止调度器...")
        self._stop_event.set()
        self.state = SchedulerState.STOPPED

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)
            if self._thread.is_alive():
                logger.warning("调度器线程未能在超时时间内停止")

        logger.info("调度器已停止")

    def pause(self) -> None:
        """暂停调度器"""
        if self.state == SchedulerState.RUNNING:
            self.state = SchedulerState.PAUSED
            logger.info("调度器已暂停")

    def resume(self) -> None:
        """恢复调度器"""
        if self.state == SchedulerState.PAUSED:
            self.state = SchedulerState.RUNNING
            self._update_next_runs()
            logger.info("调度器已恢复")

    def run_task_now(self, name: str) -> Optional[ExecutionResult]:
        """
        立即执行指定任务。

        Args:
            name: 任务名称

        Returns:
            Optional[ExecutionResult]: 执行结果，任务不存在返回 None
        """
        with self._lock:
            task = self.tasks.get(name)

        if task is None:
            logger.error(f"任务不存在: {name}")
            return None

        return self._execute_task(task)

    def get_task_info(self, name: str) -> Optional[Dict]:
        """
        获取任务信息。

        Args:
            name: 任务名称

        Returns:
            Optional[Dict]: 任务信息字典
        """
        with self._lock:
            task = self.tasks.get(name)
            if task is None:
                return None

            return {
                "name": task.name,
                "command": task.command,
                "cron_expr": task.cron_expr,
                "enabled": task.enabled,
                "status": self._task_status.get(name, "idle"),
                "last_run": self._last_run.get(name),
                "next_run": self._next_run.get(name),
                "timeout": task.timeout,
                "retries": task.retries,
                "tags": task.tags,
                "description": task.description,
            }

    def get_all_tasks_info(self) -> List[Dict]:
        """
        获取所有任务信息。

        Returns:
            List[Dict]: 任务信息列表
        """
        result = []
        with self._lock:
            for name in self.tasks:
                info = self.get_task_info(name)
                if info:
                    result.append(info)
        return result

    def _update_next_runs(self) -> None:
        """更新所有任务的下次执行时间"""
        now = datetime.now()
        with self._lock:
            for name, task in self.tasks.items():
                if task.enabled:
                    cron = self._cron_cache.get(name)
                    if cron:
                        try:
                            self._next_run[name] = cron.next_time(now)
                        except Exception:
                            pass

    def _run_loop(self) -> None:
        """调度器主循环"""
        while not self._stop_event.is_set():
            try:
                if self.state == SchedulerState.RUNNING:
                    self._check_and_execute()
                self._stop_event.wait(self.poll_interval)
            except Exception as e:
                logger.error(f"调度循环错误: {e}")
                time.sleep(1)

    def _check_and_execute(self) -> None:
        """检查并执行到期的任务"""
        now = datetime.now()
        now_no_sec = now.replace(second=0, microsecond=0)

        with self._lock:
            tasks_to_run = []
            for name, task in self.tasks.items():
                if not task.enabled:
                    continue

                cron = self._cron_cache.get(name)
                if cron is None:
                    continue

                if cron.is_interval:
                    # 间隔类型检查
                    last = self._last_run.get(name)
                    if last is None:
                        tasks_to_run.append(task)
                    else:
                        from datetime import timedelta
                        next_expected = last + timedelta(seconds=cron.interval_seconds)
                        if now >= next_expected:
                            tasks_to_run.append(task)
                else:
                    # 标准Cron检查
                    if cron._matches_all(now_no_sec):
                        # 避免同一分钟内重复执行
                        last = self._last_run.get(name)
                        if last and last.replace(second=0, microsecond=0) == now_no_sec:
                            continue
                        tasks_to_run.append(task)

        # 在锁外执行任务
        for task in tasks_to_run:
            # 重叠检测
            if self.overlap_policy == "skip" and self.executor.is_running(task.name):
                logger.info(f"任务 {task.name} 正在运行中，跳过本次执行")
                continue

            # 在新线程中执行
            t = threading.Thread(
                target=self._execute_task_thread,
                args=(task,),
                daemon=True,
            )
            t.start()

        # 更新下次执行时间
        self._update_next_runs()

    def _execute_task_thread(self, task: Task) -> None:
        """
        在独立线程中执行任务。

        Args:
            task: 任务对象
        """
        self._execute_task(task)

    def _execute_task(self, task: Task) -> ExecutionResult:
        """
        执行单个任务。

        Args:
            task: 任务对象

        Returns:
            ExecutionResult: 执行结果
        """
        with self._lock:
            self._task_status[task.name] = "running"

        logger.info(f"开始执行任务: {task.name} ({task.command})")
        start_time = datetime.now()

        try:
            result = self.executor.execute(
                task_name=task.name,
                command=task.command,
                timeout=task.timeout,
                retries=task.retries,
                retry_delay=task.retry_delay,
            )
        except Exception as e:
            logger.error(f"任务 {task.name} 执行异常: {e}")
            result = ExecutionResult(
                task_name=task.name,
                command=task.command,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                duration=0,
                timed_out=False,
                retries=0,
                success=False,
            )

        end_time = datetime.now()

        # 更新状态
        with self._lock:
            self._last_run[task.name] = start_time
            self._task_status[task.name] = "idle" if result.success else "failed"

        # 记录日志
        if self.task_logger:
            try:
                self.task_logger.log_execution(
                    task_name=task.name,
                    command=task.command,
                    exit_code=result.exit_code,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    duration=result.duration,
                    timed_out=result.timed_out,
                    retries=result.retries,
                    success=result.success,
                    started_at=start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    finished_at=end_time.strftime("%Y-%m-%d %H:%M:%S"),
                )
            except Exception as e:
                logger.error(f"记录日志失败: {e}")

        # 发送通知
        if self.notifier:
            try:
                event = "on_success" if result.success else "on_failure"
                self.notifier.notify(
                    task_name=task.name,
                    event=event,
                    result={
                        "command": result.command,
                        "exit_code": result.exit_code,
                        "duration": result.duration,
                        "timed_out": result.timed_out,
                        "retries": result.retries,
                        "success": result.success,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                    },
                )
            except Exception as e:
                logger.error(f"发送通知失败: {e}")

        status_str = "成功" if result.success else "失败"
        logger.info(
            f"任务 {task.name} 执行{status_str}，"
            f"耗时 {result.duration:.2f}s"
        )

        return result
