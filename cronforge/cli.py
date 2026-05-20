"""
CronForge - CLI入口模块

命令行界面入口，使用argparse实现子命令解析。
支持任务管理、调度控制、日志查看等功能。
"""

import argparse
import logging
import os
import sys
import signal
import time
from datetime import datetime
from typing import Optional

from cronforge import __version__
from cronforge.config import Config
from cronforge.cron_parser import CronExpression, validate_cron, get_next_times
from cronforge.humanize import humanize_cron
from cronforge.scheduler import Scheduler, SchedulerState
from cronforge.executor import TaskExecutor
from cronforge.logger import TaskLogger
from cronforge.notify import create_notifier
from cronforge.tui import TUIDashboard
from cronforge.task import Task
from cronforge.utils import (
    format_datetime,
    format_duration,
    input_with_default,
    confirm_prompt,
)


def setup_logging(verbose: bool = False) -> None:
    """
    配置日志。

    Args:
        verbose: 是否启用详细日志
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def create_parser() -> argparse.ArgumentParser:
    """
    创建命令行参数解析器。

    Returns:
        argparse.ArgumentParser: 参数解析器
    """
    parser = argparse.ArgumentParser(
        prog="cronforge",
        description="CronForge - 轻量级跨平台定时任务调度与管理引擎",
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"CronForge {__version__}",
    )
    parser.add_argument(
        "--config", "-c",
        help="指定配置文件路径",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="启用详细日志输出",
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # start 命令
    start_parser = subparsers.add_parser("start", help="启动调度器")
    start_parser.add_argument(
        "--tui", action="store_true",
        help="启动TUI面板",
    )
    start_parser.add_argument(
        "--daemon", "-d", action="store_true",
        help="以守护进程模式运行",
    )

    # list 命令
    subparsers.add_parser("list", help="列出所有任务")

    # add 命令
    subparsers.add_parser("add", help="交互式添加任务")

    # run 命令
    run_parser = subparsers.add_parser("run", help="立即执行指定任务")
    run_parser.add_argument("name", help="任务名称")

    # pause 命令
    pause_parser = subparsers.add_parser("pause", help="暂停任务")
    pause_parser.add_argument("name", help="任务名称")

    # resume 命令
    resume_parser = subparsers.add_parser("resume", help="恢复任务")
    resume_parser.add_argument("name", help="任务名称")

    # logs 命令
    logs_parser = subparsers.add_parser("logs", help="查看执行日志")
    logs_parser.add_argument("name", nargs="?", help="任务名称（可选）")
    logs_parser.add_argument("--limit", "-n", type=int, default=20, help="显示条数")
    logs_parser.add_argument("--failed", action="store_true", help="仅显示失败记录")

    # validate 命令
    validate_parser = subparsers.add_parser("validate", help="验证Cron表达式")
    validate_parser.add_argument("expr", help="Cron表达式")

    # humanize 命令
    humanize_parser = subparsers.add_parser("humanize", help="人类可读翻译")
    humanize_parser.add_argument("expr", help="Cron表达式")
    humanize_parser.add_argument(
        "--lang", "-l",
        choices=["cn", "en"],
        default="cn",
        help="语言 (cn/en)",
    )

    # init 命令
    init_parser = subparsers.add_parser("init", help="初始化配置文件")
    init_parser.add_argument(
        "--path", "-p",
        help="配置文件路径（默认: ./cronforge.yaml）",
    )

    # status 命令
    subparsers.add_parser("status", help="查看调度器状态")

    return parser


def cmd_init(args, config: Config) -> None:
    """处理 init 命令"""
    path = args.path or "./cronforge.yaml"
    if os.path.exists(path):
        if not confirm_prompt(f"配置文件 {path} 已存在，是否覆盖？"):
            print("已取消")
            return

    created_path = config.create_template(path)
    print(f"配置文件已创建: {created_path}")
    print("请编辑配置文件添加你的任务。")


def cmd_list(args, config: Config) -> None:
    """处理 list 命令"""
    if not config.tasks:
        print("暂无任务。请编辑配置文件或使用 'cronforge add' 添加任务。")
        return

    print(f"\n{'=' * 80}")
    print(f"  CronForge 任务列表 ({len(config.tasks)} 个任务)")
    print(f"{'=' * 80}\n")

    print(f"  {'名称':<18} {'Cron表达式':<16} {'启用':<6} {'标签':<15} {'描述'}")
    print(f"  {'-' * 75}")

    for task in config.tasks:
        enabled = "是" if task.enabled else "否"
        tags = ", ".join(task.tags) if task.tags else "-"
        desc = task.description[:30] if task.description else "-"
        print(
            f"  {task.name:<18} {task.cron_expr:<16} "
            f"{enabled:<6} {tags:<15} {desc}"
        )

    print()


def cmd_add(args, config: Config) -> None:
    """处理 add 命令"""
    print("\n=== 添加新任务 ===\n")

    name = input_with_default("任务名称")
    if not name:
        print("任务名称不能为空")
        return

    # 检查名称是否重复
    if config.get_task(name):
        print(f"任务 '{name}' 已存在")
        return

    command = input_with_default("执行命令")
    if not command:
        print("执行命令不能为空")
        return

    cron_expr = input_with_default("Cron表达式", "0 * * * *")
    # 验证表达式
    valid, error = validate_cron(cron_expr)
    if not valid:
        print(f"Cron表达式无效: {error}")
        return

    description = input_with_default("描述", "")
    tags_str = input_with_default("标签（逗号分隔）", "")
    tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []
    timeout = int(input_with_default("超时时间（秒）", "3600"))
    retries = int(input_with_default("重试次数", "0"))

    task = Task(
        name=name,
        command=command,
        cron_expr=cron_expr,
        timeout=timeout,
        retries=retries,
        tags=tags,
        description=description,
    )

    errors = task.validate()
    if errors:
        print(f"任务验证失败: {'; '.join(errors)}")
        return

    config.add_task(task)
    config.save()
    print(f"\n任务 '{name}' 已添加并保存到配置文件。")


def cmd_run(args, config: Config) -> None:
    """处理 run 命令"""
    task = config.get_task(args.name)
    if task is None:
        print(f"任务 '{args.name}' 不存在")
        return

    print(f"正在执行任务: {task.name}")
    print(f"命令: {task.command}\n")

    executor = TaskExecutor()
    result = executor.execute(
        task_name=task.name,
        command=task.command,
        timeout=task.timeout,
        retries=task.retries,
        retry_delay=task.retry_delay,
    )

    status = "成功" if result.success else "失败"
    print(f"\n执行结果: {status}")
    print(f"退出码: {result.exit_code}")
    print(f"耗时: {format_duration(result.duration)}")

    if result.stdout:
        print(f"\n--- stdout ---\n{result.stdout}")
    if result.stderr:
        print(f"\n--- stderr ---\n{result.stderr}")


def cmd_pause(args, config: Config) -> None:
    """处理 pause 命令"""
    task = config.get_task(args.name)
    if task is None:
        print(f"任务 '{args.name}' 不存在")
        return

    task.enabled = False
    config.save()
    print(f"任务 '{args.name}' 已暂停")


def cmd_resume(args, config: Config) -> None:
    """处理 resume 命令"""
    task = config.get_task(args.name)
    if task is None:
        print(f"任务 '{args.name}' 不存在")
        return

    task.enabled = True
    config.save()
    print(f"任务 '{args.name}' 已恢复")


def cmd_logs(args, config: Config) -> None:
    """处理 logs 命令"""
    db_path = config.get_log_db_path()
    if not os.path.exists(db_path):
        print("暂无执行日志")
        return

    task_logger = TaskLogger(db_path)
    logs = task_logger.query_logs(
        task_name=args.name,
        limit=args.limit,
        failure_only=args.failed,
    )

    if not logs:
        print("暂无执行日志")
        return

    print(f"\n{'=' * 90}")
    print(f"  执行日志 (最近 {len(logs)} 条)")
    print(f"{'=' * 90}\n")

    for log in logs:
        status = "成功" if log.get("success") else "失败"
        duration = format_duration(log.get("duration", 0))
        print(
            f"  [{log.get('started_at', '-')}] "
            f"{log.get('task_name', '-'):<18} "
            f"{status:<4} "
            f"耗时: {duration:<10} "
            f"退出码: {log.get('exit_code', '-')}"
        )
        if log.get("stderr"):
            stderr_preview = log["stderr"][:100].replace("\n", " ")
            print(f"    stderr: {stderr_preview}")
    print()


def cmd_validate(args) -> None:
    """处理 validate 命令"""
    valid, error = validate_cron(args.expr)
    if valid:
        print(f"表达式 '{args.expr}' 有效")
        # 显示接下来5次执行时间
        try:
            times = get_next_times(args.expr, count=5)
            print("\n接下来5次执行时间:")
            for i, t in enumerate(times, 1):
                print(f"  {i}. {t.strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception:
            pass
    else:
        print(f"表达式 '{args.expr}' 无效: {error}")


def cmd_humanize(args) -> None:
    """处理 humanize 命令"""
    result = humanize_cron(args.expr, lang=args.lang)
    print(f"表达式: {args.expr}")
    print(f"描述: {result}")


def cmd_status(args, config: Config) -> None:
    """处理 status 命令"""
    print(f"\nCronForge 状态")
    print(f"{'=' * 40}")
    print(f"  版本: {__version__}")
    print(f"  配置文件: {config.config_path or '未加载'}")
    print(f"  任务数量: {len(config.tasks)}")
    print(f"  启用任务: {sum(1 for t in config.tasks if t.enabled)}")
    print(f"  日志数据库: {config.get_log_db_path()}")

    # 日志统计
    db_path = config.get_log_db_path()
    if os.path.exists(db_path):
        try:
            task_logger = TaskLogger(db_path)
            stats = task_logger.get_statistics()
            print(f"\n  执行统计:")
            print(f"    总执行次数: {stats.get('total_runs', 0)}")
            print(f"    成功次数: {stats.get('success_count', 0)}")
            print(f"    失败次数: {stats.get('failure_count', 0)}")
            print(f"    成功率: {stats.get('success_rate', 0):.1f}%")
            avg_duration = stats.get('avg_duration', 0) or 0
            print(f"    平均耗时: {format_duration(avg_duration)}")
        except Exception:
            pass

    print()


def cmd_start(args, config: Config) -> None:
    """处理 start 命令"""
    setup_logging(args.verbose if hasattr(args, 'verbose') else False)
    logger = logging.getLogger("cronforge")

    if not config.tasks:
        print("配置文件中没有任务。请先添加任务。")
        return

    # 创建日志记录器
    task_logger = TaskLogger(config.get_log_db_path())

    # 创建通知器
    notifier = create_notifier(config.global_config)

    # 创建调度器
    scheduler = Scheduler(
        task_logger=task_logger,
        notifier=notifier,
        poll_interval=1.0,
    )

    # 添加任务
    for task in config.tasks:
        scheduler.add_task(task)

    # 信号处理
    def signal_handler(sig, frame):
        logger.info("收到停止信号，正在停止调度器...")
        scheduler.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if args.tui:
        # TUI模式
        dashboard = TUIDashboard(
            get_tasks_info=scheduler.get_all_tasks_info,
            get_state=lambda: scheduler.state,
            on_run_task=lambda name: scheduler.run_task_now(name),
            on_pause=scheduler.pause,
            on_resume=scheduler.resume,
        )

        scheduler.start(daemon=True)
        logger.info("调度器已启动（TUI模式）")

        try:
            dashboard.start()
        except KeyboardInterrupt:
            pass
        finally:
            scheduler.stop()
    else:
        # 普通模式
        scheduler.start(daemon=False)
        logger.info("调度器已启动，按 Ctrl+C 停止")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("正在停止调度器...")
            scheduler.stop()


def main() -> None:
    """CLI主入口"""
    parser = create_parser()
    args = parser.parse_args()

    # 没有子命令时显示帮助
    if not args.command:
        parser.print_help()
        return

    # 设置日志
    verbose = getattr(args, 'verbose', False)
    setup_logging(verbose)

    # 加载配置（部分命令不需要配置）
    config = Config()
    needs_config = args.command not in ("validate", "humanize", "init")

    if needs_config:
        try:
            config.load(getattr(args, 'config', None))
        except FileNotFoundError as e:
            print(f"错误: {e}")
            sys.exit(1)

    # 分发命令
    if args.command == "init":
        cmd_init(args, config)
    elif args.command == "list":
        cmd_list(args, config)
    elif args.command == "add":
        cmd_add(args, config)
    elif args.command == "run":
        cmd_run(args, config)
    elif args.command == "pause":
        cmd_pause(args, config)
    elif args.command == "resume":
        cmd_resume(args, config)
    elif args.command == "logs":
        cmd_logs(args, config)
    elif args.command == "validate":
        cmd_validate(args)
    elif args.command == "humanize":
        cmd_humanize(args)
    elif args.command == "status":
        cmd_status(args, config)
    elif args.command == "start":
        cmd_start(args, config)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
