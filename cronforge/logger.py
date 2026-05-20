"""
CronForge - 日志管理模块

使用SQLite数据库记录任务执行日志，
支持日志查询、统计和清理功能。
"""

import os
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional


class TaskLogger:
    """
    任务日志管理器。

    使用SQLite数据库存储任务执行日志，提供
    日志记录、查询、统计和清理功能。

    Attributes:
        db_path: SQLite数据库文件路径
    """

    def __init__(self, db_path: str):
        """
        初始化日志管理器。

        Args:
            db_path: SQLite数据库文件路径
        """
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """初始化数据库，创建日志表"""
        # 确保目录存在
        dir_path = os.path.dirname(self.db_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_name TEXT NOT NULL,
                    command TEXT NOT NULL,
                    exit_code INTEGER,
                    stdout TEXT,
                    stderr TEXT,
                    duration REAL,
                    timed_out INTEGER DEFAULT 0,
                    retries INTEGER DEFAULT 0,
                    success INTEGER DEFAULT 0,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    created_at TEXT DEFAULT (datetime('now', 'localtime'))
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_task_logs_name
                ON task_logs(task_name)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_task_logs_created
                ON task_logs(created_at)
            """)
            conn.commit()
        finally:
            conn.close()

    def log_execution(
        self,
        task_name: str,
        command: str,
        exit_code: Optional[int],
        stdout: str,
        stderr: str,
        duration: float,
        timed_out: bool,
        retries: int,
        success: bool,
        started_at: Optional[str] = None,
        finished_at: Optional[str] = None,
    ) -> int:
        """
        记录一次任务执行日志。

        Args:
            task_name: 任务名称
            command: 执行的命令
            exit_code: 退出码
            stdout: 标准输出
            stderr: 标准错误
            duration: 执行时长（秒）
            timed_out: 是否超时
            retries: 重试次数
            success: 是否成功
            started_at: 开始时间
            finished_at: 结束时间

        Returns:
            int: 日志记录ID
        """
        if started_at is None:
            started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if finished_at is None:
            finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute("""
                INSERT INTO task_logs
                (task_name, command, exit_code, stdout, stderr, duration,
                 timed_out, retries, success, started_at, finished_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task_name, command, exit_code,
                stdout[:10000] if stdout else "",  # 限制存储长度
                stderr[:10000] if stderr else "",
                duration,
                1 if timed_out else 0,
                retries,
                1 if success else 0,
                started_at,
                finished_at,
            ))
            conn.commit()
            return cursor.lastrowid or 0
        finally:
            conn.close()

    def query_logs(
        self,
        task_name: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        success_only: bool = False,
        failure_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        查询执行日志。

        Args:
            task_name: 按任务名称过滤，None表示所有任务
            limit: 返回记录数限制
            offset: 偏移量
            success_only: 仅查询成功记录
            failure_only: 仅查询失败记录

        Returns:
            List[Dict[str, Any]]: 日志记录列表
        """
        conditions = []
        params: list = []

        if task_name:
            conditions.append("task_name = ?")
            params.append(task_name)
        if success_only:
            conditions.append("success = 1")
        if failure_only:
            conditions.append("success = 0")

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        query = f"""
            SELECT id, task_name, command, exit_code, stdout, stderr,
                   duration, timed_out, retries, success, started_at, finished_at
            FROM task_logs
            {where_clause}
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])

        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def get_statistics(self, task_name: Optional[str] = None) -> Dict[str, Any]:
        """
        获取执行统计信息。

        Args:
            task_name: 按任务名称过滤，None表示全局统计

        Returns:
            Dict[str, Any]: 统计信息字典
        """
        where_clause = ""
        params: list = []
        if task_name:
            where_clause = "WHERE task_name = ?"
            params.append(task_name)

        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row

            # 总体统计
            cursor = conn.execute(f"""
                SELECT
                    COUNT(*) as total_runs,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count,
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failure_count,
                    AVG(duration) as avg_duration,
                    MAX(duration) as max_duration,
                    MIN(duration) as min_duration
                FROM task_logs
                {where_clause}
            """, params)
            stats = dict(cursor.fetchone())

            # 最近一次执行
            cursor = conn.execute(f"""
                SELECT started_at, success
                FROM task_logs
                {where_clause}
                ORDER BY id DESC LIMIT 1
            """, params)
            last_run = cursor.fetchone()

            stats["last_run"] = dict(last_run) if last_run else None

            # 成功率
            total = stats.get("total_runs", 0) or 0
            success = stats.get("success_count", 0) or 0
            stats["success_rate"] = (success / total * 100) if total > 0 else 0

            return stats
        finally:
            conn.close()

    def cleanup(self, days: int = 0, max_records: int = 0) -> int:
        """
        清理日志记录。

        Args:
            days: 保留最近N天的记录，0表示不按时间清理
            max_records: 保留最近N条记录，0表示不按数量清理

        Returns:
            int: 删除的记录数
        """
        conn = sqlite3.connect(self.db_path)
        deleted = 0
        try:
            if days > 0:
                cursor = conn.execute("""
                    DELETE FROM task_logs
                    WHERE created_at < datetime('now', ? || ' days', 'localtime')
                """, (str(-days),))
                deleted += cursor.rowcount

            if max_records > 0:
                cursor = conn.execute("""
                    DELETE FROM task_logs
                    WHERE id NOT IN (
                        SELECT id FROM task_logs
                        ORDER BY id DESC LIMIT ?
                    )
                """, (max_records,))
                deleted += cursor.rowcount

            conn.commit()
            return deleted
        finally:
            conn.close()

    def get_task_names(self) -> List[str]:
        """
        获取所有有日志记录的任务名称。

        Returns:
            List[str]: 任务名称列表
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute(
                "SELECT DISTINCT task_name FROM task_logs ORDER BY task_name"
            )
            return [row[0] for row in cursor.fetchall()]
        finally:
            conn.close()
