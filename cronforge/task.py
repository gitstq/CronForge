"""
CronForge - 任务模型模块

定义定时任务的数据模型，包含任务的所有属性，
支持任务的序列化与反序列化操作。
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


@dataclass
class Task:
    """
    定时任务数据类。

    表示一个完整的定时任务配置，包含执行命令、调度规则、
    超时设置、重试策略等属性。

    Attributes:
        name: 任务名称，唯一标识符
        command: 要执行的命令
        cron_expr: Cron表达式，定义调度规则
        timezone: 时区名称（默认本地时区）
        timeout: 执行超时时间（秒），0表示不限时
        retries: 失败重试次数
        retry_delay: 重试间隔（秒）
        enabled: 是否启用
        tags: 任务标签列表
        description: 任务描述
    """

    name: str
    command: str
    cron_expr: str
    timezone: str = "local"
    timeout: int = 3600
    retries: int = 0
    retry_delay: int = 5
    enabled: bool = True
    tags: List[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """
        将任务序列化为字典。

        Returns:
            Dict[str, Any]: 任务属性字典
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """
        从字典反序列化创建任务对象。

        Args:
            data: 任务属性字典

        Returns:
            Task: 任务对象
        """
        # 过滤掉不属于Task的字段，避免意外错误
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_fields}

        # 确保 tags 是列表
        if "tags" in filtered and not isinstance(filtered["tags"], list):
            filtered["tags"] = [filtered["tags"]] if filtered["tags"] else []

        return cls(**filtered)

    def validate(self) -> List[str]:
        """
        验证任务配置是否合法。

        Returns:
            List[str]: 错误信息列表，空列表表示验证通过
        """
        errors: List[str] = []

        if not self.name or not self.name.strip():
            errors.append("任务名称不能为空")
        elif not self.name.replace("_", "").replace("-", "").replace(" ", "").isalnum():
            errors.append("任务名称只能包含字母、数字、下划线、连字符和空格")

        if not self.command or not self.command.strip():
            errors.append("执行命令不能为空")

        if not self.cron_expr or not self.cron_expr.strip():
            errors.append("Cron表达式不能为空")

        if self.timeout < 0:
            errors.append("超时时间不能为负数")

        if self.retries < 0:
            errors.append("重试次数不能为负数")

        if self.retry_delay < 0:
            errors.append("重试间隔不能为负数")

        return errors

    def __str__(self) -> str:
        """任务的字符串表示"""
        status = "启用" if self.enabled else "禁用"
        tags_str = f" [{', '.join(self.tags)}]" if self.tags else ""
        return (
            f"Task(name='{self.name}', command='{self.command}', "
            f"cron='{self.cron_expr}', {status}{tags_str})"
        )
