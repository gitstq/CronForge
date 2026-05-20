"""
CronForge - Cron表达式解析器模块

支持标准5字段Cron表达式解析（分 时 日 月 周），
支持 *, ,, -, / 特殊字符，支持特殊别名如 @yearly, @daily 等。
提供表达式验证和下次执行时间计算功能。
"""

import re
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Set


# Cron字段定义：名称、最小值、最大值
FIELD_RANGES = {
    "minute": (0, 59),
    "hour": (0, 23),
    "day": (1, 31),
    "month": (1, 12),
    "weekday": (0, 6),  # 0=周日, 1=周一, ..., 6=周六
}

FIELD_NAMES = ["minute", "hour", "day", "month", "weekday"]

# 月份名称映射
MONTH_NAMES = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "may": 5, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

# 星期名称映射
WEEKDAY_NAMES = {
    "sun": 0, "mon": 1, "tue": 2, "wed": 3,
    "thu": 4, "fri": 5, "sat": 6,
}

# 特殊别名映射到标准Cron表达式
SPECIAL_ALIASES = {
    "@yearly": "0 0 1 1 *",
    "@annually": "0 0 1 1 *",
    "@monthly": "0 0 1 * *",
    "@weekly": "0 0 * * 0",
    "@daily": "0 0 * * *",
    "@midnight": "0 0 * * *",
    "@hourly": "0 * * * *",
}


class CronParseError(Exception):
    """Cron表达式解析错误"""
    pass


