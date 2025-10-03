# 🚀 Развертывание Yo Store на Railway

## 📋 Пошаговая инструкция

### 1. Подготовка проекта

Убедитесь, что у вас есть все файлы:
- `main.py` - главный файл приложения
- `requirements.txt` - зависимости
- `railway.json` - конфигурация Railway
- `Procfile` - команда запуска
- `runtime.txt` - версия Python

### 2. Создание аккаунта Railway

1. Перейдите на [railway.app](https://railway.app)
2. Нажмите "Login" и войдите через GitHub
3. Подтвердите авторизацию

### 3. Развертывание проекта

#### Вариант A: Через GitHub (Рекомендуется)

1. **Загрузите код на GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/yo-store.git
   git push -u origin main
   ```

2. **В Railway:**
   - Нажмите "New Project"
   - Выберите "Deploy from GitHub repo"
   - Выберите ваш репозиторий `yo-store`
   - Railway автоматически определит Python и установит зависимости

#### Вариант B: Прямая загрузка

1. **В Railway:**
   - Нажмите "New Project"
   - Выберите "Deploy from folder"
   - Загрузите папку с проектом

### 4. Настройка переменных окружения

В Railway Dashboard:

1. Перейдите в ваш проект
2. Откройте вкладку "Variables"
3. Добавьте переменные:

```
TELEGRAM_BOT_TOKEN=ваш_токен_от_botfather
SECRET_KEY=ваш_секретный_ключ
DEBUG=False
HOST=0.0.0.0
PORT=$PORT
```

### 5. Настройка базы данных

Railway автоматически предоставит PostgreSQL:

1. В проекте нажмите "New" → "Database" → "PostgreSQL"
2. Railway создаст переменную `DATABASE_URL`
3. Она автоматически подключится к вашему приложению

### 6. Получение URL

После развертывания Railway предоставит URL вида:
```
https://your-app-name.railway.app
```

### 7. Настройка Telegram Bot

1. Найдите [@BotFather](https://t.me/botfather) в Telegram
2. Отправьте команду `/newapp`
3. Выберите вашего бота
4. Настройте Mini App:
   - **Название:** Yo Store
   - **Описание:** Магазин электроники
   - **Фото:** Загрузите логотип
   - **Web App URL:** `https://your-app-name.railway.app/webapp`

### 8. Настройка Webhook (опционально)

Для продакшена настройте webhook:

1. В Railway добавьте переменную:
   ```
   TELEGRAM_WEBHOOK_URL=https://your-app-name.railway.app/webhook
   ```

2. В коде бота добавьте webhook endpoint

## 🔧 Альтернативные платформы

### Render.com

1. Подключите GitHub репозиторий
2. Выберите "Web Service"
3. Настройки:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python main.py`
   - **Environment:** Python 3

### Heroku

1. Установите Heroku CLI
2. Создайте приложение:
   ```bash
   heroku create yo-store-app
   ```
3. Загрузите код:
   ```bash
   git push heroku main
   ```

## 📱 Тестирование

После развертывания проверьте:

1. **API:** `https://your-app-name.railway.app/health`
2. **Web App:** `https://your-app-name.railway.app/webapp`
3. **API Docs:** `https://your-app-name.railway.app/docs`

## 🚨 Возможные проблемы

### Ошибка "Module not found"
- Проверьте `requirements.txt`
- Убедитесь, что все зависимости указаны

### Ошибка базы данных
- Проверьте переменную `DATABASE_URL`
- Убедитесь, что PostgreSQL добавлен в проект

### Telegram Bot не работает
- Проверьте `TELEGRAM_BOT_TOKEN`
- Убедитесь, что токен правильный

## 📞 Поддержка

При проблемах:
1. Проверьте логи в Railway Dashboard
2. Убедитесь, что все переменные окружения настроены
3. Проверьте, что порт указан как `$PORT`

## 🎉 Готово!

После настройки ваш Yo Store будет доступен по URL:
`https://your-app-name.railway.app/webapp`

И вы сможете использовать его в Telegram Mini App!
