"""
CronForge - YAML配置管理模块

负责YAML格式配置文件的加载、解析和保存。
支持多路径配置文件搜索、自动模板生成。
注意：由于零依赖要求，使用自定义的简易YAML解析器。
"""

import os
import re
from typing import Any, Dict, List, Optional, Tuple

from cronforge.task import Task


# 默认配置文件搜索路径
CONFIG_SEARCH_PATHS = [
    "./cronforge.yaml",
    "./cronforge.yml",
    os.path.expanduser("~/.cronforge/config.yaml"),
    os.path.expanduser("~/.cronforge/config.yml"),
]

# 配置文件模板
CONFIG_TEMPLATE = """# CronForge 配置文件
# 详细文档: https://github.com/cronforge/cronforge

# 全局配置
global:
  # 日志数据库路径
  log_db: ~/.cronforge/logs.db
  # 默认时区
  timezone: local
  # 默认超时时间（秒）
  default_timeout: 3600
  # 默认重试次数
  default_retries: 0
  # Webhook通知URL（可选）
  # notify_url: "http://example.com/webhook"
  # 通知事件（on_success, on_failure）
  # notify_events:
  #   - on_failure

# 任务列表
tasks:
  # 示例任务：每天早上9点执行
  - name: daily-report
    command: echo "生成日报表"
    cron_expr: "0 9 * * *"
    timezone: local
    timeout: 300
    retries: 2
    retry_delay: 10
    enabled: true
    tags:
      - report
    description: "每日报告生成任务"

  # 示例任务：每小时执行
  - name: health-check
    command: echo "健康检查完成"
    cron_expr: "@hourly"
    enabled: true
    tags:
      - monitor
    description: "系统健康检查"

  # 示例任务：每5分钟执行
  # - name: sync-data
  #   command: python sync.py
  #   cron_expr: "*/5 * * * *"
  #   enabled: false
  #   tags:
  #     - sync
  #   description: "数据同步任务"
"""


