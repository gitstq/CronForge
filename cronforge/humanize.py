"""
CronForge - Cron表达式人类可读翻译模块

将Cron表达式翻译为人类可读的中文和英文描述。
例如 "0 9 * * 1-5" 翻译为 "每周一至周五上午9:00"。
"""

from typing import Optional, Tuple

from cronforge.cron_parser import CronExpression, SPECIAL_ALIASES


# 星期名称映射
WEEKDAY_CN = {
    0: "日", 1: "一", 2: "二", 3: "三",
    4: "四", 5: "五", 6: "六",
}

WEEKDAY_EN = {
    0: "Sunday", 1: "Monday", 2: "Tuesday", 3: "Wednesday",
    4: "Thursday", 5: "Friday", 6: "Saturday",
}

MONTH_CN = {
    1: "一月", 2: "二月", 3: "三月", 4: "四月",
    5: "五月", 6: "六月", 7: "七月", 8: "八月",
    9: "九月", 10: "十月", 11: "十一月", 12: "十二月",
}


def _format_time_cn(hour: int, minute: int) -> str:
    """
    格式化中文时间描述。

    Args:
        hour: 小时
        minute: 分钟

    Returns:
        str: 中文时间描述
    """
    if minute == 0:
        if hour == 0:
            return "午夜12:00"
        elif hour == 12:
            return "中午12:00"
        elif hour < 12:
            return f"上午{hour}:00"
        else:
            return f"下午{hour - 12}:00"
    else:
        if hour == 0:
            return f"午夜12:{minute:02d}"
        elif hour == 12:
            return f"中午12:{minute:02d}"
        elif hour < 12:
            return f"上午{hour}:{minute:02d}"
        else:
            return f"下午{hour - 12}:{minute:02d}"


def _format_time_en(hour: int, minute: int) -> str:
    """
    格式化英文时间描述。

    Args:
        hour: 小时
        minute: 分钟

    Returns:
        str: 英文时间描述
    """
    if hour == 0:
        h = 12
        period = "AM"
    elif hour < 12:
        h = hour
        period = "AM"
    elif hour == 12:
        h = 12
        period = "PM"
    else:
        h = hour - 12
        period = "PM"

    if minute == 0:
        return f"{h}:00 {period}"
    return f"{h}:{minute:02d} {period}"


def _describe_field_cn(values: set, field_name: str) -> str:
    """
    生成字段的中文描述。

    Args:
        values: 字段值集合
        field_name: 字段名称

    Returns:
        str: 中文描述
    """
    if field_name == "minute":
        return ""  # 分钟通常和时间一起描述

    if field_name == "hour":
        return ""  # 小时通常和时间一起描述

    if field_name == "day":
        min_val, max_val = 1, 31
        if values == set(range(min_val, max_val + 1)):
            return ""
        sorted_vals = sorted(values)
        if len(sorted_vals) == 1:
            return f"每月{sorted_vals[0]}日"
        return f"每月{','.join(str(v) for v in sorted_vals)}日"

    if field_name == "month":
        min_val, max_val = 1, 12
        if values == set(range(min_val, max_val + 1)):
            return ""
        sorted_vals = sorted(values)
        if len(sorted_vals) == 1:
            return MONTH_CN.get(sorted_vals[0], f"{sorted_vals[0]}月")
        return "、".join(MONTH_CN.get(v, f"{v}月") for v in sorted_vals)

    if field_name == "weekday":
        min_val, max_val = 0, 6
        if values == set(range(min_val, max_val + 1)):
            return ""
        sorted_vals = sorted(values)
        if len(sorted_vals) == 1:
            return f"每周{WEEKDAY_CN.get(sorted_vals[0], str(sorted_vals[0]))}"
        # 检查是否连续
        is_contiguous = all(
            sorted_vals[i] + 1 == sorted_vals[i + 1]
            for i in range(len(sorted_vals) - 1)
        )
        if is_contiguous and len(sorted_vals) > 1:
            start = WEEKDAY_CN.get(sorted_vals[0], str(sorted_vals[0]))
            end = WEEKDAY_CN.get(sorted_vals[-1], str(sorted_vals[-1]))
            return f"每周{start}至周{end}"
        return "每周" + "、周".join(
            WEEKDAY_CN.get(v, str(v)) for v in sorted_vals
        )

    return ""


