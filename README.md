# Система онлайн-тестирования

Учебный fullstack-проект для создания, назначения, прохождения и автоматической проверки тестов.

На текущем этапе выполнена инициализация двух частей приложения:

- `backend` — FastAPI-приложение с версионируемым API и health-check;
- `frontend` — React/Vite-приложение с Material UI и React Router;
- `docs` — архитектура и материалы для защиты этапа.

## Быстрый старт backend

Требуется Python 3.12 или 3.13.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

После запуска:

- API: `http://localhost:8000`;
- Swagger UI: `http://localhost:8000/docs`;
- health-check: `http://localhost:8000/api/health`.

## Быстрый старт frontend

Требуется Node.js 20+.

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Интерфейс будет доступен по адресу `http://localhost:5173`.

## Текущий API-контракт

```http
GET /api/health
```

Успешный ответ:

```json
{
  "status": "ok",
  "service": "online-testing-api"
}
```

Подробное описание решений находится в [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), текст выступления — в [docs/STAGE_1_DEFENSE.md](docs/STAGE_1_DEFENSE.md).

