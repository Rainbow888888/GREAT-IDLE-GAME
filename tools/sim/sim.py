"""Детерминированный симулятор баланса одного забега.

Публичный API:
- load_config(path) -> Config
- load_plan(path) -> Plan
- simulate(config, plan) -> SimulationResult
- ConfigError
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field, replace
from typing import Any

EPS = 1e-9


class ConfigError(Exception):
    """Ошибка во входных данных конфигурации или плана."""


@dataclass(frozen=True)
class Milestone:
    count: int
    total_multiplier: float


@dataclass(frozen=True)
class ManualActionConfig:
    yield_: float
    cooldown_seconds: float
    stops_after_purchase_id: str | None


@dataclass(frozen=True)
class WorkerConfig:
    id: str
    base_cost: float
    cost_growth: float
    base_rate: float
    milestones: tuple[Milestone, ...]


@dataclass(frozen=True)
class BuildingConfig:
    id: str
    base_cost: float
    cost_growth: float
    base_output: float
    output_growth: float
    max_level: int


@dataclass(frozen=True)
class FixedPurchaseConfig:
    id: str
    cost: float
    category: str
    ends_run: bool


@dataclass(frozen=True)
class Config:
    tick_seconds: float
    max_seconds: float
    manual_action: ManualActionConfig
    worker: WorkerConfig
    buildings: dict[str, BuildingConfig]
    fixed_purchases: dict[str, FixedPurchaseConfig]
    prestige_multiplier: float = 1.0


@dataclass(frozen=True)
class WorkerStep:
    target_count: int
    category: str


@dataclass(frozen=True)
class BuildingStep:
    building_id: str
    target_level: int
    category: str


@dataclass(frozen=True)
class FixedStep:
    purchase_id: str


@dataclass(frozen=True)
class Plan:
    steps: tuple[WorkerStep | BuildingStep | FixedStep, ...]


@dataclass(frozen=True)
class PurchaseEvent:
    time_seconds: float
    kind: str
    item_id: str
    level: int | None
    count: int | None
    cost: float
    category: str


@dataclass
class State:
    money: float = 0.0
    worker_count: int = 0
    building_levels: dict[str, int] = field(default_factory=dict)
    fixed_purchases: set[str] = field(default_factory=set)

    def copy(self) -> State:
        return State(
            money=self.money,
            worker_count=self.worker_count,
            building_levels=dict(self.building_levels),
            fixed_purchases=set(self.fixed_purchases),
        )


@dataclass
class SimulationResult:
    completed: bool
    elapsed_seconds: float
    events: list[PurchaseEvent]
    state: State
    max_meaningful_gap_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "completed": self.completed,
            "elapsed_seconds": self.elapsed_seconds,
            "events": [
                {
                    "time_seconds": e.time_seconds,
                    "kind": e.kind,
                    "item_id": e.item_id,
                    "level": e.level,
                    "count": e.count,
                    "cost": e.cost,
                    "category": e.category,
                }
                for e in self.events
            ],
            "state": {
                "money": self.state.money,
                "worker_count": self.state.worker_count,
                "building_levels": self.state.building_levels,
                "fixed_purchases": sorted(self.state.fixed_purchases),
            },
            "max_meaningful_gap_seconds": self.max_meaningful_gap_seconds,
        }


def _check_keys(name: str, data: dict[str, Any], required: set[str], optional: set[str] | None = None) -> None:
    optional = optional or set()
    unknown = set(data.keys()) - required - optional
    if unknown:
        raise ConfigError(f"{name}: неизвестные поля: {sorted(unknown)}")
    missing = required - set(data.keys())
    if missing:
        raise ConfigError(f"{name}: отсутствуют обязательные поля: {sorted(missing)}")


def _positive_number(name: str, value: Any, *, allow_zero: bool = False) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ConfigError(f"{name} должен быть числом")
    limit = 0 if allow_zero else 0
    if (not allow_zero and value <= limit) or (allow_zero and value < limit):
        raise ConfigError(f"{name} должен быть {'неотрицательным' if allow_zero else 'положительным'}")
    return float(value)


def _positive_int(name: str, value: Any) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ConfigError(f"{name} должен быть целым числом")
    if value <= 0:
        raise ConfigError(f"{name} должен быть положительным")
    return value


def load_config(path: str) -> Config:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError as exc:
        raise ConfigError(f"конфиг не найден: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(f"ошибка JSON в конфиге: {exc}") from exc

    if not isinstance(data, dict):
        raise ConfigError("конфиг должен быть объектом")

    _check_keys(
        "config",
        data,
        required={"schemaVersion", "tickSeconds", "maxSeconds", "manualAction", "worker", "buildings", "fixedPurchases"},
        optional={"prestigeMultiplier"},
    )

    schema_version = data.get("schemaVersion")
    if schema_version != 1:
        raise ConfigError(f"schemaVersion должен быть 1, получен {schema_version}")

    tick_seconds = _positive_number("tickSeconds", data["tickSeconds"])
    max_seconds = _positive_number("maxSeconds", data["maxSeconds"])

    manual = data["manualAction"]
    if not isinstance(manual, dict):
        raise ConfigError("manualAction должен быть объектом")
    _check_keys("manualAction", manual, required={"yield", "cooldownSeconds", "stopsAfterPurchaseId"})
    manual_yield = _positive_number("manualAction.yield", manual["yield"])
    manual_cooldown = _positive_number("manualAction.cooldownSeconds", manual["cooldownSeconds"])
    stops_after = manual["stopsAfterPurchaseId"]
    if stops_after is not None and not isinstance(stops_after, str):
        raise ConfigError("manualAction.stopsAfterPurchaseId должен быть строкой или null")

    if manual_cooldown % tick_seconds > EPS and abs((manual_cooldown / tick_seconds) - round(manual_cooldown / tick_seconds)) > EPS:
        raise ConfigError("manualAction.cooldownSeconds должен делиться на tickSeconds без остатка")

    worker = data["worker"]
    if not isinstance(worker, dict):
        raise ConfigError("worker должен быть объектом")
    _check_keys("worker", worker, required={"id", "baseCost", "costGrowth", "baseRate", "milestones"})
    worker_id = worker["id"]
    if not isinstance(worker_id, str) or not worker_id:
        raise ConfigError("worker.id должен быть непустой строкой")
    worker_base_cost = _positive_number("worker.baseCost", worker["baseCost"])
    worker_cost_growth = _positive_number("worker.costGrowth", worker["costGrowth"])
    worker_base_rate = _positive_number("worker.baseRate", worker["baseRate"])

    raw_milestones = worker["milestones"]
    if not isinstance(raw_milestones, list):
        raise ConfigError("worker.milestones должен быть массивом")
    milestone_objs: list[Milestone] = []
    seen_counts: set[int] = set()
    for i, item in enumerate(raw_milestones):
        if not isinstance(item, dict):
            raise ConfigError(f"worker.milestones[{i}] должен быть объектом")
        _check_keys(f"worker.milestones[{i}]", item, required={"count", "totalMultiplier"})
        count = _positive_int(f"worker.milestones[{i}].count", item["count"])
        mult = _positive_number(f"worker.milestones[{i}].totalMultiplier", item["totalMultiplier"])
        if count in seen_counts:
            raise ConfigError(f"worker.milestones: повторяющееся значение count {count}")
        seen_counts.add(count)
        milestone_objs.append(Milestone(count=count, total_multiplier=mult))
    milestone_objs.sort(key=lambda m: m.count)

    buildings_data = data["buildings"]
    if not isinstance(buildings_data, list):
        raise ConfigError("buildings должен быть массивом")
    buildings: dict[str, BuildingConfig] = {}
    for i, b in enumerate(buildings_data):
        if not isinstance(b, dict):
            raise ConfigError(f"buildings[{i}] должен быть объектом")
        _check_keys(
            f"buildings[{i}]",
            b,
            required={"id", "baseCost", "costGrowth", "baseOutput", "outputGrowth", "maxLevel"},
        )
        bid = b["id"]
        if not isinstance(bid, str) or not bid:
            raise ConfigError(f"buildings[{i}].id должен быть непустой строкой")
        base_cost = _positive_number(f"buildings[{i}].baseCost", b["baseCost"])
        cost_growth = _positive_number(f"buildings[{i}].costGrowth", b["costGrowth"])
        base_output = _positive_number(f"buildings[{i}].baseOutput", b["baseOutput"])
        output_growth = _positive_number(f"buildings[{i}].outputGrowth", b["outputGrowth"])
        max_level = _positive_int(f"buildings[{i}].maxLevel", b["maxLevel"])
        if bid in buildings:
            raise ConfigError(f"buildings: повторяющийся id '{bid}'")
        buildings[bid] = BuildingConfig(
            id=bid,
            base_cost=base_cost,
            cost_growth=cost_growth,
            base_output=base_output,
            output_growth=output_growth,
            max_level=max_level,
        )

    fixed_data = data["fixedPurchases"]
    if not isinstance(fixed_data, list):
        raise ConfigError("fixedPurchases должен быть массивом")
    fixed: dict[str, FixedPurchaseConfig] = {}
    for i, f in enumerate(fixed_data):
        if not isinstance(f, dict):
            raise ConfigError(f"fixedPurchases[{i}] должен быть объектом")
        _check_keys(f"fixedPurchases[{i}]", f, required={"id", "cost", "category", "endsRun"})
        fid = f["id"]
        if not isinstance(fid, str) or not fid:
            raise ConfigError(f"fixedPurchases[{i}].id должен быть непустой строкой")
        cost = _positive_number(f"fixedPurchases[{i}].cost", f["cost"])
        category = f["category"]
        if not isinstance(category, str) or not category:
            raise ConfigError(f"fixedPurchases[{i}].category должен быть непустой строкой")
        ends_run = f["endsRun"]
        if not isinstance(ends_run, bool):
            raise ConfigError(f"fixedPurchases[{i}].endsRun должен быть boolean")
        if fid in fixed:
            raise ConfigError(f"fixedPurchases: повторяющийся id '{fid}'")
        fixed[fid] = FixedPurchaseConfig(id=fid, cost=cost, category=category, ends_run=ends_run)

    all_ids = {worker_id} | set(buildings.keys()) | set(fixed.keys())
    if len(all_ids) != len({worker_id}) + len(buildings) + len(fixed):
        raise ConfigError("идентификаторы worker, buildings и fixedPurchases должны быть уникальными")

    if stops_after is not None and stops_after not in fixed:
        raise ConfigError(f"manualAction.stopsAfterPurchaseId '{stops_after}' не найден в fixedPurchases")

    prestige_multiplier = 1.0
    if "prestigeMultiplier" in data:
        prestige_multiplier = _positive_number("prestigeMultiplier", data["prestigeMultiplier"])

    return Config(
        tick_seconds=tick_seconds,
        max_seconds=max_seconds,
        manual_action=ManualActionConfig(
            yield_=manual_yield,
            cooldown_seconds=manual_cooldown,
            stops_after_purchase_id=stops_after,
        ),
        worker=WorkerConfig(
            id=worker_id,
            base_cost=worker_base_cost,
            cost_growth=worker_cost_growth,
            base_rate=worker_base_rate,
            milestones=tuple(milestone_objs),
        ),
        buildings=buildings,
        fixed_purchases=fixed,
        prestige_multiplier=prestige_multiplier,
    )


def load_plan(path: str) -> Plan:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError as exc:
        raise ConfigError(f"план не найден: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(f"ошибка JSON в плане: {exc}") from exc

    if not isinstance(data, dict):
        raise ConfigError("план должен быть объектом")
    _check_keys("plan", data, required={"steps"})
    raw_steps = data["steps"]
    if not isinstance(raw_steps, list):
        raise ConfigError("plan.steps должен быть массивом")

    steps: list[WorkerStep | BuildingStep | FixedStep] = []
    for i, s in enumerate(raw_steps):
        if not isinstance(s, dict):
            raise ConfigError(f"plan.steps[{i}] должен быть объектом")
        if "kind" not in s:
            raise ConfigError(f"plan.steps[{i}]: отсутствует kind")
        kind = s["kind"]
        if kind == "worker":
            _check_keys(f"plan.steps[{i}]", s, required={"kind", "targetCount", "category"})
            target = _positive_int(f"plan.steps[{i}].targetCount", s["targetCount"])
            category = s["category"]
            if not isinstance(category, str) or not category:
                raise ConfigError(f"plan.steps[{i}].category должен быть непустой строкой")
            steps.append(WorkerStep(target_count=target, category=category))
        elif kind == "building":
            _check_keys(f"plan.steps[{i}]", s, required={"kind", "id", "targetLevel", "category"})
            bid = s["id"]
            if not isinstance(bid, str) or not bid:
                raise ConfigError(f"plan.steps[{i}].id должен быть непустой строкой")
            target = _positive_int(f"plan.steps[{i}].targetLevel", s["targetLevel"])
            category = s["category"]
            if not isinstance(category, str) or not category:
                raise ConfigError(f"plan.steps[{i}].category должен быть непустой строкой")
            steps.append(BuildingStep(building_id=bid, target_level=target, category=category))
        elif kind == "fixed":
            _check_keys(f"plan.steps[{i}]", s, required={"kind", "id"})
            fid = s["id"]
            if not isinstance(fid, str) or not fid:
                raise ConfigError(f"plan.steps[{i}].id должен быть непустой строкой")
            steps.append(FixedStep(purchase_id=fid))
        else:
            raise ConfigError(f"plan.steps[{i}]: неизвестный kind '{kind}'")

    return Plan(steps=tuple(steps))


def _validate_plan_against_config(config: Config, plan: Plan) -> None:
    for i, step in enumerate(plan.steps):
        if isinstance(step, BuildingStep):
            if step.building_id not in config.buildings:
                raise ConfigError(f"plan.steps[{i}]: неизвестное здание '{step.building_id}'")
            if step.target_level > config.buildings[step.building_id].max_level:
                raise ConfigError(
                    f"plan.steps[{i}]: targetLevel {step.target_level} превышает maxLevel "
                    f"{config.buildings[step.building_id].max_level} для '{step.building_id}'"
                )
        elif isinstance(step, FixedStep):
            if step.purchase_id not in config.fixed_purchases:
                raise ConfigError(f"plan.steps[{i}]: неизвестная покупка '{step.purchase_id}'")


def worker_cost(worker: WorkerConfig, n: int) -> float:
    """Стоимость n-го рабочего (нумерация с 0)."""
    return worker.base_cost * (worker.cost_growth ** n)


def milestone_multiplier(worker: WorkerConfig, count: int) -> float:
    """Итоговый множитель рабочих для текущего количества."""
    mult = 1.0
    for ms in worker.milestones:
        if count >= ms.count:
            mult = ms.total_multiplier
        else:
            break
    return mult


def worker_rate(worker: WorkerConfig, count: int) -> float:
    return worker.base_rate * count * milestone_multiplier(worker, count)


def building_cost(building: BuildingConfig, level: int) -> float:
    """Стоимость покупки уровня level (нумерация с 1)."""
    return building.base_cost * (building.cost_growth ** (level - 1))


def building_rate(building: BuildingConfig, level: int) -> float:
    """Пассивный доход от уровня level (нумерация с 1)."""
    return building.base_output * (building.output_growth ** (level - 1))


def _passive_rate(config: Config, state: State) -> float:
    wr = worker_rate(config.worker, state.worker_count)
    br = 0.0
    for bid, level in state.building_levels.items():
        if level > 0:
            br += building_rate(config.buildings[bid], level)
    return wr + br


def _manual_triggered(manual: ManualActionConfig, tick_seconds: float, current_time: float) -> bool:
    next_time = current_time + tick_seconds
    remainder = next_time % manual.cooldown_seconds
    return remainder < EPS or abs(manual.cooldown_seconds - remainder) < EPS


MEANINGFUL_CATEGORIES = {"unlock", "visual", "mechanical"}


def simulate(
    config: Config,
    plan: Plan,
    *,
    income_scale: float = 1.0,
    production_multiplier: float = 1.0,
) -> SimulationResult:
    if income_scale <= 0:
        raise ConfigError("income_scale должен быть положительным")
    if production_multiplier <= 0:
        raise ConfigError("production_multiplier должен быть положительным")

    _validate_plan_against_config(config, plan)

    total_multiplier = income_scale * production_multiplier

    state = State(
        money=0.0,
        worker_count=0,
        building_levels={bid: 0 for bid in config.buildings},
        fixed_purchases=set(),
    )
    events: list[PurchaseEvent] = []
    manual_active = True
    current_time = 0.0
    step_idx = 0
    completed = False
    ended_run = False

    max_ticks = int(config.max_seconds / config.tick_seconds + EPS) + 1
    for _ in range(max_ticks):
        if step_idx >= len(plan.steps) and not ended_run:
            break
        if current_time + EPS >= config.max_seconds:
            break

        # 1. Пассивный доход от состояния на начало тика.
        state.money += _passive_rate(config, state) * config.tick_seconds * total_multiplier

        # 2. Ручное действие.
        if manual_active and _manual_triggered(config.manual_action, config.tick_seconds, current_time):
            state.money += config.manual_action.yield_ * total_multiplier

        # 3. Перевод времени.
        current_time += config.tick_seconds

        # 4. Покупки текущей цели.
        while step_idx < len(plan.steps):
            step = plan.steps[step_idx]
            if isinstance(step, WorkerStep):
                if state.worker_count >= step.target_count:
                    step_idx += 1
                    continue
                cost = worker_cost(config.worker, state.worker_count)
                if state.money + EPS >= cost:
                    state.money -= cost
                    state.worker_count += 1
                    events.append(
                        PurchaseEvent(
                            time_seconds=current_time,
                            kind="worker",
                            item_id=config.worker.id,
                            level=None,
                            count=state.worker_count,
                            cost=cost,
                            category=step.category,
                        )
                    )
                else:
                    break
            elif isinstance(step, BuildingStep):
                bcfg = config.buildings[step.building_id]
                cur_level = state.building_levels[step.building_id]
                if cur_level >= step.target_level:
                    step_idx += 1
                    continue
                next_level = cur_level + 1
                cost = building_cost(bcfg, next_level)
                if state.money + EPS >= cost:
                    state.money -= cost
                    state.building_levels[step.building_id] = next_level
                    events.append(
                        PurchaseEvent(
                            time_seconds=current_time,
                            kind="building",
                            item_id=bcfg.id,
                            level=next_level,
                            count=None,
                            cost=cost,
                            category=step.category,
                        )
                    )
                else:
                    break
            elif isinstance(step, FixedStep):
                fcfg = config.fixed_purchases[step.purchase_id]
                if state.money + EPS >= fcfg.cost:
                    state.money -= fcfg.cost
                    state.fixed_purchases.add(step.purchase_id)
                    events.append(
                        PurchaseEvent(
                            time_seconds=current_time,
                            kind="fixed",
                            item_id=fcfg.id,
                            level=None,
                            count=None,
                            cost=fcfg.cost,
                            category=fcfg.category,
                        )
                    )
                    if config.manual_action.stops_after_purchase_id == fcfg.id:
                        manual_active = False
                    if fcfg.ends_run:
                        ended_run = True
                        completed = True
                        break
                    step_idx += 1
                else:
                    break

        if ended_run:
            break

    max_gap = 0.0
    last_meaningful_time = 0.0
    for event in events:
        if event.category in MEANINGFUL_CATEGORIES:
            gap = event.time_seconds - last_meaningful_time
            if gap > max_gap:
                max_gap = gap
            last_meaningful_time = event.time_seconds

    return SimulationResult(
        completed=completed,
        elapsed_seconds=current_time,
        events=events,
        state=state.copy(),
        max_meaningful_gap_seconds=max_gap,
    )


def _format_time(seconds: float) -> str:
    total = int(round(seconds / 1))  # секунды — целые кратные tickSeconds
    minutes = total // 60
    secs = total % 60
    return f"{minutes:02d}:{secs:02d}"


def _render_event(event: PurchaseEvent) -> str:
    parts = [
        _format_time(event.time_seconds),
        "purchase",
        event.item_id,
    ]
    if event.count is not None:
        parts.append(f"count={event.count}")
    if event.level is not None:
        parts.append(f"level={event.level}")
    parts.append(f"cost={event.cost:.2f}")
    parts.append(f"category={event.category}")
    return " | ".join(parts)


def run(
    config_path: str,
    plan_path: str,
    *,
    income_scale: float = 1.0,
    prestige: bool = False,
) -> tuple[int, str]:
    try:
        config = load_config(config_path)
        plan = load_plan(plan_path)
        production_multiplier = config.prestige_multiplier if prestige else 1.0
        result = simulate(config, plan, income_scale=income_scale, production_multiplier=production_multiplier)
    except ConfigError as exc:
        return 2, f"ERROR | {exc}"

    lines = [_render_event(e) for e in result.events]
    lines.append(
        f"SUMMARY | completed={str(result.completed).lower()} "
        f"| elapsedSeconds={int(round(result.elapsed_seconds))} "
        f"| maxMeaningfulGapSeconds={int(round(result.max_meaningful_gap_seconds))}"
    )

    # Успех — только если куплена покупка с endsRun=true.
    code = 0 if result.completed else 3

    return code, "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Симулятор баланса одного забега.")
    parser.add_argument("--config", required=True, help="Путь к JSON-конфигу")
    parser.add_argument("--plan", required=True, help="Путь к JSON-плану")
    parser.add_argument("--income-scale", type=float, default=1.0, help="Множитель дохода (default: 1.0)")
    parser.add_argument("--prestige", action="store_true", help="Использовать prestigeMultiplier из конфига")
    args = parser.parse_args(argv)

    code, output = run(args.config, args.plan, income_scale=args.income_scale, prestige=args.prestige)
    print(output)
    return code


if __name__ == "__main__":
    sys.exit(main())
