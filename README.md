# Python Document Search

Тестовое задание: простой поисковик по текстам документов.

## Стек

- Python 3.12
- FastAPI
- PostgreSQL + SQLAlchemy 2.0 async
- Elasticsearch 8
- httpx/pytest/pytest-asyncio
- Docker Compose

### Важное замечание про CSV

В предоставленном `posts.csv` 1500 строк и нет поля `id`. Поэтому при импорте используется номер строки, начиная с `1`, как стабильный `id`. В реальном проекте `id` должен приходить из источника данных.

## Запуск через Docker

Положить `posts.csv` в корень проекта и выполнить:

```bash
docker compose up --build -d
```

После запуска API доступен на http://localhost:8000.

Swagger: http://localhost:8000/docs

OpenAPI JSON: http://localhost:8000/openapi.json

## Импорт CSV

После старта контейнеров:

```bash
docker compose exec api python -m app.import_data /data/posts.csv
```

Проверка:

```bash
curl "http://localhost:8000/search?q=конкурс"
```

Удаление:

```bash
curl -X DELETE "http://localhost:8000/documents/1"
```

## Локальный запуск

Нужны PostgreSQL и Elasticsearch 8.x.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## API

### `GET /search?q=...`

Ищет документы по `text` в Elasticsearch. Возвращает максимум 20 документов из PostgreSQL со всеми полями, сортируя их по `created_date DESC`.

Пример ответа:

```json
[
  {
    "id": 10,
    "rubrics": ["VK-123"],
    "text": "пример документа",
    "created_date": "2019-07-25T12:42:13"
  }
]
```

### `DELETE /documents/{id}`

Удаляет документ из PostgreSQL и Elasticsearch.

- `204` — удалено
- `404` — документа нет

## Тесты

```bash
pytest -q
```

Тесты отделены от инфраструктуры и проверяют API health endpoint без поднятия внешних сервисов. Для production-like функциональных тестов можно добавить Testcontainers PostgreSQL + Elasticsearch.

## Архитектура

```text
                 ┌───────────────┐
HTTP ───────────>│    FastAPI    │
                 └───────┬───────┘
                         │
             ┌───────────┴───────────┐
             │                       │
             v                       v
      ┌─────────────┐         ┌──────────────┐
      │ Elasticsearch│         │ PostgreSQL   │
      │ text search  │         │ source data  │
      └─────────────┘         └──────────────┘
```

Сначала Elasticsearch возвращает подходящие `id`, затем PostgreSQL отдаёт полные документы и выполняет требуемую сортировку по дате.

Для простоты демонстрации в Elasticsearch берётся до 1000 совпадений перед сортировкой в БД. В production это лучше заменить на search_after / более точную схему выборки, если индекс большой.
