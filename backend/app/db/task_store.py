"""任务存储（阶段 1：内存实现）。

为什么单独封装成一个类？
    阶段 1 用内存字典，后面换成 SQLite 时**只改这一个文件**，
    service 层零改动。这就是 Java 里的"面向接口编程"。

为什么需要 Lock？
    提交请求（主线程）和仿真完成回调（线程池线程）会同时写任务表，
    不加锁可能出现读写撕裂。
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any

# 任务状态流转：PENDING → RUNNING → SUCCEEDED / FAILED
PENDING = "PENDING"
RUNNING = "RUNNING"
SUCCEEDED = "SUCCEEDED"
FAILED = "FAILED"


def now() -> str:
    """统一的 UTC 时间戳（ISO8601）。"""
    return datetime.now(timezone.utc).isoformat()


class TaskStore:
    """任务表。内存版，进程重启后数据丢失（阶段 1 可接受）。"""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._tasks: dict[str, dict[str, Any]] = {}

    def create(self, task_id: str, config: dict) -> None:
        with self._lock:
            self._tasks[task_id] = {
                "task_id": task_id,
                "status": PENDING,
                "progress": 0.0,
                "config": config,
                "kpi": None,
                "error_message": None,
                "created_at": now(),
                "finished_at": None,
            }

    def update(self, task_id: str, **fields: Any) -> None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is not None:
                task.update(fields)

    def get(self, task_id: str) -> dict[str, Any] | None:
        """返回副本，避免调用方修改内部状态。"""
        with self._lock:
            task = self._tasks.get(task_id)
            return dict(task) if task is not None else None
