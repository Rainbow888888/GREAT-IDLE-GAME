# Ревью Codex — S2.1 Unity project shell

Дата: 2026-09-21 · Вердикт: **ACCEPT**

## Проверено

- проект использует Unity `6000.3.24f1`;
- `Game.Core` имеет `noEngineReferences=true`, `Game.Runtime` ссылается на Core;
- `Run1ConfigLoader` читает `Resources/balance/run1` через `JsonUtility`;
- независимый EditMode-прогон Codex: `1/1 passed`;
- Python-регрессия симулятора: `14/14 passed`;
- `run1.json` не изменён, для Unity создан `.meta`;
- новые файлы в `Assets/` имеют `.meta`;
- `Library/`, `Logs/`, `UserSettings/` игнорируются Git;
- временная bootstrap-папка отсутствует.

Заявленный mutation-check подтверждён исполнителем; сам тест содержит прямые проверки
конкретных значений, поэтому подмена `2400` на `2401` действительно проверяет чтение JSON.

## Неблокирующий хвост для S2.2

Шаблон оставил `productName=GREAT-IDLE-GAME-BOOTSTRAP`, `DefaultCompany` и временный
application identifier. До первой сборки S2.2 должна заменить их через Unity Editor API,
не ручным редактированием YAML.
