# S1.1 — ядро симулятора экономики

Этап: 1 · Исполнитель: Kimi/OpenCode · Главное ревью: Codex
Визуальная приёмка: не требуется · Баланс забега I в эту задачу не входит

## Наблюдаемый результат

Команда

```powershell
python tools/sim/sim.py --config tools/sim/fixtures/smoke-config.json --plan tools/sim/fixtures/smoke-plan.json
```

завершается с кодом `0` и печатает детерминированный таймлайн, в котором:

- первый рабочий куплен на `00:10`;
- Rig L1 — на `00:25`;
- пятый рабочий — на `00:35`;
- авто-доставка — на `00:40`;
- Rig L2 — на `00:46`;
- EMP — на `00:54`.

Исполнитель не выбирает правила экономики и не подбирает баланс — они заданы ниже.

## Разрешённые файлы

- `tools/sim/sim.py`;
- `tools/sim/test_sim.py`;
- `tools/sim/README.md`;
- `tools/sim/fixtures/smoke-config.json`;
- `tools/sim/fixtures/smoke-plan.json`.

Другие файлы не менять.

## Точный формат smoke-config.json

```json
{
  "schemaVersion": 1,
  "tickSeconds": 1,
  "maxSeconds": 120,
  "manualAction": { "yield": 1, "cooldownSeconds": 1, "stopsAfterPurchaseId": "auto_delivery" },
  "worker": {
    "id": "worker",
    "baseCost": 10,
    "costGrowth": 1.17,
    "baseRate": 1,
    "milestones": [
      { "count": 5, "totalMultiplier": 1.5 },
      { "count": 10, "totalMultiplier": 1.75 },
      { "count": 20, "totalMultiplier": 2.0 }
    ]
  },
  "buildings": [
    {
      "id": "rig",
      "baseCost": 30,
      "costGrowth": 2.4,
      "baseOutput": 3,
      "outputGrowth": 1.6,
      "maxLevel": 2
    }
  ],
  "fixedPurchases": [
    { "id": "auto_delivery", "cost": 50, "category": "mechanical", "endsRun": false },
    { "id": "emp", "cost": 100, "category": "mechanical", "endsRun": true }
  ]
}
```

Поля обязательны. Неизвестные поля, дубли id, неположительные числа и неизвестные id
в плане дают `ConfigError`. `cooldownSeconds` должен делиться на `tickSeconds` без остатка.

## Точный формат smoke-plan.json

```json
{
  "steps": [
    { "kind": "worker", "targetCount": 1, "category": "routine" },
    { "kind": "building", "id": "rig", "targetLevel": 1, "category": "unlock" },
    { "kind": "worker", "targetCount": 5, "category": "routine" },
    { "kind": "fixed", "id": "auto_delivery" },
    { "kind": "building", "id": "rig", "targetLevel": 2, "category": "visual" },
    { "kind": "fixed", "id": "emp" }
  ]
}
```

План выполняется строго сверху вниз. Цель worker/building покупается по одному уровню
или рабочему, пока не достигнут target. Если после покупки хватает на следующую цель,
она покупается в ту же секунду.

## Правила расчёта

Внутри расчёта значения не округлять. Для сравнения денег использовать epsilon `1e-9`.
Округление до двух знаков применяется только при печати.

```text
WorkerCost(n)   = baseCost × costGrowth^n, где n = текущее число рабочих
WorkerRate      = baseRate × count × последний достигнутый totalMultiplier
BuildingCost(L) = baseCost × costGrowth^(L-1), где L — покупаемый уровень
BuildingRate(L) = baseOutput × outputGrowth^(L-1)
PassiveRate     = WorkerRate + сумма BuildingRate текущих уровней
```

Milestone-множители итоговые, не перемножаются. До первой вехи множитель `1`.

Один тик `[t, t+1]`:

1. начислить passive income от состояния на начале тика;
2. начислить manual yield, если действие активно и на `t+1` приходится cooldown;
3. перевести время в `t+1`;
4. покупать текущую цель плана, пока она доступна и не выполнена;
5. новые покупки начинают производить только со следующего тика;
6. покупка с `endsRun=true` немедленно завершает симуляцию.

После `auto_delivery` ручное действие не выполняется начиная со следующего тика.

## Формат текстового вывода

Одна покупка — одна строка; время всегда `MM:SS`, числа — два знака:

```text
00:10 | purchase | worker | count=1 | cost=10.00 | category=routine
00:25 | purchase | rig | level=1 | cost=30.00 | category=unlock
...
00:54 | purchase | emp | cost=100.00 | category=mechanical
SUMMARY | completed=true | elapsedSeconds=54
```

Промежуточные покупки рабочих тоже печатаются. При timeout summary содержит
`completed=false`; при ошибке конфигурации одна строка начинается с `ERROR |`.

## Публичный API sim.py

- `load_config(path) -> Config`;
- `load_plan(path) -> Plan`;
- `simulate(config, plan) -> SimulationResult`;
- `ConfigError` для ошибок входных данных.

`SimulationResult` хранит `completed`, `elapsed_seconds`, итоговое состояние и список
событий. CLI возвращает `0` при покупке `endsRun`, `2` при `ConfigError`, `3` если
`maxSeconds` закончились раньше плана.

## Обязательные тесты

1. `test_worker_costs`: `10`, `11.7`, `13.689` для n=0/1/2.
2. `test_building_levels`: L1/L2 стоят `30/72`, производят `3/4.8`.
3. `test_milestones_are_total`: count 4/5/10/20 → `1/1.5/1.75/2`.
4. `test_smoke_timeline`: ключевые времена ровно `10,25,35,40,46,54`.
5. `test_deterministic`: два запуска дают полностью одинаковые события и итог.
6. `test_config_is_used`: при manual yield `2` первый рабочий куплен на `5` секунде.
7. `test_unknown_plan_id_rejected`: неизвестный id даёт `ConfigError`.
8. `test_timeout`: при `maxSeconds=20` результат не completed, CLI-код `3`.

Проверка:

```powershell
python -m unittest tools.sim.test_sim -v
```

## Приёмка

- ровно перечисленные пять файлов созданы, другие файлы не изменены;
- все 8 тестов проходят;
- CLI показывает шесть контрольных времён;
- README содержит только команды запуска, тестов и описание кодов возврата;
- исполнитель показывает `git diff` и вывод тестов, но не коммитит.

## Запрещено

Run I config, подбор баланса, `Assets/`, Unity/C#, графики, оптимизатор, случайность,
сторонние Python-пакеты, дополнительные сущности и рефакторинг документов.
