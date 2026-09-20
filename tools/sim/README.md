# tools/sim

Детерминированный симулятор баланса одного забега.

## Запуск

```powershell
python tools/sim/sim.py --config tools/sim/fixtures/smoke-config.json --plan tools/sim/fixtures/smoke-plan.json
```

## Тесты

```powershell
python -m unittest tools.sim.test_sim -v
```

## Коды возврата CLI

- `0` — план выполнен: куплена покупка с `endsRun=true`.
- `2` — ошибка конфигурации (`ConfigError`).
- `3` — план не завершён: либо закончилось `maxSeconds`, либо в плане отсутствует `endsRun=true`.
