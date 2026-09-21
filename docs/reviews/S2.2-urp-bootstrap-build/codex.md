# Ревью Codex — S2.2 URP 2D bootstrap build

Дата: 2026-09-21 · Итоговый вердикт: **ACCEPT**

## Блокер

Свежая Windows-сборка запускается, но показывает только фон `#101318`: текст
`GREAT IDLE GAME` отсутствует. В сохранённой сцене у корневого `Canvas` записан
`m_LocalScale: {x: 0, y: 0, z: 0}`, поэтому весь дочерний UI схлопнут до нуля.

Это не теоретическое замечание: Codex заново собрал проект через
`Game.Editor.BuildWindows.Build`, запустил полученный `.exe` и получил пустой кадр.

## Требуемое исправление

1. В `ProjectSetup.EnsureBootstrapScene` после создания Canvas явно сохранить
   ненулевой scale корневого `RectTransform` (ожидается `Vector3.one`).
2. Расширить существующий `BootstrapProjectContractIsSaved`, чтобы он падал при
   нулевом scale Canvas/Title, а не проверял только `Title.sizeDelta`.
3. Повторно выполнить EditMode-тесты, Windows build и визуальную проверку свежего
   `.exe`. На кадре должен быть виден центрированный `GREAT IDLE GAME`.

Новые тестовые классы не добавлять: по контракту итог остаётся `2/2`.

## Что уже прошло

- независимый EditMode-прогон Codex: `2/2 passed`;
- URP asset и `Renderer2DData` сохранены и связаны;
- Graphics и все Quality levels ссылаются на один URP asset;
- прямой набор пакетов соответствует задаче, запрещённые пакеты отсутствуют;
- свежая Windows-сборка завершилась успешно (`99,002,875` байт);
- compile/shader/default-renderer ошибок в build log нет;
- все новые файлы в `Assets/` имеют `.meta`, build и logs игнорируются Git.

На первом круге коммит и push были запрещены до исправления блокера.

## Повторное ревью исправления

Визуальный дефект устранён, но исправление **не принято**: `ProjectSetup` читает
`Bootstrap.unity` как текст и меняет Unity YAML регулярным выражением в
`FixCanvasLocalScaleInSavedScene`. Это прямо нарушает §1 задачи («не редактировать
`.unity` как текст») и создаёт хрупкую зависимость от внутреннего формата сцены.

Требовалось удалить весь YAML/Regex-патч и проверять Canvas через Unity API.

## Итоговая приёмка

- YAML/Regex-патч полностью удалён; `ProjectSetup` использует Unity Editor API;
- регрессионный тест открывает сцену и проверяет Canvas через Unity API;
- независимый EditMode-прогон Codex: `2/2 passed`;
- Python-регрессия симулятора: `14/14 passed`;
- независимая Windows-сборка Codex успешна (`99,002,875` байт);
- свежий `.exe` запущен: по центру виден `GREAT IDLE GAME` на фоне `#101318`;
- compile/shader/default-renderer ошибок в build log нет.

Нулевой сериализованный scale корневого Overlay Canvas в batchmode не означает
нулевой runtime-scale: `CanvasScaler` пересчитывает его после создания экрана. Это
подтверждено фактическим запуском свежей сборки.
