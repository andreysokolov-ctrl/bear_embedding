# BEAR Embedding

Класс Python `EmbeddingPipeline`: получение готовых текстовых чанков, сборка поисковых запросов и векторизация через внешний Infinity.

Целевой репозиторий: [andreysokolov-ctrl/bear_embedding](https://github.com/andreysokolov-ctrl/bear_embedding).

## Начало работы

- [Установка, использование класса и примеры](README_EMBEDDING.md)
- [Публикация в GitHub](PUBLISH_TO_GITHUB.md)
- [Контракты с парсингом, чанкингом и Qdrant](docs/embedding/architecture.md)
- [Разбор рекомендаций DeepSeek](docs/embedding/deepseek_review.md)
- [Проверки и их ограничения](docs/embedding/validation.md)
- [Merge и перенос в GitLab](docs/embedding/merge_plan.md)
- [Исходный README блока парсинга/чанкинга](README_PARSING.md)

Код предыдущего блока сохранён в `bear-text-beta/` и `bear-fusion-lab/`.
База: [IRelapseIT/BEAR_Chanking-Parsing](https://github.com/IRelapseIT/BEAR_Chanking-Parsing), commit `c2447d4ff89cb0f5e33006d505e6d0243930c292`.

Ветка реализации: `feature/embedding-pipeline`; `main` в Git bundle содержит исходную базу для проверки и слияния через PR.
