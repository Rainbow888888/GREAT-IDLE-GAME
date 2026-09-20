# GREAT-IDLE-GAME — текущий контекст

Снимок: 2026-09-21. При расхождении действуют фактический Git, `PROJECT_CONTRACT.md`
и `ROADMAP.md`.

## Где мы

Текущий этап: **2 — каркас Unity-проекта**.
Этап 1 закрыт коммитом `945b379`. Текущая задача: **S2.1 — рабочий Unity-проект
и импорт run1.json**. Unity-кода пока нет.

## Проверенное состояние

- Локальная папка: `O:\AI\GREAT-IDLE-GAME`.
- GitHub: `Rainbow888888/GREAT-IDLE-GAME`, ветка `main`.
- S1.2: 14/14 тестов, baseline EMP 1895 сек, meaningful gap 273 сек,
  prestige-повтор 240 сек, ревью Codex `ACCEPT`.
- Unity `6000.3.24f1` установлена по `O:\UNITY\6000.3.24f1\Editor\Unity.exe`.
- Unity CLI `1.0.0-beta.10`; доступен шаблон `com.unity.template.2d`.

## Зафиксированный цикл забега I

Ручная резка → рабочие → Salvage Rig → Crew Quarters → Workshop → авто-доставка →
корабль просыпается → Guard Post → первая угроза → пробит внешний слой → EMP.
Один ресурс Scrap, четыре здания, без дополнительных систем.

Codex — главный ревьювер; Claude — независимый критик на гейтах. После `ACCEPT`
Codex сразу коммитит и пушит принятую задачу (D-024).

## Следующий результат

Kimi выполняет `docs/tasks/S2.1-unity-project-shell.md`: безопасно создаёт Unity-проект
в уже существующем репозитории и доказывает одним EditMode-тестом, что игровой
`run1.json` реально читается через Unity.

После реализации Codex проверяет фактические файлы и пишет
`docs/reviews/S2.1-unity-project-shell/codex.md`. Claude на этой задаче не обязателен.

## Не делать сейчас

URP, сцена, UI, арт, Windows build, экономика, второй забег и новые системы.

## Порядок чтения

1. `AGENTS.md`.
2. `docs/tasks/S2.1-unity-project-shell.md`.
3. `docs/UNITY_PITFALLS.md`.
4. `PROJECT_CONTRACT.md` §7.

## Стартовый промпт исполнителю

```text
Проект GREAT-IDLE-GAME, папка O:\AI\GREAT-IDLE-GAME.
Выполни только docs/tasks/S2.1-unity-project-shell.md. Сначала проверь задачу на
противоречия и наличие лицензии Unity, затем реализуй, запусти все проверки и покажи
фактический diff. Документы не меняй и не коммить.
```

Название следующего чата: `🟡 S2.1 — Unity-проект читает баланс`
