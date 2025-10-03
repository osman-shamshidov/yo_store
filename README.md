# 🛍️ Yo Store Telegram Mini App

Telegram mini app для магазина электроники с автоматическим обновлением цен каждые 10 минут.

## 🚀 Возможности

- 📱 **Telegram Bot** - интерактивный бот с кнопками и командами
- 🛍️ **Mini App** - полноценное веб-приложение в Telegram
- 💰 **Автообновление цен** - цены обновляются каждые 10 минут
- 📊 **API** - RESTful API для работы с товарами
- 🗄️ **База данных** - SQLite/PostgreSQL для хранения данных
- 🔍 **Поиск** - поиск товаров по названию, бренду, модели

## 📦 Категории товаров

- 📱 Смартфоны
- 💻 Ноутбуки
- 🎮 Игровые приставки
- 🎧 Наушники
- 📱 Планшеты
- 🔊 Умные колонки

## 🛠️ Установка и запуск

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка окружения

Создайте файл `.env` на основе `.env.example`:

```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_WEBHOOK_URL=https://yourdomain.com/webhook

# Database Configuration
DATABASE_URL=sqlite:///./yo_store.db

# App Configuration
SECRET_KEY=your_secret_key_here
DEBUG=True
HOST=0.0.0.0
PORT=8000
```

### 3. Получение Telegram Bot Token

1. Найдите [@BotFather](https://t.me/botfather) в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Скопируйте полученный токен в `.env` файл

### 4. Запуск приложения

```bash
python main.py
```

## 📱 Использование

### Telegram Bot команды

- `/start` - Главное меню
- `/help` - Справка
- `/categories` - Показать все категории
- `/search <запрос>` - Поиск товаров

### Веб-интерфейс

Откройте в браузере: `http://localhost:8000/webapp`

### API Endpoints

- `GET /categories` - Получить все категории
- `GET /products` - Получить товары (с фильтрами)
- `GET /products/{id}` - Получить товар по ID
- `GET /search` - Поиск товаров
- `GET /health` - Проверка состояния

## 🔧 Настройка обновления цен

### Автоматическое обновление

Цены автоматически обновляются каждые 10 минут с случайными изменениями от -5% до +5%.

### Обновление из файла

Для обновления цен из внешнего файла используйте формат JSON:

```json
[
    {
        "product_id": 1,
        "price": 94990.0,
        "comment": "iPhone 15 Pro - снижение цены"
    }
]
```

Затем вызовите метод `load_prices_from_file()` в `price_updater.py`.

## 🗄️ База данных

### SQLite (по умолчанию)

База данных создается автоматически в файле `yo_store.db`.

### PostgreSQL

Для использования PostgreSQL измените `DATABASE_URL` в `.env`:

```
DATABASE_URL=postgresql://username:password@localhost:5432/yo_store
```

## 📁 Структура проекта

```
yo_mini_app/
├── main.py              # Главный файл приложения
├── api.py               # FastAPI приложение
├── telegram_bot.py      # Telegram бот
├── models.py            # Модели базы данных
├── database.py          # Настройка базы данных
├── price_updater.py     # Система обновления цен
├── config.py            # Конфигурация
├── webapp.html          # Веб-интерфейс
├── sample_prices.json   # Пример файла с ценами
├── requirements.txt     # Зависимости
└── README.md           # Документация
```

## 🚀 Развертывание

### Локальная разработка

```bash
python main.py
```

### Docker (опционально)

Создайте `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "main.py"]
```

### Облачное развертывание

Рекомендуемые платформы:
- **Heroku** - простое развертывание
- **Railway** - хорошая поддержка Python
- **DigitalOcean** - VPS с полным контролем
- **AWS/GCP** - масштабируемые решения

## 🔒 Безопасность

- Используйте HTTPS для продакшена
- Настройте webhook для Telegram бота
- Ограничьте доступ к API
- Регулярно обновляйте зависимости

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи приложения
2. Убедитесь, что все зависимости установлены
3. Проверьте настройки в `.env` файле
4. Убедитесь, что порт 8000 свободен

## 🎯 Дальнейшее развитие

Возможные улучшения:
- Система заказов
- Интеграция с платежными системами
- Админ-панель
- Система уведомлений
- Аналитика продаж
- Многоязычность

