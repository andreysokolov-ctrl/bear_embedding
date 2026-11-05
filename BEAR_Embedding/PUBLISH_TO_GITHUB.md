# Публикация в andreysokolov-ctrl/bear_embedding

Адрес уже указан: https://github.com/andreysokolov-ctrl/bear_embedding.git.
Код готов. На 05.11.2026 создание первого файла через подключение отклонено GitHub:
`403 Resource not accessible by integration`. Репозиторий был пустым; удалённый PR не создан.

## Через подключённое приложение

Разрешить GitHub-подключению доступ к `bear_embedding` в настройках подключения/установки
приложения. После изменения доступа публикацию можно продолжить. Токены и пароли в чат
передавать не нужно.

## Обычным git push

Команды ниже рассчитаны на всё ещё пустой репозиторий. Если в нём появились новые commit,
сначала fetch и проверить историю; force push не использовать.

Распаковать ZIP, открыть терминал в каталоге `BEAR_Embedding`, где находятся README и `transfer/`:

```bash
git clone -b feature/embedding-pipeline transfer/BEAR_Embedding.bundle bear_embedding
cd bear_embedding
git remote rename origin transfer
git branch main transfer/main
git remote add origin https://github.com/andreysokolov-ctrl/bear_embedding.git
git push -u origin main
git push -u origin feature/embedding-pipeline
```

Git использует авторизацию вашего компьютера. Пароль аккаунта GitHub не подставлять
в команды или URL; при необходимости использовать штатное окно менеджера учётных данных.

После успешных push открыть:

https://github.com/andreysokolov-ctrl/bear_embedding/compare/main...feature/embedding-pipeline

Нажать **Create pull request**. Заголовок:

> Добавить EmbeddingPipeline между чанкингом и Qdrant

Описание:

> Добавляет сборку поисковых запросов и пакетную векторизацию готовых чанков через Infinity.
> Сохраняет ProcessingResult/Chunk, метаданные, профили и фильтры Qdrant.
> Реализованы проверка токенного бюджета, L2-нормализация, опциональный кэш и IR-метрики.
> Локальная проверка: 157 тестов прошли, 2 пропущены с указанными причинами.
> Настоящий инференс и сервер Qdrant проверяются отдельным smoke-test; новый RuBQ-прогон не выполнялся.

`main` будет содержать исходную базу парсинга/чанкинга, а feature-ветка - модуль и интеграцию.
После проверки PR слияние выполняется отдельно. Git bundle сохраняет исходную Git-историю,
а не только копию файлов.
