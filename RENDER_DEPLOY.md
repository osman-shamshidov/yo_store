# 🚀 Развертывание Yo Store на Render.com

## 📋 Пошаговая инструкция

### 1. Подготовка проекта

Убедитесь, что у вас есть все файлы:
- `main.py` - главный файл приложения
- `requirements.txt` - зависимости
- `Procfile` - команда запуска
- `runtime.txt` - версия Python

### 2. Создание аккаунта Render

1. Перейдите на [render.com](https://render.com)
2. Нажмите "Get Started for Free"
3. Войдите через GitHub
4. Подтвердите авторизацию

### 3. Развертывание проекта

#### Шаг 1: Создание Web Service
1. В Render Dashboard нажмите "New +"
2. Выберите "Web Service"
3. Подключите GitHub репозиторий `osman-shamshidov/yo_store`

#### Шаг 2: Настройка сборки
- **Name:** yo-store
- **Environment:** Python 3
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python main.py`

#### Шаг 3: Настройка переменных окружения
В разделе "Environment Variables" добавьте:
```
TELEGRAM_BOT_TOKEN=ваш_токен_от_botfather
SECRET_KEY=ваш_секретный_ключ_минимум_32_символа
DEBUG=False
HOST=0.0.0.0
PORT=$PORT
```

### 4. Настройка базы данных

#### Создание PostgreSQL базы
1. В Render Dashboard нажмите "New +"
2. Выберите "PostgreSQL"
3. Название: `yo-store-db`
4. Render автоматически создаст переменную `DATABASE_URL`

#### Подключение к приложению
1. В настройках Web Service
2. Добавьте переменную: `DATABASE_URL` (скопируйте из PostgreSQL сервиса)

### 5. Получение URL

После развертывания Render даст вам URL вида:
```
https://yo-store.onrender.com
```

### 6. Настройка Telegram Bot

1. Найдите [@BotFather](https://t.me/botfather)
2. Отправьте `/newapp`
3. Выберите вашего бота
4. Настройте Mini App:
   - **Название:** Yo Store
   - **Описание:** Магазин электроники
   - **Фото:** Загрузите логотип
   - **Web App URL:** `https://yo-store.onrender.com/webapp`

## 🔧 Альтернативные платформы

### Fly.io
```bash
# Установка CLI
curl -L https://fly.io/install.sh | sh

# Логин
fly auth login

# Создание приложения
fly launch

# Развертывание
fly deploy
```

### PythonAnywhere
1. Создайте аккаунт на [pythonanywhere.com](https://pythonanywhere.com)
2. Загрузите код через Git
3. Настройте WSGI файл
4. Запустите приложение

## 📱 Результат

После развертывания:
- **API:** `https://your-app-name.onrender.com`
- **Web App:** `https://your-app-name.onrender.com/webapp`
- **Mini App в Telegram:** Доступен через бота

## 🚨 Возможные проблемы

### Render не видит репозиторий
- Убедитесь, что репозиторий публичный
- Проверьте права доступа Render к GitHub

### Ошибка сборки
- Проверьте `requirements.txt`
- Убедитесь, что все зависимости указаны

### Ошибка базы данных
- Проверьте переменную `DATABASE_URL`
- Убедитесь, что PostgreSQL создан

## 🎉 Готово!

Ваш Yo Store будет доступен на Render.com с автоматическим HTTPS и PostgreSQL базой данных!
