"""
CronForge - 任务执行器模块

负责实际执行定时任务命令，支持超时控制、
重试机制（指数退避）、执行结果捕获和执行时间统计。
"""

import subprocess
import time
import threading
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class ExecutionResult:
    """
    任务执行结果。

    Attributes:
        task_name: 任务名称
        command: 执行的命令
        exit_code: 退出码，None表示超时或异常
        stdout: 标准输出
        stderr: 标准错误输出
        duration: 执行时长（秒）
        timed_out: 是否超时
        retries: 实际重试次数
        success: 是否执行成功
    """

    task_name: str
    command: str
    exit_code: Optional[int]
    stdout: str
    stderr: str
    duration: float
    timed_out: bool
    retries: int
    success: bool


class TaskExecutor:
    """
    任务执行器。

    使用subprocess执行命令，支持超时控制、
    重试机制和结果捕获。

    Attributes:
        default_timeout: 默认超时时间（秒）
    """

    def __init__(self, default_timeout: int = 3600):
        """
        初始化任务执行器。

        Args:
            default_timeout: 默认超时时间（秒），0表示不限时
        """
        self.default_timeout = default_timeout
        self._running_tasks: dict = {}
        self._lock = threading.Lock()

    def execute(
        self,
        task_name: str,
        command: str,
        timeout: int = 0,
        retries: int = 0,
        retry_delay: int = 5,
    ) -> ExecutionResult:
        """
        执行任务命令。

        Args:
            task_name: 任务名称
            command: 要执行的命令
            timeout: 超时时间（秒），0表示不限时
            retries: 失败重试次数
            retry_delay: 重试间隔（秒）

        Returns:
            ExecutionResult: 执行结果
        """
        if timeout <= 0:
            timeout = self.default_timeout

        attempt = 0
        max_attempts = retries + 1
        last_result: Optional[ExecutionResult] = None

        while attempt < max_attempts:
            attempt += 1
            result = self._run_once(
                task_name=task_name,
                command=command,
                timeout=timeout,
                attempt=attempt,
            )
            last_result = result

            if result.success:
                result.retries = attempt - 1
                return result

            # 如果还有重试机会，等待后重试
            if attempt < max_attempts:
                # 指数退避：delay * 2^(attempt-1)
                delay = retry_delay * (2 ** (attempt - 1))
                time.sleep(delay)

        if last_result:
            last_result.retries = attempt - 1
        return last_result  # type: ignore

    def _run_once(
        self,
        task_name: str,
        command: str,
        timeout: int,
        attempt: int = 1,
    ) -> ExecutionResult:
        """
        执行一次命令。

        Args:
            task_name: 任务名称
            command: 要执行的命令
            timeout: 超时时间（秒）
            attempt: 当前尝试次数

        Returns:
            ExecutionResult: 执行结果
        """
        start_time = time.time()
        timed_out = False
        exit_code: Optional[int] = None
        stdout = ""
        stderr = ""

        try:
            # 使用subprocess执行命令
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # 注册运行中的任务
            with self._lock:
                self._running_tasks[task_name] = process

            try:
                stdout_bytes, stderr_bytes = process.communicate(
                    timeout=timeout if timeout > 0 else None
                )
                stdout = stdout_bytes or ""
                stderr = stderr_bytes or ""
                exit_code = process.returncode
            except subprocess.TimeoutExpired:
                timed_out = True
                process.kill()
                try:
                    stdout_bytes, stderr_bytes = process.communicate(timeout=5)
                    stdout = stdout_bytes or ""
                    stderr = stderr_bytes or ""
                except subprocess.TimeoutExpired:
                    pass
                exit_code = -1

        except Exception as e:
            stderr = str(e)
            exit_code = -1

        finally:
            # 移除运行中的任务
            with self._lock:
                self._running_tasks.pop(task_name, None)

        duration = time.time() - start_time
        success = exit_code == 0 and not timed_out

        return ExecutionResult(
            task_name=task_name,
            command=command,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration=duration,
            timed_out=timed_out,
            retries=0,
            success=success,
        )

    def is_running(self, task_name: str) -> bool:
        """
        检查任务是否正在运行。

        Args:
            task_name: 任务名称

        Returns:
            bool: 是否正在运行
        """
        with self._lock:
            return task_name in self._running_tasks

    def kill_task(self, task_name: str) -> bool:
        """
        终止正在运行的任务。

        Args:
            task_name: 任务名称

        Returns:
            bool: 是否成功终止
        """
        with self._lock:
            process = self._running_tasks.get(task_name)
            if process:
                try:
                    process.kill()
                    return True
                except Exception:
                    return False
        return False

    def get_running_tasks(self) -> list:
        """
        获取正在运行的任务列表。

        Returns:
            list: 正在运行的任务名称列表
        """
        with self._lock:
            return list(self._running_tasks.keys())
