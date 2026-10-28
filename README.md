# Система онлайн-тестирования с защищённым клиентом

Django-сервер для тестов + Electron-клиент в режиме киоска для прохождения экзаменов на Linux
(замена Safe Exam Browser, у которого нет Linux-клиента). План работ — в `EXAM_SECURITY_INTEGRATION.md`.

## Структура

```
Proekt_PP/
├── backend/            Django-проект
│   ├── config/         настройки, urls
│   ├── accounts/       пользователи и роли (ADMIN / TEACHER / STUDENT)
│   ├── testing/        тесты, вопросы, варианты ответов
│   ├── attempts/       попытки прохождения, ответы, журнал событий
│   ├── study_groups/   учебные группы
│   ├── analytics/      статистика (не `statistics` — конфликт со стандартной библиотекой)
│   ├── api/            REST API
│   ├── templates/  static/  media/
│   └── requirements.txt
├── electron-app/       клиент-киоск
│   ├── main.js         окно в kiosk mode, блок навигации и новых окон
│   ├── preload.js
│   └── config.json     адрес сервера
└── venv/               виртуальное окружение Python (не в git)
```

## Требования

- Python 3.12+
- Node.js 20+

## Запуск сервера

```bash
python3.12 -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt

cd backend
cp .env.example .env                # по желанию
python manage.py migrate
python manage.py seed_data          # демо-данные (или createsuperuser)
python manage.py runserver
```

Открыть http://127.0.0.1:8000/ — админка `/admin/`, API `/api/`.

### Демо-аккаунты (только для учебного режима)

| Логин | Пароль | Роль |
|---|---|---|
| admin | admin12345 | администратор |
| teacher | teacher12345 | преподаватель |
| student, petrov, sidorov | student12345 | студенты группы ПИ-21 |

Тест «Компьютерные сети (экзамен)» открывается только из клиента-киоска.

### API прохождения теста (для студента)

```
GET  /api/tests/                     доступные тесты
POST /api/tests/<id>/start/          начать или продолжить попытку
GET  /api/attempts/<id>/             вопросы (без правильных ответов) и сохранённые ответы
POST /api/attempts/<id>/answer/      {"question": 5, "options": [17]}
POST /api/attempts/<id>/finish/      завершить и получить результат
POST /api/attempts/<id>/events/      {"event_type": "FOCUS_LOST"}
GET  /api/attempts/<id>/time-left/   оставшееся время по часам сервера
```

Просроченные попытки закрываются при любом обращении к ним, а также командой
`python manage.py expire_attempts` (на сервере — по cron раз в минуту).

### Тесты

```bash
python manage.py test
```

Для PostgreSQL: `pip install "psycopg[binary]"` и заполнить переменные `POSTGRES_*` в `backend/.env`.

## Запуск клиента

```bash
cd electron-app
npm install
npm run dev     # обычное окно с DevTools — для разработки
npm start       # режим киоска (полноэкранный, без выхода через меню)
```

Адрес сервера и ключ клиента задаются в `electron-app/config.json` или переменными `EXAM_URL` и `EXAM_CLIENT_KEY`.
Ключ должен совпадать с `EXAM_CLIENT_KEY` сервера (`backend/.env`):

```bash
EXAM_URL=https://exam.example.ru/ EXAM_CLIENT_KEY=... npm start
```

Выйти из режима киоска при разработке: Cmd+Q (macOS) / Alt+F4 (Linux). Блокировка этих
комбинаций и системных клавиш — фаза 3.
