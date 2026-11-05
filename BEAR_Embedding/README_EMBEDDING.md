# BEAR: получение текста, сбор запроса, векторизация

Реализация: `bear-text-beta/src/bear_text_beta/embedding_pipeline.py`, класс **EmbeddingPipeline**.
Автор задачи: Соколов Андрей Викторович, ЕТ-212.

Сборка основана на [BEAR_Chanking-Parsing](https://github.com/IRelapseIT/BEAR_Chanking-Parsing),
commit `c2447d4ff89cb0f5e33006d505e6d0243930c292`. Оба исходных пакета сохранены.
Изменения подготовлены в ветке `feature/embedding-pipeline` поверх этого commit.

## Что делает класс

У документов и вопросов два входа в одну embedding-модель:

1. Документы: `ProcessingResult.chunks[].embedding_text` -> пакетная векторизация -> `EmbeddedChunk[]`.
2. Вопрос: исходный текст -> NFC и нормализация пробелов -> необязательное преобразование -> вектор.

Документ не превращается в поисковый вопрос. Парсинг и чанкинг выполняет предыдущий блок.
Заголовки/breadcrumbs уже находятся в `embedding_text`; второй раз они не добавляются.
`Chunk.text`, `source_spans`, порядок чанков, ID, вложения и метаданные сохраняются.

Модель живёт во внешнем **Infinity**. Python-класс использует `EmbeddingProvider`, проверяет
размерность/NaN/Inf/нулевые векторы, нормализует L2 и не обрезает вход молча.
Qdrant, активацией поколений и фильтрами пространства продолжает управлять `IndexingService`.

## Установка и проверка без GPU

Python **3.12** (требование предыдущего блока). Из корня проекта:

Для воспроизведения проверенного окружения после создания venv можно сначала выполнить
`python -m pip install -r requirements.verified.txt`. Это зафиксированные наблюдённые версии,
не веса моделей; обычная установка ниже использует диапазоны зависимостей upstream.

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e "./bear-text-beta[dev]" -e "./bear-fusion-lab[demo,acceptance]"
python -m pytest bear-text-beta/tests -q
# Для полной проверки upstream Fusion нужен только токенизатор E5, без весов:
bear --model-dir bear-text-beta/models/e5 prepare-model
python -m pytest bear-fusion-lab/tests -q
python examples/embedding_pipeline_demo.py
```

Демо использует явно обозначенные тестовые векторы и HTTP-заглушки. Оно проверяет сборку и
контракты, **не** качество модели. Для запуска этих проверок модели скачивать не нужно.
Полные upstream-тесты Fusion отдельно используют токенизатор E5 и зависимости PDF/OCR из extras;
OCR-проверки также требуют системный Tesseract. Минимальный core/новый модуль проверяются без них.

## Настоящий инференс и Qdrant

Подготовить токенизатор с фиксацией ревизии (веса без `--weights` не скачиваются):

```bash
bear --model-dir models/bge-m3 prepare-model --model bge-m3
```

При необходимости загрузить и веса в тот же каталог:

```bash
bear --model-dir models/bge-m3 prepare-model --model bge-m3 --weights
```

Развернуть Infinity по [официальной документации](https://github.com/michaelfeil/infinity),
загрузить **ту же закреплённую ревизию** BAAI/bge-m3. Сервис должен предоставлять
`GET /v1/models` и `POST /v1/embeddings`. Его точное served-model ID указать в конфигурации.
Модель/ревизия сервера - обязанность конфигурации развёртывания: одного `/models` недостаточно,
чтобы доказать совпадение весов с локальным tokenizer manifest.

Для Linux/macOS:

```bash
export BEAR_MODEL_DIR=models/bge-m3
export BEAR_INFINITY_URL=http://127.0.0.1:7997/v1
export BEAR_INFINITY_MODEL=BAAI/bge-m3
export BEAR_QDRANT_URL=http://127.0.0.1:6333
export BEAR_QDRANT_COLLECTION=bear_bge_m3_pipeline_v1
```

В PowerShell использовать `$env:BEAR_MODEL_DIR="models/bge-m3"` и аналогично для остальных.
Не выставлять `BEAR_OFFLINE=1` / `BEAR_TEST_COUNTER=1` для реальной индексации.
Для удалённых сервисов заменить адреса. В Colab `localhost` относится к машине Colab,
а не к домашнему компьютеру. API-ключи: `BEAR_INFINITY_API_KEY` / `BEAR_QDRANT_API_KEY`.

Пройти существующий путь обработки:

```bash
bear --model-dir models/bge-m3 process examples/ssl.txt --document ssl-guide --mode token --output state/ssl.json
bear --model-dir models/bge-m3 index state/ssl.json
bear --model-dir models/bge-m3 search "Как настроить SSL?" --top-k 50
```

Встроенный TXT/HTML/DOCX-контур предыдущего блока по умолчанию требует настроенный Dedoc;
его запуск описан в `bear-text-beta/README.md`. Демо выше использует реальный локальный TXTParser.

После запуска сервисов можно выполнить отдельный smoke-test:

```bash
python examples/smoke_external.py --model-dir models/bge-m3
```

Он создаёт небольшой документ в отдельном тестовом пространстве/коллекции. Качество на RuBQ
этот smoke-test не измеряет. Модели и внешние сервисы не были запущены при локальной проверке пакета.

## Использование класса

```python
from pathlib import Path
from bear_text_beta.embedding_pipeline import EmbeddingPipeline, MemoryVectorCache
from bear_text_beta.embeddings import HFTokenCounter, InfinityEmbeddingProvider, load_profile

profile = load_profile(Path("models/bge-m3"))
counter = HFTokenCounter(Path("models/bge-m3"), profile)
provider = InfinityEmbeddingProvider(
    "http://127.0.0.1:7997/v1", profile, counter,
    server_model="BAAI/bge-m3", max_tokens=480,
)
with EmbeddingPipeline(provider, counter, profile, max_tokens=480,
                       cache=MemoryVectorCache(4096)) as pipeline:
    prepared = pipeline.vectorize_query("  Как\n настроить SSL? ")
    print(prepared.query.original, prepared.query.text)
    print(len(prepared.vector), prepared.embedding_profile_id)
    # result = ProcessingResult от парсера/чанкера того же профиля
    # embedded_chunks = pipeline.vectorize_chunks(result)
```

В `Services` класс уже подключён автоматически для реального инференса; отдельная подмена
`IndexingService` не требуется. Его метод `search()` теперь строит запрос через пайплайн.
`embed(text)` совместим со схемой презентации, `embed_batch(texts, purpose)` - с кодом предыдущего блока.
Для FastAPI есть `await pipeline.aembed(text)`: sync HTTP выносится в поток; вызовы одного экземпляра
сериализуются. Для высокой нагрузки нужен отдельный пул/асинхронный провайдер.

`PreparedQuery` содержит original/normalized/text/token_count/builder_version.
Текст в общие логи выводится только с `log_query_text=True`; trace доступен вызывающему коду всегда.
`on_event` получает счётчики и время векторизации без содержимого запросов.
Это время **не** включает поиск Qdrant или реранкер.
Ошибка пользовательского `on_event` передаётся вызывающему коду: обработчик должен быть надёжным.

Кэш опциональный, ограниченный, в памяти процесса: после перезапуска пуст.
Ключ включает профиль/ревизии/префиксы, назначение (`query`/`document`/`similarity`),
лимит и точный подготовленный текст. Совпадающие строки внутри батча вычисляются один раз.
Можно реализовать `VectorCache` для Redis, не меняя класс.

## Модели и качество

Шаблон BGE-M3: 1024 dense-компоненты, без `query:`/`passage:` префиксов.
512 токенов - выбранный рабочий предел профиля, 480 - бюджет текущего рантайма.
Предел самой BGE-M3 - 8192; увеличение бюджета требует согласования чанкинга и профиля.
Прежний E5-small (384, `query:`/`passage:`) сохранён для совместимости.
Менять модель для запроса без переиндексации корпуса нельзя.

По предыдущему тесту RuBQ предварительно выбрана связка BGE-M3 + BGE-reranker-v2-m3.
Реранкинг находится после retrieval и в текущую задачу класса не включён.
Новый модуль сам по себе не доказывает улучшение nDCG. Новый RuBQ-прогон здесь не выполнялся.

Метрики для передачи следующему блоку:

```python
from bear_text_beta.retrieval_metrics import evaluate_rankings
report = evaluate_rankings(
    rankings={"q1": ["chunk-a", "chunk-b"]},
    qrels={"q1": {"chunk-b": 1}},
    latencies_ms={"q1": 15.2},
)
```

Считаются nDCG@10, MRR@10, Recall@50, p50/p95. Передавать ранжирование всех кандидатов до 50,
даже если показываются только первые 10. ID в qrels и выдаче должны относиться к одному уровню:
чанк либо документ. Нельзя сравнивать старые RuBQ paragraph-ID с новыми chunk-ID без remapping.

Документация:

- [Контракты и архитектура](docs/embedding/architecture.md)
- [Разбор рекомендаций DeepSeek](docs/embedding/deepseek_review.md)
- [Слияние, GitHub и GitLab](docs/embedding/merge_plan.md)
- [Результаты проверки](docs/embedding/validation.md)
