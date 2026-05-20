"""
CronForge - Webhook通知模块

支持通过HTTP POST发送Webhook通知，
可配置通知URL、事件类型和消息模板。
"""

import json
import urllib.request
import urllib.error
import ssl
from typing import Optional, Dict, Any
from datetime import datetime


class NotifyError(Exception):
    """通知发送错误"""
    pass


class WebhookNotifier:
    """
    Webhook通知发送器。

    通过HTTP POST请求发送任务执行结果通知。

    Attributes:
        url: Webhook URL
        events: 触发通知的事件列表
        timeout: 请求超时时间（秒）
    """

    def __init__(
        self,
        url: str,
        events: Optional[list] = None,
        timeout: int = 10,
    ):
        """
        初始化Webhook通知器。

        Args:
            url: Webhook URL
            events: 触发通知的事件列表，如 ["on_success", "on_failure"]
            timeout: 请求超时时间（秒）
        """
        self.url = url
        self.events = events or ["on_failure"]
        self.timeout = timeout

    def should_notify(self, event: str) -> bool:
        """
        判断是否应该发送通知。

        Args:
            event: 事件类型 ("on_success" 或 "on_failure")

        Returns:
            bool: 是否应该发送通知
        """
        return event in self.events

    def notify(
        self,
        task_name: str,
        event: str,
        result: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        发送Webhook通知。

        Args:
            task_name: 任务名称
            event: 事件类型
            result: 执行结果字典

        Returns:
            bool: 是否发送成功
        """
        if not self.should_notify(event):
            return True

        payload = self._build_payload(task_name, event, result)

        try:
            return self._send(payload)
        except Exception as e:
            raise NotifyError(f"发送Webhook通知失败: {e}")

    def _build_payload(
        self,
        task_name: str,
        event: str,
        result: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        构建通知负载。

        Args:
            task_name: 任务名称
            event: 事件类型
            result: 执行结果

        Returns:
            Dict[str, Any]: 通知负载
        """
        payload = {
            "source": "cronforge",
            "event": event,
            "task_name": task_name,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        if result:
            payload["data"] = {
                "command": result.get("command", ""),
                "exit_code": result.get("exit_code"),
                "duration": result.get("duration", 0),
                "timed_out": result.get("timed_out", False),
                "retries": result.get("retries", 0),
                "success": result.get("success", False),
                "stdout": (result.get("stdout", "") or "")[:500],
                "stderr": (result.get("stderr", "") or "")[:500],
            }

        return payload

    def _send(self, payload: Dict[str, Any]) -> bool:
        """
        发送HTTP POST请求。

        Args:
            payload: 请求负载

        Returns:
            bool: 是否发送成功
        """
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        req = urllib.request.Request(
            self.url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "CronForge/1.0",
            },
            method="POST",
        )

        try:
            # 创建不验证SSL证书的上下文（兼容自签名证书）
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            with urllib.request.urlopen(req, timeout=self.timeout, context=ctx) as resp:
                return 200 <= resp.status < 300
        except urllib.error.URLError as e:
            raise NotifyError(f"HTTP请求失败: {e}")
        except Exception as e:
            raise NotifyError(f"发送通知时发生错误: {e}")


def create_notifier(config: Optional[Dict[str, Any]] = None) -> Optional[WebhookNotifier]:
    """
    根据配置创建通知器实例。

    Args:
        config: 配置字典，包含 notify_url 和 notify_events

    Returns:
        Optional[WebhookNotifier]: 通知器实例，未配置返回 None
    """
    if not config:
        return None

    url = config.get("notify_url")
    if not url:
        return None

    events = config.get("notify_events", ["on_failure"])
    if isinstance(events, str):
        events = [events]

    return WebhookNotifier(url=url, events=events)
