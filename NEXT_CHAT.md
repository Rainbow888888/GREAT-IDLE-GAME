# GREAT-IDLE-GAME — текущий контекст

Снимок: 2026-09-21. При расхождении действуют фактический Git, `PROJECT_CONTRACT.md`
и `ROADMAP.md`.

## Где мы

Текущий этап: **2 — каркас Unity-проекта**.
Этап 1 закрыт коммитом `945b379`. S2.1 принята и запушена (`08e627e`).
Текущая задача: **S2.2 — URP 2D, bootstrap-сцена и Windows build**.

## Проверенное состояние

- Локальная папка: `O:\AI\GREAT-IDLE-GAME`.
- GitHub: `Rainbow888888/GREAT-IDLE-GAME`, ветка `main`.
- S1.2: 14/14 тестов, baseline EMP 1895 сек, meaningful gap 273 сек,
  prestige-повтор 240 сек, ревью Codex `ACCEPT`.
- Unity `6000.3.24f1` установлена по `O:\UNITY\6000.3.24f1\Editor\Unity.exe`.
- Unity CLI `1.0.0-beta.10`; доступен шаблон `com.unity.template.2d`.
- S2.1: Unity EditMode 1/1, Python 14/14; JSON читается через Resources/JsonUtility.
- Принятая база S2.1 сохранена в `08e627e`; работать нужно на актуальном `main`,
  не переходя в detached HEAD.

## Зафиксированный цикл забега I

Ручная резка → рабочие → Salvage Rig → Crew Quarters → Workshop → авто-доставка →
корабль просыпается → Guard Post → первая угроза → пробит внешний слой → EMP.
Один ресурс Scrap, четыре здания, без дополнительных систем.

Codex — главный ревьювер; Claude — независимый критик на гейтах. После `ACCEPT`
Codex сразу коммитит и пушит принятую задачу (D-024).

## Следующий результат

Kimi выполняет `docs/tasks/S2.2-urp-bootstrap-build.md`: точечно устанавливает URP,
создаёт 2D renderer и одну bootstrap-сцену через Unity API, запускает 2 EditMode-теста
и собирает Windows `.exe` с текстом `GREAT IDLE GAME`.

После реализации Codex проверяет фактические файлы и пишет
`docs/reviews/S2.2-urp-bootstrap-build/codex.md`; затем Claude критикует гейт этапа 2.
Этап закрывается только после визуального подтверждения владельца.

## Не делать сейчас

Экономика, клики, рабочие, здания, игровой UI, арт, анимации и новые системы.

## Порядок чтения

1. `AGENTS.md`.
2. `docs/tasks/S2.2-urp-bootstrap-build.md`.
3. `docs/UNITY_PITFALLS.md`.
4. `PROJECT_CONTRACT.md` §7.

## Стартовый промпт исполнителю

```text
Проект GREAT-IDLE-GAME, папка O:\AI\GREAT-IDLE-GAME.
Выполни только docs/tasks/S2.2-urp-bootstrap-build.md на актуальной ветке main.
Не делай checkout 08e627e: это историческая база S2.1, а не рабочий HEAD. Сначала
проверь preflight, затем выполняй package phase и setup phase раздельно. Запусти тесты,
mutation-check и Windows build, покажи фактический diff и логи. Не коммить.
```

Название следующего чата: `🟡 S2.2 — первый запускаемый build`
