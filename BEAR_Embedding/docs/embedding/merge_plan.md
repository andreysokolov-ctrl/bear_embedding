# Подготовка merge и перенос

## Что уже подготовлено

- База: `IRelapseIT/BEAR_Chanking-Parsing` commit `c2447d4ff89cb0f5e33006d505e6d0243930c292`.
- Ветка реализации: `feature/embedding-pipeline` поверх этой базы.
- Сохранены оба пакета `bear-text-beta` и `bear-fusion-lab`; нет переименования исходных сущностей.
- Добавлены класс, шаблон BGE-M3, метрики, демо, тесты, документация и CI для GitHub/GitLab.
- `Services` использует новый класс для онлайн-инференса; offline/test режимы сохранены.
- Внешний `dedoc_service`, отсутствующий в upstream, явно обозначен как необязательная зависимость
  одного его теста. Реализация Dedoc не подменялась заглушкой в production-коде.
- Тест RSS experimental demo пропускается, если psutil не видит процессы в среде;
  в обычной ОС проверка по-прежнему выполняется. Production-логика лимитов не менялась.

Целевой репозиторий получен: `https://github.com/andreysokolov-ctrl/bear_embedding.git`.
При проверке 05.11.2026 он был пустым. GitHub подтвердил права владельца аккаунта,
но запись через подключение отклонил: `403 Resource not accessible by integration`.
Удалённых commit/ветки/PR пока нет. Для публикации нужно разрешить приложению доступ
к этому репозиторию либо выполнить обычный git push от своего аккаунта.
Точные команды с уже подставленным адресом: [PUBLISH_TO_GITHUB.md](../../PUBLISH_TO_GITHUB.md).
История upstream и feature-ветка полностью сохранены в bundle.

## Существующий BEAR на GitHub или GitLab

В архиве есть исходники, patch и `transfer/BEAR_Embedding.bundle` с историей базы и feature-веткой.
Сначала распаковать ZIP. Из существующего локального checkout целевого BEAR:

```bash
git fetch /absolute/path/to/transfer/BEAR_Embedding.bundle feature/embedding-pipeline
git switch -c feature/embedding-pipeline-import FETCH_HEAD
python -m pip install -e './bear-text-beta[dev]'
python -m pytest bear-text-beta/tests -q
```

Если целевой проект имеет общую историю с upstream, можно открыть PR/MR из импортированной
ветки в целевую main. Прямой push в защищённую main не требуется.

Если корни истории разные, не применять `--allow-unrelated-histories` вслепую.
Создать ветку **от целевой main**, затем перенести оба пакета и документацию в согласованные
каталоги (`git restore --source=...` по выбранным путям или ручной перенос).
Сверить основную командную схему `Chunk`/`ProcessingResult` и порты; при отличиях писать адаптер,
а не держать два параллельных несовместимых класса. После этого повторить тесты и создать MR.
Схема основного GitLab из презентации не была доступна для чтения в этой задаче.

## Новый пустой репозиторий

Владелец создаёт пустой `BEAR-Embedding` без README/License/.gitignore (или предоставляет
существующий пустой репозиторий с доступом). Полную историю из bundle можно развернуть так:

```bash
git clone transfer/BEAR_Embedding.bundle BEAR-Embedding
cd BEAR-Embedding
git remote rename origin transfer
git branch main transfer/main
git remote add origin https://github.com/andreysokolov-ctrl/bear_embedding.git
git push origin main
git push -u origin feature/embedding-pipeline
```

Для GitLab заменить URL на адрес целевого проекта. Это обычный push, без force.
В `main` находится исходная база, реализация - в feature-ветке. Затем открыть PR/MR
`feature/embedding-pipeline -> main`. Обе ветки входят в bundle. Рекомендованное название MR:
`Добавить EmbeddingPipeline между чанкингом и Qdrant`.

Описание MR:

> Добавляет сборку поисковых запросов и пакетную векторизацию готовых чанков через Infinity.
> Сохраняет существующие ProcessingResult/Chunk, метаданные, профили и фильтры Qdrant.
> Включает проверку токенного бюджета, нормализацию, опциональный кэш, IR-метрики и тесты контрактов.
> Реальные модели и сервисы проверяются отдельным smoke-test; новый RuBQ-бенчмарк не выполнялся.

## Важное различие форматов GitLab

Обычный ZIP исходников не является GitLab Project Export. Нельзя обещать его прямой импорт
через кнопку импорта проекта. Рабочие варианты: распаковать ZIP и сделать git push из bundle,
либо после публикации использовать **Repository by URL** при включённой этой возможности.
GitLab Project Export - отдельный архив, формируемый самим GitLab, с метаданными проекта;
этот пакет им не является. Здесь сохранена Git-история, но не issues/MR/настройки доступа.

Первичные инструкции: [GitLab Project Export](https://docs.gitlab.com/user/project/settings/import_export/)
и [Repository by URL](https://docs.gitlab.com/user/import/third_party_systems/repo_by_url/).

## До командного merge

Сверить фактическую схему основного GitLab и способ DI, запустить Infinity/Qdrant smoke,
проверить ту же ревизию весов и токенизатора, затем прогнать RuBQ с неизменными qrels.
Статусы экспериментального Fusion не переводить в accepted без проверки source fidelity.
Публикация и фактический PR ожидают разрешения на запись через GitHub-подключение; целевой URL уже известен.