class SimpleYAMLParser:
    """
    简易YAML解析器。

    仅支持CronForge配置所需的YAML子集：
    - 键值对（字符串、数字、布尔值）
    - 列表
    - 嵌套字典
    - 注释
    """

    def parse(self, text: str) -> Dict[str, Any]:
        """
        解析YAML文本为字典。

        Args:
            text: YAML格式文本

        Returns:
            Dict[str, Any]: 解析结果
        """
        lines = text.split("\n")
        # 预处理：移除注释和空行，保留结构
        cleaned = []
        for line in lines:
            stripped = line.rstrip()
            # 跳过空行
            if not stripped.strip():
                continue
            # 移除行内注释（但保留引号内的#号）
            stripped = self._remove_comment(stripped)
            if stripped.strip():
                cleaned.append(stripped)

        result: Dict[str, Any] = {}
        self._parse_block(cleaned, 0, result)
        return result

    def _remove_comment(self, line: str) -> str:
        """移除行内注释"""
        in_quote = False
        quote_char = None
        for i, ch in enumerate(line):
            if ch in ('"', "'") and (i == 0 or line[i - 1] != '\\'):
                if not in_quote:
                    in_quote = True
                    quote_char = ch
                elif ch == quote_char:
                    in_quote = False
                    quote_char = None
            elif ch == '#' and not in_quote:
                return line[:i].rstrip()
        return line

    def _get_indent(self, line: str) -> int:
        """获取行缩进级别"""
        return len(line) - len(line.lstrip())

    def _parse_value(self, value_str: str) -> Any:
        """解析YAML值"""
        value_str = value_str.strip()

        if not value_str or value_str == "~" or value_str.lower() == "null":
            return None

        # 布尔值
        if value_str.lower() in ("true", "yes", "on"):
            return True
        if value_str.lower() in ("false", "no", "off"):
            return False

        # 数字
        try:
            if "." in value_str:
                return float(value_str)
            return int(value_str)
        except ValueError:
            pass

        # 去除引号
        if (value_str.startswith('"') and value_str.endswith('"')) or \
           (value_str.startswith("'") and value_str.endswith("'")):
            return value_str[1:-1]

        return value_str

    def _parse_block(self, lines: List[str], start_idx: int, result: Any) -> int:
        """
        递归解析YAML块。

        Args:
            lines: 所有行
            start_idx: 开始索引
            result: 结果容器

        Returns:
            int: 下一个要处理的行索引
        """
        i = start_idx
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # 列表项
            if stripped.startswith("- "):
                if isinstance(result, list):
                    item_content = stripped[2:].strip()

                    # 检查是否是 key: value 或 key: 格式（字典项）
                    if ":" in item_content:
                        colon_idx = item_content.index(":")
                        key = item_content[:colon_idx].strip()
                        value_part = item_content[colon_idx + 1:].strip()
                        key = str(self._parse_value(key)) if key else key

                        item_dict: Dict[str, Any] = {}

                        if not value_part:
                            # key: 后面为空，子行在下方
                            item_dict[key] = None
                            i += 1
                            base_indent = self._get_indent(line)
                            sub_lines = []
                            while i < len(lines):
                                next_line = lines[i]
                                if not next_line.strip():
                                    i += 1
                                    continue
                                if self._get_indent(next_line) <= base_indent:
                                    break
                                sub_lines.append(next_line)
                                i += 1
                            if sub_lines:
                                self._parse_block(sub_lines, 0, item_dict)
                        else:
                            # key: value 在同一行
                            item_dict[key] = self._parse_value(value_part)
                            i += 1

                        # 继续收集同级的键值对
                        base_indent = self._get_indent(line)
                        while i < len(lines):
                            next_line = lines[i]
                            if not next_line.strip():
                                i += 1
                                continue
                            next_indent = self._get_indent(next_line)
                            if next_indent <= base_indent:
                                break
                            next_stripped = next_line.strip()
                            if ":" in next_stripped and not next_stripped.startswith("- "):
                                nc = next_stripped.index(":")
                                nk = next_stripped[:nc].strip()
                                nv = next_stripped[nc + 1:].strip()
                                nk = str(self._parse_value(nk)) if nk else nk
                                if not nv:
                                    # 子字典或子列表
                                    i += 1
                                    sub_base = next_indent
                                    sub_lines2 = []
                                    while i < len(lines):
                                        sl = lines[i]
                                        if not sl.strip():
                                            i += 1
                                            continue
                                        if self._get_indent(sl) <= sub_base:
                                            break
                                        sub_lines2.append(sl)
                                        i += 1
                                    if sub_lines2:
                                        first_sub = sub_lines2[0].strip()
                                        if first_sub.startswith("- "):
                                            sub_list: list = []
                                            self._parse_block(sub_lines2, 0, sub_list)
                                            item_dict[nk] = sub_list
                                        else:
                                            sub_dict: Dict[str, Any] = {}
                                            self._parse_block(sub_lines2, 0, sub_dict)
                                            item_dict[nk] = sub_dict
                                    else:
                                        item_dict[nk] = None
                                else:
                                    item_dict[nk] = self._parse_value(nv)
                                    i += 1
                            else:
                                break

                        result.append(item_dict)
                    else:
                        result.append(self._parse_value(item_content))
                        i += 1
                else:
                    i += 1
                continue

            # 键值对
            if ":" in stripped:
                colon_idx = stripped.index(":")
                key = stripped[:colon_idx].strip()
                value_part = stripped[colon_idx + 1:].strip()

                # 去除key的引号
                key = str(self._parse_value(key)) if key else key

                if not value_part:
                    # 值为空，检查下一行
                    i += 1
                    base_indent = self._get_indent(line)
                    sub_lines = []
                    while i < len(lines):
                        next_line = lines[i]
                        if not next_line.strip():
                            i += 1
                            continue
                        if self._get_indent(next_line) <= base_indent:
                            break
                        sub_lines.append(next_line)
                        i += 1

                    if sub_lines:
                        # 检查子行是列表还是字典
                        first_sub = sub_lines[0].strip()
                        if first_sub.startswith("- "):
                            sub_result: list = []
                            self._parse_block(sub_lines, 0, sub_result)
                            if isinstance(result, dict):
                                result[key] = sub_result
                        else:
                            sub_dict: Dict[str, Any] = {}
                            self._parse_block(sub_lines, 0, sub_dict)
                            if isinstance(result, dict):
                                result[key] = sub_dict
                    else:
                        if isinstance(result, dict):
                            result[key] = None
                else:
                    if isinstance(result, dict):
                        result[key] = self._parse_value(value_part)
                    i += 1
                continue

            i += 1

        return i

    def dump(self, data: Dict[str, Any], indent: int = 0) -> str:
        """
        将字典序列化为YAML文本。

        Args:
            data: 要序列化的数据
            indent: 缩进级别

        Returns:
            str: YAML格式文本
        """
        lines = []
        prefix = "  " * indent

        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    lines.append(f"{prefix}{key}:")
                    lines.append(self.dump(value, indent + 1))
                elif isinstance(value, list):
                    lines.append(f"{prefix}{key}:")
                    for item in value:
                        if isinstance(item, dict):
                            first = True
                            for k, v in item.items():
                                if first:
                                    if isinstance(v, dict):
                                        lines.append(f"{prefix}  - {k}:")
                                        lines.append(self.dump(v, indent + 2))
                                    elif isinstance(v, list):
                                        lines.append(f"{prefix}  - {k}:")
                                        for li in v:
                                            lines.append(f"{prefix}      - {self._format_value(li)}")
                                    else:
                                        lines.append(f"{prefix}  - {k}: {self._format_value(v)}")
                                    first = False
                                else:
                                    if isinstance(v, dict):
                                        lines.append(f"{prefix}    {k}:")
                                        lines.append(self.dump(v, indent + 2))
                                    elif isinstance(v, list):
                                        lines.append(f"{prefix}    {k}:")
                                        for li in v:
                                            lines.append(f"{prefix}      - {self._format_value(li)}")
                                    else:
                                        lines.append(f"{prefix}    {k}: {self._format_value(v)}")
                        else:
                            lines.append(f"{prefix}  - {self._format_value(item)}")
                else:
                    lines.append(f"{prefix}{key}: {self._format_value(value)}")
        return "\n".join(lines)

    def _format_value(self, value: Any) -> str:
        """格式化值为YAML字符串"""
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, str):
            # 如果字符串包含特殊字符，加引号
            if any(c in value for c in (":", "#", "{", "}", "[", "]", ",", "&", "*", "?", "|", "-", "<", ">", "=", "!", "%", "@", "`")):
                return f'"{value}"'
            if value.lower() in ("true", "false", "null", "yes", "no"):
                return f'"{value}"'
            return value
        return str(value)


