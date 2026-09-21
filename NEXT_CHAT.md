# GREAT-IDLE-GAME — текущий контекст

Снимок: 2026-09-21. При расхождении действуют фактический Git, `PROJECT_CONTRACT.md`
и `ROADMAP.md`.

## Где мы

Текущий этап: **2 — каркас Unity-проекта**.
Этап 1 закрыт коммитом `945b379`. S2.1 принята и запушена (`08e627e`).
S2.2 технически принята Codex. Статус этапа: **ожидание визуального подтверждения
владельца и критики Claude**.

## Проверенное состояние

- Локальная папка: `O:\AI\GREAT-IDLE-GAME`.
- GitHub: `Rainbow888888/GREAT-IDLE-GAME`, ветка `main`.
- S1.2: 14/14 тестов, baseline EMP 1895 сек, meaningful gap 273 сек,
  prestige-повтор 240 сек, ревью Codex `ACCEPT`.
- Unity `6000.3.24f1` установлена по `O:\UNITY\6000.3.24f1\Editor\Unity.exe`.
- Unity CLI `1.0.0-beta.10`; доступен шаблон `com.unity.template.2d`.
- S2.1: Unity EditMode 1/1, Python 14/14; JSON читается через Resources/JsonUtility.
- S2.2: Unity EditMode 2/2, Python 14/14, Windows build успешен; Codex запустил
  свежий `.exe` и увидел центрированный `GREAT IDLE GAME`.
- Принятая база S2.1 сохранена в `08e627e`; работать нужно на актуальном `main`,
  не переходя в detached HEAD.

## Зафиксированный цикл забега I

Ручная резка → рабочие → Salvage Rig → Crew Quarters → Workshop → авто-доставка →
корабль просыпается → Guard Post → первая угроза → пробит внешний слой → EMP.
Один ресурс Scrap, четыре здания, без дополнительных систем.

Codex — главный ревьювер; Claude — независимый критик на гейтах. После `ACCEPT`
Codex сразу коммитит и пушит принятую задачу (D-024).

## Следующий результат

Владелец запускает свежий `Builds/Windows/GREAT-IDLE-GAME.exe` и подтверждает, что
видит заголовок. Затем Claude читает задачу, фактический diff и ревью Codex и даёт
независимую критику гейта этапа 2. До этих двух подтверждений этап не закрыт.

## Не делать сейчас

Экономика, клики, рабочие, здания, игровой UI, арт, анимации и новые системы.

## Порядок чтения

1. `AGENTS.md`.
2. `docs/tasks/S2.2-urp-bootstrap-build.md`.
3. `docs/reviews/S2.2-urp-bootstrap-build/codex.md`.
4. `docs/UNITY_PITFALLS.md`.
5. `PROJECT_CONTRACT.md` §7.

## Стартовый промпт Claude

```text
Проведи независимую критику гейта этапа 2 GREAT-IDLE-GAME. Ничего не изменяй.
Прочитай ROADMAP.md (этап 2), docs/tasks/S2.2-urp-bootstrap-build.md,
docs/reviews/S2.2-urp-bootstrap-build/codex.md и фактический diff принятого коммита.
Ищи только блокеры перехода к этапу 3; отдельно отметь, что требует визуального
подтверждения владельца.
```

Название следующего чата: `⏸ ЭТАП 2 — визуальный гейт и критика Claude`
