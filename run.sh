#!/bin/bash

# Перевірка наявності Python та Node.js
command -v python3 >/dev/null 2>&1 || { echo "Python 3 не встановлено" >&2; exit 1; }
command -v node >/dev/null 2>&1 || { echo "Node.js не встановлено" >&2; exit 1; }

# Створення та активація віртуального середовища
echo "Створення віртуального середовища..."
python3 -m venv venv
source venv/bin/activate

# Встановлення залежностей Python
echo "Встановлення залежностей Python..."
pip install -r requirements.txt

# Встановлення залежностей Node.js
echo "Встановлення залежностей Node.js..."
cd frontend
npm install

# Запуск бекенду
echo "Запуск бекенду..."
cd ..
python app.py &
BACKEND_PID=$!

# Запуск фронтенду
echo "Запуск фронтенду..."
cd frontend
npm start &
FRONTEND_PID=$!

# Функція для коректного завершення процесів
cleanup() {
    echo "Завершення роботи..."
    kill $BACKEND_PID
    kill $FRONTEND_PID
    exit 0
}

# Перехоплення сигналу завершення
trap cleanup SIGINT SIGTERM

# Очікування завершення
wait 