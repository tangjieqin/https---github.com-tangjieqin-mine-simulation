"""仿真内核测试（阶段 1）。

跑法（在 backend/ 目录）：
    pytest
"""

from app.simulation.engine import run_scenario


def test_same_seed_is_reproducible():
    """同配置同 seed，两次结果必须完全一致。

    这是仿真的底线：结果要支撑决策，跑两次不一样就没有公信力。
    """
    cfg = {"trucks": 4, "shift_minutes": 120.0, "seed": 42}
    assert run_scenario(cfg) == run_scenario(cfg)


def test_different_seed_changes_result():
    """不同 seed 应该得到不同结果，反向证明随机性确实生效。"""
    a = run_scenario({"trucks": 4, "shift_minutes": 120.0, "seed": 1})
    b = run_scenario({"trucks": 4, "shift_minutes": 120.0, "seed": 999})
    assert a != b


def test_more_trucks_yield_more_tonnage():
    """车越多产量越高（边际递减，但方向必须是上升的）。"""
    few = run_scenario({"trucks": 2, "shift_minutes": 240.0})
    many = run_scenario({"trucks": 6, "shift_minutes": 240.0})
    assert many["tonnage_t"] > few["tonnage_t"]


def test_wait_time_grows_with_trucks():
    """电铲只有 1 台，车越多排队越久 —— 排队论的基本规律。"""
    few = run_scenario({"trucks": 1, "shift_minutes": 240.0})
    many = run_scenario({"trucks": 8, "shift_minutes": 240.0})
    assert many["avg_wait_load_min"] > few["avg_wait_load_min"]


def test_utilization_is_ratio():
    """利用率是 0~1 的小数，不能越界。"""
    kpi = run_scenario({"trucks": 4, "shift_minutes": 120.0})
    assert 0.0 <= kpi["truck_utilization"] <= 1.0
