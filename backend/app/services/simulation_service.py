"""仿真业务层：负责"提交任务 → 异步执行 → 回写结果"。

全项目最关键的一段逻辑在这里，两个必须记住的点：

1. 为什么用进程池而不是线程池？
   仿真是纯 CPU 计算，Python 有 GIL，线程池等于串行，会把服务卡死。

2. 为什么结果要在回调里写回？
   子进程有**独立的内存**，在 worker 里改 TaskStore 主进程根本看不到。
   必须用 `future.add_done_callback(...)` —— 回调运行在**主进程**，
   才能把结果写进任务表。
"""

from __future__ import annotations

import threading
import uuid
from concurrent.futures import Future, ProcessPoolExecutor

from app.db.task_store import FAILED, RUNNING, SUCCEEDED, TaskStore, now
from app.simulation.engine import run_scenario

# 全局唯一的进程池与任务表（阶段 1 单实例部署，够用；多实例时要换成外部队列）
#
# 注意：进程池必须**惰性创建**。如果在模块导入时就创建，
# Windows 的 spawn 子进程会重新 import 本模块，从而试图在子进程里再建一个进程池，
# 触发 "daemonic processes are not allowed to have children"。
_executor: ProcessPoolExecutor | None = None
_executor_lock = threading.Lock()
_store = TaskStore()


def _get_executor() -> ProcessPoolExecutor:
    global _executor
    if _executor is None:
        with _executor_lock:
            if _executor is None:  # 双检锁，避免并发时创建多个池
                _executor = ProcessPoolExecutor(max_workers=2)
    return _executor


def _on_finished(task_id: str, future: Future) -> None:
    """仿真结束后的回写逻辑。运行在主进程的线程池线程里。"""
    try:
        kpi = future.result()  # 若子进程抛异常，这里会重新抛出
    except Exception as exc:  # noqa: BLE001 - 阶段 1 先笼统兜住，后续细分错误码
        _store.update(
            task_id,
            status=FAILED,
            error_message=f"{type(exc).__name__}: {exc}",
            finished_at=now(),
        )
        return

    _store.update(
        task_id,
        status=SUCCEEDED,
        progress=1.0,
        kpi=kpi,
        finished_at=now(),
    )


def submit(config: dict) -> str:
    """提交一次仿真，立即返回 task_id（不等待计算完成）。"""
    task_id = uuid.uuid4().hex[:16]
    _store.create(task_id, config)
    _store.update(task_id, status=RUNNING)

    future = _get_executor().submit(run_scenario, config)
    future.add_done_callback(lambda f, tid=task_id: _on_finished(tid, f))
    return task_id


def get_task(task_id: str) -> dict | None:
    return _store.get(task_id)


# 暴露给测试/后续 SQLite 实现注入用
def get_store() -> TaskStore:
    return _store