def _describe_field_en(values: set, field_name: str) -> str:
    """
    生成字段的英文描述。

    Args:
        values: 字段值集合
        field_name: 字段名称

    Returns:
        str: 英文描述
    """
    if field_name in ("minute", "hour"):
        return ""

    if field_name == "day":
        min_val, max_val = 1, 31
        if values == set(range(min_val, max_val + 1)):
            return ""
        sorted_vals = sorted(values)
        if len(sorted_vals) == 1:
            return f"on day {sorted_vals[0]} of the month"
        return f"on days {','.join(str(v) for v in sorted_vals)}"

    if field_name == "month":
        min_val, max_val = 1, 12
        if values == set(range(min_val, max_val + 1)):
            return ""
        sorted_vals = sorted(values)
        month_names = [
            "", "January", "February", "March", "April",
            "May", "June", "July", "August",
            "September", "October", "November", "December"
        ]
        names = [month_names[v] for v in sorted_vals if 1 <= v <= 12]
        return "in " + ", ".join(names)

    if field_name == "weekday":
        min_val, max_val = 0, 6
        if values == set(range(min_val, max_val + 1)):
            return ""
        sorted_vals = sorted(values)
        names = [WEEKDAY_EN.get(v, str(v)) for v in sorted_vals]
        if len(names) == 1:
            return f"every {names[0]}"
        return "every " + ", ".join(names)

    return ""


def humanize_cron(expression: str, lang: str = "cn") -> str:
    """
    将Cron表达式翻译为人类可读的描述。

    Args:
        expression: Cron表达式字符串
        lang: 语言，"cn" 为中文，"en" 为英文

    Returns:
        str: 人类可读的描述

    Examples:
        >>> humanize_cron("0 9 * * 1-5", "cn")
        '每周一至周五上午9:00'
        >>> humanize_cron("0 9 * * 1-5", "en")
        'At 9:00 AM, every Monday through Friday'
    """
    expr_lower = expression.strip().lower()

    # 处理特殊别名
    alias_descriptions_cn = {
        "@yearly": "每年1月1日午夜12:00",
        "@annually": "每年1月1日午夜12:00",
        "@monthly": "每月1日午夜12:00",
        "@weekly": "每周日午夜12:00",
        "@daily": "每天午夜12:00",
        "@midnight": "每天午夜12:00",
        "@hourly": "每小时整点",
    }
    alias_descriptions_en = {
        "@yearly": "Once a year, at midnight on January 1st",
        "@annually": "Once a year, at midnight on January 1st",
        "@monthly": "Once a month, at midnight on the 1st",
        "@weekly": "Once a week, at midnight on Sunday",
        "@daily": "Every day at midnight",
        "@midnight": "Every day at midnight",
        "@hourly": "Every hour, on the hour",
    }

    if expr_lower in alias_descriptions_cn:
        if lang == "cn":
            return alias_descriptions_cn[expr_lower]
        return alias_descriptions_en[expr_lower]

    # 处理 @every_Ns/@every_Nm/@every_Nh
    import re
    every_match = re.match(r"^@every_(\d+)([smh])$", expr_lower)
    if every_match:
        value = int(every_match.group(1))
        unit = every_match.group(2)
        if lang == "cn":
            unit_cn = {"s": "秒", "m": "分钟", "h": "小时"}
            return f"每隔{value}{unit_cn[unit]}"
        else:
            unit_en = {"s": "second(s)", "m": "minute(s)", "h": "hour(s)"}
            return f"Every {value} {unit_en[unit]}"

    # 解析标准Cron表达式
    try:
        cron = CronExpression(expression)
    except Exception:
        return f"[无法解析: {expression}]"

    if cron.is_interval:
        if lang == "cn":
            return f"每隔{cron.interval_seconds}秒"
        return f"Every {cron.interval_seconds} seconds"

    # 获取各字段值
    minutes = cron.fields.get("minute", set())
    hours = cron.fields.get("hour", set())
    days = cron.fields.get("day", set())
    months = cron.fields.get("month", set())
    weekdays = cron.fields.get("weekday", set())

    if lang == "cn":
        return _humanize_cn(minutes, hours, days, months, weekdays)
    return _humanize_en(minutes, hours, days, months, weekdays)