class Config:
    """
    配置管理类。

    负责加载、解析和管理CronForge配置。

    Attributes:
        global_config: 全局配置字典
        tasks: 任务列表
        config_path: 配置文件路径
    """

    def __init__(self):
        """初始化配置管理器"""
        self.global_config: Dict[str, Any] = {
            "log_db": os.path.expanduser("~/.cronforge/logs.db"),
            "timezone": "local",
            "default_timeout": 3600,
            "default_retries": 0,
        }
        self.tasks: List[Task] = []
        self.config_path: Optional[str] = None
        self._parser = SimpleYAMLParser()

    def load(self, config_path: Optional[str] = None) -> None:
        """
        加载配置文件。

        Args:
            config_path: 指定配置文件路径，如果为 None 则自动搜索

        Raises:
            FileNotFoundError: 配置文件不存在
        """
        if config_path:
            path = config_path
        else:
            path = self._find_config()

        if path is None:
            raise FileNotFoundError(
                "未找到配置文件。请运行 'cronforge init' 创建配置文件，"
                "或使用 -c/--config 指定配置文件路径。"
            )

        self.config_path = path

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        data = self._parser.parse(content)
        self._apply_config(data)

    def _find_config(self) -> Optional[str]:
        """
        在搜索路径中查找配置文件。

        Returns:
            Optional[str]: 找到的配置文件路径，未找到返回 None
        """
        for path in CONFIG_SEARCH_PATHS:
            expanded = os.path.expanduser(path)
            if os.path.isfile(expanded):
                return expanded
        return None

    def _apply_config(self, data: Dict[str, Any]) -> None:
        """
        应用解析后的配置数据。

        Args:
            data: 解析后的配置字典
        """
        # 应用全局配置
        if "global" in data and isinstance(data["global"], dict):
            self.global_config.update(data["global"])

        # 扩展路径中的 ~
        if "log_db" in self.global_config:
            self.global_config["log_db"] = os.path.expanduser(
                str(self.global_config["log_db"])
            )

        # 加载任务
        if "tasks" in data and isinstance(data["tasks"], list):
            self.tasks = []
            for task_data in data["tasks"]:
                if isinstance(task_data, dict):
                    # 合并全局默认值
                    if "timeout" not in task_data and "default_timeout" in self.global_config:
                        task_data["timeout"] = self.global_config["default_timeout"]
                    if "retries" not in task_data and "default_retries" in self.global_config:
                        task_data["retries"] = self.global_config["default_retries"]
                    if "timezone" not in task_data and "timezone" in self.global_config:
                        task_data["timezone"] = self.global_config["timezone"]

                    task = Task.from_dict(task_data)
                    self.tasks.append(task)

    def save(self, path: Optional[str] = None) -> None:
        """
        保存配置到文件。

        Args:
            path: 保存路径，如果为 None 则使用当前配置路径
        """
        save_path = path or self.config_path
        if save_path is None:
            save_path = "./cronforge.yaml"

        # 确保目录存在
        dir_path = os.path.dirname(save_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

        # 构建配置数据
        data = {
            "global": self.global_config,
            "tasks": [task.to_dict() for task in self.tasks],
        }

        yaml_text = self._parser.dump(data)
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(yaml_text)

        self.config_path = save_path

    def create_template(self, path: Optional[str] = None) -> str:
        """
        创建配置文件模板。

        Args:
            path: 文件路径，如果为 None 则使用 ./cronforge.yaml

        Returns:
            str: 创建的文件路径
        """
        save_path = path or "./cronforge.yaml"

        # 确保目录存在
        dir_path = os.path.dirname(save_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

        with open(save_path, "w", encoding="utf-8") as f:
            f.write(CONFIG_TEMPLATE)

        return save_path

    def get_task(self, name: str) -> Optional[Task]:
        """
        根据名称获取任务。

        Args:
            name: 任务名称

        Returns:
            Optional[Task]: 任务对象，未找到返回 None
        """
        for task in self.tasks:
            if task.name == name:
                return task
        return None

    def add_task(self, task: Task) -> None:
        """
        添加任务。

        Args:
            task: 任务对象
        """
        self.tasks.append(task)

    def remove_task(self, name: str) -> bool:
        """
        移除任务。

        Args:
            name: 任务名称

        Returns:
            bool: 是否成功移除
        """
        for i, task in enumerate(self.tasks):
            if task.name == name:
                self.tasks.pop(i)
                return True
        return False

    def get_log_db_path(self) -> str:
        """
        获取日志数据库路径。

        Returns:
            str: 日志数据库文件路径
        """
        return self.global_config.get(
            "log_db",
            os.path.expanduser("~/.cronforge/logs.db"),
        )

    def get_notify_url(self) -> Optional[str]:
        """
        获取通知URL。

        Returns:
            Optional[str]: 通知URL，未配置返回 None
        """
        return self.global_config.get("notify_url")

    def get_notify_events(self) -> List[str]:
        """
        获取通知事件列表。

        Returns:
            List[str]: 通知事件列表
        """
        events = self.global_config.get("notify_events", [])
        if not isinstance(events, list):
            events = [events]
        return events
