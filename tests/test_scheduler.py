"""
CronForge - 任务调度引擎测试

测试任务调度逻辑、启用/禁用、立即执行等功能。
"""

import unittest
import os
import tempfile
import time
import threading
from datetime import datetime

from cronforge.task import Task
from cronforge.scheduler import Scheduler, SchedulerState
from cronforge.logger import TaskLogger


class TestSchedulerBasic(unittest.TestCase):
    """测试调度器基本功能"""

    def setUp(self):
        """测试初始化"""
        self.scheduler = Scheduler(poll_interval=0.1)

    def test_add_task(self):
        """测试添加任务"""
        task = Task(
            name="test-task",
            command="echo hello",
            cron_expr="* * * * *",
        )
        self.scheduler.add_task(task)
        self.assertIn("test-task", self.scheduler.tasks)

    def test_remove_task(self):
        """测试移除任务"""
        task = Task(
            name="test-task",
            command="echo hello",
            cron_expr="* * * * *",
        )
        self.scheduler.add_task(task)
        self.assertTrue(self.scheduler.remove_task("test-task"))
        self.assertNotIn("test-task", self.scheduler.tasks)

    def test_remove_nonexistent_task(self):
        """测试移除不存在的任务"""
        self.assertFalse(self.scheduler.remove_task("nonexistent"))

    def test_enable_task(self):
        """测试启用任务"""
        task = Task(
            name="test-task",
            command="echo hello",
            cron_expr="* * * * *",
            enabled=False,
        )
        self.scheduler.add_task(task)
        self.assertFalse(self.scheduler.tasks["test-task"].enabled)
        self.scheduler.enable_task("test-task")
        self.assertTrue(self.scheduler.tasks["test-task"].enabled)

    def test_disable_task(self):
        """测试禁用任务"""
        task = Task(
            name="test-task",
            command="echo hello",
            cron_expr="* * * * *",
            enabled=True,
        )
        self.scheduler.add_task(task)
        self.scheduler.disable_task("test-task")
        self.assertFalse(self.scheduler.tasks["test-task"].enabled)

    def test_enable_nonexistent_task(self):
        """测试启用不存在的任务"""
        self.assertFalse(self.scheduler.enable_task("nonexistent"))

    def test_disable_nonexistent_task(self):
        """测试禁用不存在的任务"""
        self.assertFalse(self.scheduler.disable_task("nonexistent"))


class TestSchedulerExecution(unittest.TestCase):
    """测试任务执行"""

    def setUp(self):
        """测试初始化"""
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.task_logger = TaskLogger(self.db_path)
        self.scheduler = Scheduler(
            task_logger=self.task_logger,
            poll_interval=0.1,
        )

    def tearDown(self):
        """测试清理"""
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_run_task_now(self):
        """测试立即执行任务"""
        task = Task(
            name="echo-test",
            command="echo hello",
            cron_expr="* * * * *",
            timeout=10,
        )
        self.scheduler.add_task(task)
        result = self.scheduler.run_task_now("echo-test")

        self.assertIsNotNone(result)
        self.assertTrue(result.success)
        self.assertIn("hello", result.stdout)

    def test_run_nonexistent_task(self):
        """测试执行不存在的任务"""
        result = self.scheduler.run_task_now("nonexistent")
        self.assertIsNone(result)

    def test_run_task_with_timeout(self):
        """测试超时执行"""
        task = Task(
            name="timeout-test",
            command="sleep 10",
            cron_expr="* * * * *",
            timeout=1,
        )
        self.scheduler.add_task(task)
        result = self.scheduler.run_task_now("timeout-test")

        self.assertIsNotNone(result)
        self.assertTrue(result.timed_out)

    def test_run_task_with_retries(self):
        """测试重试机制"""
        task = Task(
            name="retry-test",
            command="exit 1",
            cron_expr="* * * * *",
            timeout=5,
            retries=2,
            retry_delay=1,
        )
        self.scheduler.add_task(task)
        result = self.scheduler.run_task_now("retry-test")

        self.assertIsNotNone(result)
        self.assertFalse(result.success)
        self.assertEqual(result.retries, 2)

    def test_task_logging(self):
        """测试任务日志记录"""
        task = Task(
            name="log-test",
            command="echo logged",
            cron_expr="* * * * *",
            timeout=10,
        )
        self.scheduler.add_task(task)
        self.scheduler.run_task_now("log-test")

        # 查询日志
        logs = self.task_logger.query_logs(task_name="log-test")
        self.assertEqual(len(logs), 1)
        self.assertTrue(logs[0]["success"])
        self.assertIn("logged", logs[0]["stdout"])


class TestSchedulerLifecycle(unittest.TestCase):
    """测试调度器生命周期"""

    def test_initial_state(self):
        """测试初始状态"""
        scheduler = Scheduler()
        self.assertEqual(scheduler.state, SchedulerState.STOPPED)

    def test_start_and_stop(self):
        """测试启动和停止"""
        scheduler = Scheduler(poll_interval=0.1)
        task = Task(
            name="test-task",
            command="echo test",
            cron_expr="@every_10s",
        )
        scheduler.add_task(task)

        scheduler.start(daemon=True)
        self.assertEqual(scheduler.state, SchedulerState.RUNNING)

        time.sleep(0.3)

        scheduler.stop(timeout=5)
        self.assertEqual(scheduler.state, SchedulerState.STOPPED)

    def test_pause_and_resume(self):
        """测试暂停和恢复"""
        scheduler = Scheduler(poll_interval=0.1)
        scheduler.start(daemon=True)
        self.assertEqual(scheduler.state, SchedulerState.RUNNING)

        scheduler.pause()
        self.assertEqual(scheduler.state, SchedulerState.PAUSED)

        scheduler.resume()
        self.assertEqual(scheduler.state, SchedulerState.RUNNING)

        scheduler.stop(timeout=5)


class TestSchedulerTaskInfo(unittest.TestCase):
    """测试任务信息查询"""

    def test_get_task_info(self):
        """测试获取任务信息"""
        scheduler = Scheduler()
        task = Task(
            name="info-test",
            command="echo info",
            cron_expr="0 9 * * *",
            tags=["test"],
            description="测试任务",
        )
        scheduler.add_task(task)

        info = scheduler.get_task_info("info-test")
        self.assertIsNotNone(info)
        self.assertEqual(info["name"], "info-test")
        self.assertEqual(info["command"], "echo info")
        self.assertEqual(info["cron_expr"], "0 9 * * *")
        self.assertTrue(info["enabled"])

    def test_get_all_tasks_info(self):
        """测试获取所有任务信息"""
        scheduler = Scheduler()
        task1 = Task(name="task1", command="echo 1", cron_expr="* * * * *")
        task2 = Task(name="task2", command="echo 2", cron_expr="@hourly")
        scheduler.add_task(task1)
        scheduler.add_task(task2)

        infos = scheduler.get_all_tasks_info()
        self.assertEqual(len(infos), 2)
        names = {info["name"] for info in infos}
        self.assertEqual(names, {"task1", "task2"})


if __name__ == "__main__":
    unittest.main()
