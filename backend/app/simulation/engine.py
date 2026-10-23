"""露天矿运力仿真内核（阶段 1 最小版）。

场景：1 个装载点（电铲）+ 1 个卸载点 + N 台卡车，跑一个班次，统计 4 个 KPI。

设计约定：
1. 本模块**不依赖 FastAPI**，可以命令行直接跑，也可以被进程池调用。
2. `run_scenario` 必须是**模块级函数**（进程池要求可被 pickle）。
3. 所有随机性来自单一 `random.Random(seed)` 实例，保证同 seed 结果可复现。

命令行自检：
    python -m app.simulation.engine
"""

from __future__ import annotations

import random
import simpy

# 默认参数：与 PRD FR-01「最小场景」一致
DEFAULT_CONFIG: dict = {
    "trucks": 2,               # 卡车数
    "shift_minutes": 60.0,     # 班次时长（仿真分钟）
    "truck_capacity_t": 100.0, # 单车载重（吨）
    "load_min": 4.0,           # 装载耗时
    "dump_min": 2.0,           # 卸载耗时
    "travel_loaded_min": 12.0, # 重车行驶耗时
    "travel_empty_min": 9.0,   # 空车返回耗时
    "seed": 42,                # 随机种子
}

# 耗时扰动幅度：装载/行驶不是固定值，乘一个 [1-x, 1+x] 的系数
_JITTER = 0.15


def _jitter(rng: random.Random, base: float) -> float:
    """给基础耗时加上随机扰动。

    rng 是**全局唯一**的随机实例：所有卡车共用它，
    这样"同 seed → 同随机序列 → 同结果"才成立。
    """
    return base * rng.uniform(1.0 - _JITTER, 1.0 + _JITTER)


def _truck_process(
    env: simpy.Environment,
    shovel: simpy.Resource,
    dump: simpy.Resource,
    cfg: dict,
    rng: random.Random,
    stats: dict,
) -> None:
    """一台卡车的作业循环：等装 → 装载 → 重车行驶 → 等卸 → 卸载 → 空车返回。

    这是一个 SimPy 进程（生成器函数）。关键语法：
    - `yield env.timeout(t)`：把当前进程挂起 t 分钟，**不是**线程 sleep，
      不占 CPU，仿真时钟直接推进。
    - `with shovel.request() as req:`：向电铲这个"资源"申请一个工位。
      容量满时自动排队；`with` 退出时**自动释放**，不写会永久占着电铲。
    """
    while True:
        # 1) 排队等电铲
        arrive = env.now
        with shovel.request() as req:
            yield req
            stats["wait_load"] += env.now - arrive

            # 2) 装载
            t = _jitter(rng, cfg["load_min"])
            yield env.timeout(t)
            stats["busy"] += t

        # 3) 重车行驶到卸载点
        t = _jitter(rng, cfg["travel_loaded_min"])
        yield env.timeout(t)
        stats["busy"] += t

        # 4) 排队等卸载位
        arrive = env.now
        with dump.request() as req:
            yield req
            stats["wait_dump"] += env.now - arrive

            # 5) 卸载
            t = _jitter(rng, cfg["dump_min"])
            yield env.timeout(t)
            stats["busy"] += t

        # 6) 一次完整循环结束，计入产量
        stats["cycles"] += 1
        stats["tonnage"] += cfg["truck_capacity_t"]

        # 7) 空车返回装载点
        t = _jitter(rng, cfg["travel_empty_min"])
        yield env.timeout(t)
        stats["busy"] += t


def run_scenario(cfg: dict) -> dict:
    """跑一次仿真，返回 KPI 字典。

    入参缺失的字段用 DEFAULT_CONFIG 补齐，因此进程池里传部分参数也可以。
    """
    cfg = {**DEFAULT_CONFIG, **(cfg or {})}

    env = simpy.Environment()
    shovel = simpy.Resource(env, capacity=1)  # 电铲：同时只能服务 1 台车
    dump = simpy.Resource(env, capacity=1)    # 卸载点：同时只能服务 1 台车

    rng = random.Random(cfg["seed"])
    stats = {"busy": 0.0, "wait_load": 0.0, "wait_dump": 0.0, "cycles": 0, "tonnage": 0.0}

    for i in range(int(cfg["trucks"])):
        env.process(_truck_process(env, shovel, dump, cfg, rng, stats))

    # 到点即停：正在半路的循环不计入产量
    env.run(until=float(cfg["shift_minutes"]))

    trucks = int(cfg["trucks"])
    shift = float(cfg["shift_minutes"])
    cycles = stats["cycles"]

    # 利用率 = 有效工作时间（行驶+装卸）/ 总可用时间；排队等待不算有效工作
    utilization = stats["busy"] / (trucks * shift) if trucks and shift else 0.0
    # 平均每次循环的等装时间
    avg_wait_load = stats["wait_load"] / cycles if cycles else 0.0

    return {
        "tonnage_t": round(stats["tonnage"], 1),
        "cycles": cycles,
        "truck_utilization": round(utilization, 4),
        "avg_wait_load_min": round(avg_wait_load, 2),
    }


def _print_row(tag: str, kpi: dict) -> None:
    print(
        f"{tag:<8}"
        f"产量 {kpi['tonnage_t']:>8.1f} t | "
        f"循环 {kpi['cycles']:>4d} 次 | "
        f"利用率 {kpi['truck_utilization'] * 100:>6.2f}% | "
        f"等装 {kpi['avg_wait_load_min']:>6.2f} min"
    )


if __name__ == "__main__":
    print("=== 默认场景（2 车 / 60 分钟）===")
    _print_row("2车", run_scenario({}))

    print("\n=== 车数扫描（观察排队论趋势）===")
    for n in (2, 4, 6, 8):
        _print_row(f"{n}车", run_scenario({"trucks": n}))

    print("\n=== 可复现性（同 seed 跑两次）===")
    a = run_scenario({"trucks": 4})
    b = run_scenario({"trucks": 4})
    print(f"第一次: {a}\n第二次: {b}\n一致: {a == b}")
