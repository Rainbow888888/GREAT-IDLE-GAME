# tools/sim

Детерминированный симулятор баланса одного забега.

## Запуск

Smoke:

```powershell
python tools/sim/sim.py --config tools/sim/fixtures/smoke-config.json --plan tools/sim/fixtures/smoke-plan.json
```

Забег I:

```powershell
python tools/sim/sim.py --config Assets/Game/Resources/balance/run1.json --plan tools/sim/run1-plan.json
python tools/sim/sim.py --config Assets/Game/Resources/balance/run1.json --plan tools/sim/run1-plan.json --income-scale 0.9
python tools/sim/sim.py --config Assets/Game/Resources/balance/run1.json --plan tools/sim/run1-plan.json --prestige
```

### CLI-опции

- `--config PATH` — путь к JSON-конфигу (обязательный).
- `--plan PATH` — путь к JSON-плану (обязательный).
- `--income-scale N` — множитель дохода, default `1.0`.
- `--prestige` — использовать `config.prestigeMultiplier` как production multiplier.

`SUMMARY` дополнительно печатает `maxMeaningfulGapSeconds=N`.

## Тесты

```powershell
python -m unittest tools.sim.test_sim -v
```

## Коды возврата CLI

- `0` — план выполнен: куплена покупка с `endsRun=true`.
- `2` — ошибка конфигурации (`ConfigError`).
- `3` — план не завершён: либо закончилось `maxSeconds`, либо в плане отсутствует `endsRun=true`.
