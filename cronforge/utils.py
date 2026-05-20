"""
CronForge - 工具函数模块

提供项目中通用的工具函数，包括时间格式化、
字符串处理、文件路径操作等。
"""

import os
import sys
from datetime import datetime, timezone, timedelta
from typing import Optional, Any, Dict


def get_local_timezone() -> timezone:
    """
    获取本地时区。

    Returns:
        timezone: 本地时区对象
    """
    # 尝试获取系统本地时区偏移
    utc_offset = datetime.now().astimezone().utcoffset()
    if utc_offset is not None:
        return timezone(utc_offset)
    return timezone.utc


def now_tz(tz: Optional[timezone] = None) -> datetime:
    """
    获取带时区的当前时间。

    Args:
        tz: 时区对象，如果为 None 则使用本地时区

    Returns:
        datetime: 带时区的当前时间
    """
    if tz is None:
        tz = get_local_timezone()
    return datetime.now(tz)


def format_datetime(dt: Optional[datetime], fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    格式化日期时间。

    Args:
        dt: 日期时间对象，如果为 None 返回 '-'
        fmt: 格式化字符串

    Returns:
        str: 格式化后的时间字符串
    """
    if dt is None:
        return "-"
    return dt.strftime(fmt)


def format_duration(seconds: float) -> str:
    """
    格式化持续时间。

    Args:
        seconds: 秒数

    Returns:
        str: 人类可读的持续时间字符串
    """
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m{secs:.0f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h{minutes}m"


def truncate_string(s: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    截断字符串到指定长度。

    Args:
        s: 原始字符串
        max_length: 最大长度
        suffix: 截断后缀

    Returns:
        str: 截断后的字符串
    """
    if len(s) <= max_length:
        return s
    return s[: max_length - len(suffix)] + suffix


def ensure_directory(path: str) -> None:
    """
    确保目录存在，不存在则创建。

    Args:
        path: 目录路径
    """
    os.makedirs(path, exist_ok=True)


def safe_get(data: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    """
    安全地从嵌套字典中获取值。

    Args:
        data: 字典数据
        keys: 键的路径
        default: 默认值

    Returns:
        Any: 获取到的值或默认值
    """
    current = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def confirm_prompt(message: str, default: bool = False) -> bool:
    """
    显示确认提示。

    Args:
        message: 提示信息
        default: 默认值

    Returns:
        bool: 用户确认结果
    """
    suffix = " [Y/n] " if default else " [y/N] "
    try:
        response = input(message + suffix).strip().lower()
        if not response:
            return default
        return response in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        print()
        return default


def input_with_default(prompt: str, default: str = "") -> str:
    """
    带默认值的输入。

    Args:
        prompt: 提示信息
        default: 默认值

    Returns:
        str: 用户输入或默认值
    """
    try:
        display_prompt = f"{prompt}"
        if default:
            display_prompt += f" [{default}]"
        display_prompt += ": "
        value = input(display_prompt).strip()
        return value if value else default
    except (EOFError, KeyboardInterrupt):
        print()
        return default
