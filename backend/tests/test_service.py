"""服务层测试：重点验证"异步提交 + 回调回写"这条链路真的成立。

这是整个阶段 1 最容易出错的地方：子进程算完，结果必须回到主进程的任务表里。
"""

import time

from app.db.task_store import SUCCEEDED
from app.services import simulation_service


def _wait_done(task_id: str, timeout_sec: float = 20.0) -> dict:
    """轮询等待任务结束（和前端做的事一样）。"""
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        task = simulation_service.get_task(task_id)
        assert task is not None
        if task["status"] in (SUCCEEDED, "FAILED"):
            return task
        time.sleep(0.1)
    raise AssertionError("任务超时未结束")


def test_submit_returns_task_id_immediately():
    """提交必须立刻返回，不能等仿真跑完。"""
    task_id = simulation_service.submit({"trucks": 4, "shift_minutes": 120.0})
    assert task_id
    assert simulation_service.get_task(task_id) is not None


def test_result_is_written_back_to_store():
    """子进程算出的 KPI，必须能被主进程查到（回调回写生效）。"""
    task_id = simulation_service.submit({"trucks": 4, "shift_minutes": 120.0, "seed": 42})
    task = _wait_done(task_id)

    assert task["status"] == SUCCEEDED
    assert task["kpi"] is not None
    assert task["kpi"]["tonnage_t"] > 0
    assert task["progress"] == 1.0


def test_unknown_task_returns_none():
    assert simulation_service.get_task("not-exist") is None
