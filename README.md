# Система пошуку медіа-джерел

Система для пошуку та агрегації медіа-джерел з використанням різних пошукових систем та RSS-стрічок.

## Функціональність

- Пошук медіа-джерел через Google News та DuckDuckGo
- Аналіз веб-сайтів на наявність новинного контенту
- Збереження знайдених джерел у MongoDB
- Експорт даних у CSV формат
- Веб-інтерфейс для керування джерелами

## Технології

### Backend
- FastAPI
- MongoDB (motor)
- Selenium (undetected-chromedriver)
- newspaper3k
- DuckDuckGo Search API

### Frontend
- React
- TypeScript
- Material-UI

## Встановлення

1. Клонуйте репозиторій:
```bash
git clone [URL репозиторію]
cd sm_parse
```

2. Встановіть залежності для backend:
```bash
pip install -r requirements.txt
```

3. Встановіть залежності для frontend:
```bash
cd frontend
npm install
```

4. Запустіть MongoDB

5. Запустіть backend:
```bash
python app.py
```

6. Запустіть frontend:
```bash
cd frontend
npm start
```

## Структура проекту

```
sm_parse/
├── backend/
│   ├── api/
│   ├── config/
│   ├── models/
│   └── services/
├── frontend/
│   ├── src/
│   └── public/
└── requirements.txt
```

## Ліцензія

MIT 