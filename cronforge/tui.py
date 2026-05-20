"""
CronForge - TUI Dashboard模块

使用curses实现终端UI面板，显示任务列表、状态、
下次执行时间，支持实时刷新和键盘操作。
如果curses不可用则降级为纯文本输出。
"""

import sys
import threading
import time
from datetime import datetime
from typing import Optional, Dict, List, Callable

from cronforge.utils import format_datetime, format_duration

# 尝试导入curses
try:
    import curses
    CURSES_AVAILABLE = True
except ImportError:
    CURSES_AVAILABLE = False


class TUIDashboard:
    """
    TUI终端面板。

    使用curses库实现交互式终端界面，显示任务调度状态。
    如果curses不可用，自动降级为纯文本输出。

    Attributes:
        get_tasks_info: 获取任务信息的回调函数
        get_state: 获取调度器状态的回调函数
        on_run_task: 立即执行任务的回调函数
        on_pause: 暂停调度器的回调函数
        on_resume: 恢复调度器的回调函数
    """

    def __init__(
        self,
        get_tasks_info: Callable[[], List[Dict]],
        get_state: Callable[[], str],
        on_run_task: Optional[Callable[[str], None]] = None,
        on_pause: Optional[Callable[[], None]] = None,
        on_resume: Optional[Callable[[], None]] = None,
    ):
        """
        初始化TUI面板。

        Args:
            get_tasks_info: 获取任务信息的回调函数
            get_state: 获取调度器状态的回调函数
            on_run_task: 立即执行任务的回调函数
            on_pause: 暂停调度器的回调函数
            on_resume: 恢复调度器的回调函数
        """
        self.get_tasks_info = get_tasks_info
        self.get_state = get_state
        self.on_run_task = on_run_task
        self.on_pause = on_pause
        self.on_resume = on_resume
        self._running = False
        self._selected = 0
        self._message = ""
        self._message_time = 0

    def start(self) -> None:
        """启动TUI面板"""
        if not CURSES_AVAILABLE:
            self._start_text_mode()
            return

        try:
            curses.wrapper(self._curses_main)
        except Exception as e:
            print(f"TUI启动失败: {e}，切换到文本模式")
            self._start_text_mode()

    def stop(self) -> None:
        """停止TUI面板"""
        self._running = False

    def _start_text_mode(self) -> None:
        """文本模式输出"""
        self._running = True
        print("\n=== CronForge Dashboard (文本模式) ===")
        print("按 Ctrl+C 退出\n")

        try:
            while self._running:
                self._render_text()
                time.sleep(2)
        except KeyboardInterrupt:
            self._running = False
            print("\n已退出Dashboard")

    def _render_text(self) -> None:
        """渲染文本模式输出"""
        # 使用ANSI转义码清屏
        print("\033[2J\033[H", end="")
        print("=" * 70)
        print(f"  CronForge Dashboard  |  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  调度器状态: {self.get_state().upper()}")
        print("=" * 70)

        tasks = self.get_tasks_info()
        if not tasks:
            print("\n  暂无任务\n")
        else:
            print(f"\n  {'序号':<4} {'任务名称':<20} {'状态':<8} {'启用':<6} {'下次执行':<20}")
            print("  " + "-" * 62)
            for i, task in enumerate(tasks):
                status = task.get("status", "idle")
                enabled = "是" if task.get("enabled", True) else "否"
                next_run = format_datetime(task.get("next_run"))
                name = task.get("name", "unknown")[:18]

                status_display = {
                    "running": "运行中",
                    "idle": "空闲",
                    "failed": "失败",
                }.get(status, status)

                print(
                    f"  {i + 1:<4} {name:<20} {status_display:<8} "
                    f"{enabled:<6} {next_run:<20}"
                )

        print("\n" + "=" * 70)

    def _curses_main(self, stdscr) -> None:
        """
        curses主循环。

        Args:
            stdscr: curses标准屏幕对象
        """
        curses.curs_set(0)  # 隐藏光标
        stdscr.nodelay(True)  # 非阻塞输入
        stdscr.timeout(500)  # 刷新间隔（毫秒）

        self._running = True

        while self._running:
            # 处理键盘输入
            try:
                key = stdscr.getch()
                self._handle_key(key, stdscr)
            except Exception:
                pass

            # 渲染界面
            self._render_curses(stdscr)

            # 检查窗口大小
            try:
                stdscr.refresh()
            except Exception:
                break

    def _handle_key(self, key: int, stdscr) -> None:
        """
        处理键盘输入。

        Args:
            key: 按键码
            stdscr: curses屏幕对象
        """
        tasks = self.get_tasks_info()

        if key == ord("q") or key == ord("Q"):
            self._running = False
        elif key == curses.KEY_UP or key == ord("k"):
            self._selected = max(0, self._selected - 1)
        elif key == curses.KEY_DOWN or key == ord("j"):
            self._selected = min(len(tasks) - 1, self._selected + 1)
        elif key == ord("r") or key == ord("R"):
            # 立即执行选中任务
            if tasks and 0 <= self._selected < len(tasks):
                name = tasks[self._selected].get("name", "")
                if self.on_run_task:
                    self.on_run_task(name)
                    self._set_message(f"已触发任务: {name}")
        elif key == ord("p") or key == ord("P"):
            # 暂停/恢复
            state = self.get_state()
            if state == "running" and self.on_pause:
                self.on_pause()
                self._set_message("调度器已暂停")
            elif state == "paused" and self.on_resume:
                self.on_resume()
                self._set_message("调度器已恢复")

    def _set_message(self, msg: str) -> None:
        """设置状态栏消息"""
        self._message = msg
        self._message_time = time.time()

    def _render_curses(self, stdscr) -> None:
        """
        渲染curses界面。

        Args:
            stdscr: curses屏幕对象
        """
        height, width = stdscr.getmaxyx()
        stdscr.clear()

        # 标题栏
        title = f" CronForge Dashboard | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} "
        state = self.get_state()
        state_color = {
            "running": "运行中",
            "paused": "已暂停",
            "stopped": "已停止",
        }.get(state, state)

        try:
            stdscr.addstr(0, 0, title[:width - 1], curses.A_REVERSE)
            stdscr.addstr(1, 0, f" 状态: {state_color} | 按 r 执行, p 暂停/恢复, q 退出"[:width - 1])
        except curses.error:
            pass

        # 表头
        header = f" {'#':<3} {'任务名称':<18} {'状态':<8} {'启用':<5} {'下次执行':<20}"
        try:
            stdscr.addstr(3, 0, header[:width - 1], curses.A_BOLD)
            stdscr.addstr(4, 0, "-" * min(width - 1, 70))
        except curses.error:
            pass

        # 任务列表
        tasks = self.get_tasks_info()
        for i, task in enumerate(tasks):
            y = 5 + i
            if y >= height - 2:
                break

            name = task.get("name", "unknown")[:16]
            status = task.get("status", "idle")
            enabled = "是" if task.get("enabled", True) else "否"
            next_run = format_datetime(task.get("next_run"))

            status_display = {
                "running": "运行中",
                "idle": "空闲",
                "failed": "失败",
            }.get(status, status)

            line = f" {i + 1:<3} {name:<18} {status_display:<8} {enabled:<5} {next_run:<20}"

            attr = 0
            if i == self._selected:
                attr = curses.A_REVERSE
            elif status == "running":
                attr = curses.A_BOLD
            elif status == "failed":
                attr = curses.A_DIM

            try:
                stdscr.addstr(y, 0, line[:width - 1], attr)
            except curses.error:
                pass

        # 状态栏
        if self._message and time.time() - self._message_time < 5:
            try:
                stdscr.addstr(height - 1, 0, f" {self._message}"[:width - 1], curses.A_REVERSE)
            except curses.error:
                pass

    def get_text_output(self) -> str:
        """
        获取纯文本格式的面板输出。

        Returns:
            str: 文本格式的面板内容
        """
        lines = []
        lines.append("=" * 60)
        lines.append(f"  CronForge Dashboard")
        lines.append(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"  状态: {self.get_state().upper()}")
        lines.append("=" * 60)

        tasks = self.get_tasks_info()
        if not tasks:
            lines.append("\n  暂无任务\n")
        else:
            lines.append(
                f"\n  {'任务名称':<20} {'状态':<8} {'启用':<6} {'下次执行':<20}"
            )
            lines.append("  " + "-" * 56)
            for task in tasks:
                name = task.get("name", "unknown")[:18]
                status = task.get("status", "idle")
                enabled = "是" if task.get("enabled", True) else "否"
                next_run = format_datetime(task.get("next_run"))

                status_display = {
                    "running": "运行中",
                    "idle": "空闲",
                    "failed": "失败",
                }.get(status, status)

                lines.append(
                    f"  {name:<20} {status_display:<8} "
                    f"{enabled:<6} {next_run:<20}"
                )

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)
