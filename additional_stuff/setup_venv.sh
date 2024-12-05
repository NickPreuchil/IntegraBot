#!/bin/bash

# Проверяем существование виртуального окружения
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Активируем виртуальное окружение и устанавливаем зависимости
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