def _humanize_cn(
    minutes: set,
    hours: set,
    days: set,
    months: set,
    weekdays: set,
) -> str:
    """
    生成中文人类可读描述。

    Args:
        minutes: 分钟值集合
        hours: 小时值集合
        days: 日期值集合
        months: 月份值集合
        weekdays: 星期值集合

    Returns:
        str: 中文描述
    """
    parts = []

    # 月份描述
    month_desc = _describe_field_cn(months, "month")
    if month_desc:
        parts.append(month_desc)

    # 星期描述
    weekday_desc = _describe_field_cn(weekdays, "weekday")

    # 日期描述（仅在无星期时显示）
    day_desc = ""
    if not weekday_desc:
        day_desc = _describe_field_cn(days, "day")
        if day_desc:
            parts.append(day_desc)
    else:
        parts.append(weekday_desc)

    # 时间描述
    all_minutes = set(range(0, 60))
    all_hours = set(range(0, 24))

    if hours == all_hours and minutes == all_minutes:
        parts.append("每分钟")
    elif hours == all_hours:
        # 每小时的特定分钟
        sorted_mins = sorted(minutes)
        if len(sorted_mins) == 1:
            parts.append(f"每小时的第{sorted_mins[0]}分钟")
        else:
            parts.append(f"每小时的第{','.join(str(m) for m in sorted_mins)}分钟")
    elif minutes == all_minutes:
        sorted_hours = sorted(hours)
        if len(sorted_hours) == 1:
            parts.append(f"{sorted_hours[0]}时每分钟")
        else:
            parts.append("、" .join(f"{h}时" for h in sorted_hours) + "每分钟")
    else:
        # 特定时间点
        sorted_hours = sorted(hours)
        sorted_mins = sorted(minutes)

        if len(sorted_hours) == 1 and len(sorted_mins) == 1:
            time_str = _format_time_cn(sorted_hours[0], sorted_mins[0])
            # 如果没有其他描述，加"每天"
            if not parts:
                parts.append(f"每天{time_str}")
            else:
                parts.append(time_str)
        elif len(sorted_hours) == 1:
            time_str = _format_time_cn(sorted_hours[0], sorted_mins[0])
            if len(sorted_mins) <= 5:
                min_strs = ",".join(f"{m:02d}" for m in sorted_mins)
                if not parts:
                    parts.append(f"每天{sorted_hours[0]}:{min_strs}")
                else:
                    parts.append(f"{sorted_hours[0]}:{min_strs}")
            else:
                if not parts:
                    parts.append(f"每天{time_str}")
                else:
                    parts.append(time_str)
        else:
            if not parts:
                parts.append("每天")
            time_strs = []
            for h in sorted_hours:
                for m in sorted_mins:
                    time_strs.append(f"{h}:{m:02d}")
            if len(time_strs) <= 5:
                parts.append("、".join(time_strs))
            else:
                parts.append(f"多个时间点({len(time_strs)}个)")

    return "".join(parts) if parts else "每分钟"


def _humanize_en(
    minutes: set,
    hours: set,
    days: set,
    months: set,
    weekdays: set,
) -> str:
    """
    生成英文人类可读描述。

    Args:
        minutes: 分钟值集合
        hours: 小时值集合
        days: 日期值集合
        months: 月份值集合
        weekdays: 星期值集合

    Returns:
        str: 英文描述
    """
    parts = []

    # 时间部分
    all_minutes = set(range(0, 60))
    all_hours = set(range(0, 24))

    if hours == all_hours and minutes == all_minutes:
        parts.append("Every minute")
    elif hours == all_hours:
        sorted_mins = sorted(minutes)
        if len(sorted_mins) == 1:
            parts.append(f"At every minute {sorted_mins[0]}")
        else:
            parts.append(f"At minutes {','.join(str(m) for m in sorted_mins)}")
    elif minutes == all_minutes:
        sorted_hours = sorted(hours)
        if len(sorted_hours) == 1:
            parts.append(f"Every minute of hour {sorted_hours[0]}")
        else:
            parts.append(f"Every minute during hours {','.join(str(h) for h in sorted_hours)}")
    else:
        sorted_hours = sorted(hours)
        sorted_mins = sorted(minutes)
        if len(sorted_hours) == 1 and len(sorted_mins) == 1:
            parts.append(f"At {_format_time_en(sorted_hours[0], sorted_mins[0])}")
        else:
            time_parts = []
            for h in sorted_hours:
                for m in sorted_mins:
                    time_parts.append(_format_time_en(h, m))
            if len(time_parts) <= 5:
                parts.append("At " + ", ".join(time_parts))
            else:
                parts.append(f"At multiple times ({len(time_parts)} occurrences)")

    # 月份
    month_desc = _describe_field_en(months, "month")
    if month_desc:
        parts.append(month_desc)

    # 星期
    weekday_desc = _describe_field_en(weekdays, "weekday")

    # 日期
    if not weekday_desc:
        day_desc = _describe_field_en(days, "day")
        if day_desc:
            parts.append(day_desc)
    else:
        parts.append(weekday_desc)

    return ", ".join(parts) if parts else "Every minute"