class CronExpression:
    """
    Cron表达式解析器。

    解析标准5字段Cron表达式并计算下次执行时间。

    Attributes:
        raw_expression: 原始表达式字符串
        fields: 解析后的字段值集合
        is_interval: 是否为固定间隔表达式（@every_Ns 等）
        interval_seconds: 固定间隔的秒数（仅当 is_interval 为 True 时有效）
    """

    def __init__(self, expression: str):
        """
        初始化Cron表达式解析器。

        Args:
            expression: Cron表达式字符串

        Raises:
            CronParseError: 表达式格式错误时抛出
        """
        self.raw_expression = expression.strip()
        self.fields: dict = {}
        self.is_interval: bool = False
        self.interval_seconds: int = 0
        self._parse()

    def _parse(self) -> None:
        """解析Cron表达式"""
        expr = self.raw_expression.lower()

        # 检查 @every_Ns/@every_Nm/@every_Nh 格式
        every_match = re.match(r"^@every_(\d+)([smh])$", expr)
        if every_match:
            value = int(every_match.group(1))
            unit = every_match.group(2)
            if unit == "s":
                self.interval_seconds = value
            elif unit == "m":
                self.interval_seconds = value * 60
            elif unit == "h":
                self.interval_seconds = value * 3600
            if self.interval_seconds <= 0:
                raise CronParseError(f"间隔时间必须大于0: {self.raw_expression}")
            self.is_interval = True
            return

        # 检查特殊别名
        if expr in SPECIAL_ALIASES:
            expr = SPECIAL_ALIASES[expr]

        # 分割字段
        parts = expr.split()
        if len(parts) != 5:
            raise CronParseError(
                f"Cron表达式必须包含5个字段（分 时 日 月 周），"
                f"当前有 {len(parts)} 个字段: {self.raw_expression}"
            )

        # 解析每个字段
        for i, field_name in enumerate(FIELD_NAMES):
            self.fields[field_name] = self._parse_field(
                parts[i], field_name, FIELD_RANGES[field_name]
            )

    def _parse_field(self, field: str, field_name: str, value_range: Tuple[int, int]) -> Set[int]:
        """
        解析单个Cron字段。

        Args:
            field: 字段字符串
            field_name: 字段名称
            value_range: 合法值范围 (min, max)

        Returns:
            Set[int]: 该字段匹配的所有值

        Raises:
            CronParseError: 字段格式错误时抛出
        """
        min_val, max_val = value_range
        result: Set[int] = set()

        # 处理逗号分隔的多个值
        for part in field.split(","):
            result.update(self._parse_part(part, field_name, min_val, max_val))

        if not result:
            raise CronParseError(f"字段 '{field_name}' 解析结果为空: {field}")

        # 验证值范围
        for val in result:
            if val < min_val or val > max_val:
                raise CronParseError(
                    f"字段 '{field_name}' 的值 {val} 超出范围 [{min_val}-{max_val}]"
                )

        return result

    def _parse_part(self, part: str, field_name: str, min_val: int, max_val: int) -> Set[int]:
        """
        解析字段的一部分（处理 *, -, / 运算符）。

        Args:
            part: 字段部分字符串
            field_name: 字段名称
            min_val: 最小值
            max_val: 最大值

        Returns:
            Set[int]: 匹配的值集合
        """
        # 处理 */N 步长格式
        if "/" in part:
            base, step_str = part.split("/", 1)
            try:
                step = int(step_str)
            except ValueError:
                raise CronParseError(f"步长必须是整数: {step_str}")
            if step <= 0:
                raise CronParseError(f"步长必须大于0: {step}")

            if base == "*":
                start = min_val
                end = max_val
            elif "-" in base:
                start_str, end_str = base.split("-", 1)
                start = self._resolve_value(start_str, field_name)
                end = self._resolve_value(end_str, field_name)
            else:
                start = self._resolve_value(base, field_name)
                end = max_val

            return set(range(start, end + 1, step))

        # 处理 * 通配符
        if part == "*":
            return set(range(min_val, max_val + 1))

        # 处理范围 N-M
        if "-" in part:
            start_str, end_str = part.split("-", 1)
            start = self._resolve_value(start_str, field_name)
            end = self._resolve_value(end_str, field_name)
            if start > end:
                raise CronParseError(
                    f"范围起始值 {start} 大于结束值 {end}: {part}"
                )
            return set(range(start, end + 1))

        # 处理单个值
        val = self._resolve_value(part, field_name)
        return {val}

    def _resolve_value(self, value_str: str, field_name: str) -> int:
        """
        将字符串值解析为整数，支持名称映射。

        Args:
            value_str: 值字符串
            field_name: 字段名称

        Returns:
            int: 解析后的整数值
        """
        value_str = value_str.strip()

        # 尝试直接转换为整数
        try:
            return int(value_str)
        except ValueError:
            pass

        # 月份名称映射
        if field_name == "month" and value_str in MONTH_NAMES:
            return MONTH_NAMES[value_str]

        # 星期名称映射
        if field_name == "weekday" and value_str in WEEKDAY_NAMES:
            return WEEKDAY_NAMES[value_str]

        raise CronParseError(
            f"无法解析字段 '{field_name}' 的值: '{value_str}'"
        )

    def matches(self, dt: datetime) -> bool:
        """
        判断给定时间是否匹配此Cron表达式。

        Args:
            dt: 日期时间对象

        Returns:
            bool: 是否匹配
        """
        if self.is_interval:
            return False  # 间隔类型不使用匹配方式

        return (
            dt.minute in self.fields["minute"]
            and dt.hour in self.fields["hour"]
            and dt.day in self.fields["day"]
            and dt.month in self.fields["month"]
            and (dt.weekday() + 1) % 7 in self.fields["weekday"]
            # Python weekday(): Monday=0, Sunday=6
            # Cron weekday: Sunday=0, Monday=1, ..., Saturday=6
            # 转换: (python_weekday + 1) % 7
        )

    def next_time(self, after: Optional[datetime] = None) -> datetime:
        """
        计算下次执行时间。

        Args:
            after: 起始时间，如果为 None 则使用当前时间

        Returns:
            datetime: 下次执行时间
        """
        if after is None:
            after = datetime.now()

        if self.is_interval:
            return after + timedelta(seconds=self.interval_seconds)

        # 从下一分钟开始搜索
        candidate = after.replace(second=0, microsecond=0) + timedelta(minutes=1)

        # 最大搜索范围：2年
        max_iterations = 525600  # 2年的分钟数
        for _ in range(max_iterations):
            if self._matches_all(candidate):
                return candidate
            candidate += timedelta(minutes=1)

        # 如果2年内找不到，返回一个远期时间
        return after + timedelta(days=365)

    def _matches_all(self, dt: datetime) -> bool:
        """
        检查时间是否匹配所有字段。

        Args:
            dt: 日期时间对象

        Returns:
            bool: 是否匹配
        """
        return (
            dt.minute in self.fields["minute"]
            and dt.hour in self.fields["hour"]
            and dt.day in self.fields["day"]
            and dt.month in self.fields["month"]
            and (dt.weekday() + 1) % 7 in self.fields["weekday"]
        )

    def __repr__(self) -> str:
        return f"CronExpression('{self.raw_expression}')"

    def __str__(self) -> str:
        return self.raw_expression


def validate_cron(expression: str) -> Tuple[bool, Optional[str]]:
    """
    验证Cron表达式是否合法。

    Args:
        expression: Cron表达式字符串

    Returns:
        Tuple[bool, Optional[str]]: (是否合法, 错误信息)
    """
    try:
        CronExpression(expression)
        return True, None
    except CronParseError as e:
        return False, str(e)


def parse_cron(expression: str) -> CronExpression:
    """
    解析Cron表达式。

    Args:
        expression: Cron表达式字符串

    Returns:
        CronExpression: 解析后的Cron表达式对象

    Raises:
        CronParseError: 表达式格式错误时抛出
    """
    return CronExpression(expression)


def get_next_times(expression: str, count: int = 5, after: Optional[datetime] = None) -> List[datetime]:
    """
    获取接下来的多次执行时间。

    Args:
        expression: Cron表达式字符串
        count: 需要获取的次数
        after: 起始时间

    Returns:
        List[datetime]: 执行时间列表
    """
    cron = CronExpression(expression)
    times = []
    current = after or datetime.now()
    for _ in range(count):
        current = cron.next_time(current)
        times.append(current)
    return times
