# 🚀 Быстрое развертывание Yo Store на Railway

## 🎯 Что у нас есть

✅ **Полностью готовое приложение Yo Store** с:
- Telegram Bot с интерактивными кнопками
- Веб-интерфейс с логотипом
- API для работы с товарами
- Автоматическое обновление цен каждые 10 минут
- База данных с тестовыми товарами
- Готовность к развертыванию

## 🚀 Развертывание на Railway

### Шаг 1: Подготовка кода
```bash
# Код уже готов в папке yo_mini_app
cd /Users/msk-hq-nb-1823/Documents/yo_mini_app

# Запустить скрипт развертывания
./deploy.sh
```

### Шаг 2: Создание GitHub репозитория
1. Перейдите на [github.com/new](https://github.com/new)
2. Название: `yo-store`
3. Сделайте **публичным**
4. Нажмите "Create repository"

### Шаг 3: Загрузка кода на GitHub
```bash
git remote add origin https://github.com/YOUR_USERNAME/yo-store.git
git push -u origin main
```
(Замените `YOUR_USERNAME` на ваш GitHub username)

### Шаг 4: Развертывание на Railway
1. Перейдите на [railway.app](https://railway.app)
2. Войдите через GitHub
3. Нажмите "New Project"
4. Выберите "Deploy from GitHub repo"
5. Выберите репозиторий `yo-store`
6. Railway автоматически определит Python и установит зависимости

### Шаг 5: Настройка переменных окружения
В Railway Dashboard → Variables добавьте:
```
TELEGRAM_BOT_TOKEN=ваш_токен_от_botfather
SECRET_KEY=ваш_секретный_ключ_минимум_32_символа
DEBUG=False
HOST=0.0.0.0
PORT=$PORT
```

### Шаг 6: Добавление базы данных
1. В Railway нажмите "New" → "Database" → "PostgreSQL"
2. Railway автоматически создаст переменную `DATABASE_URL`

### Шаг 7: Получение URL
После развертывания Railway даст вам URL вида:
```
https://your-app-name.railway.app
```

## 🤖 Настройка Telegram Bot

### Создание бота
1. Найдите [@BotFather](https://t.me/botfather) в Telegram
2. Отправьте `/newbot`
3. Название: `Yo Store Bot`
4. Username: `yo_store_bot` (или любой доступный)
5. Скопируйте токен

### Настройка Mini App
1. В чате с @BotFather отправьте `/newapp`
2. Выберите вашего бота
3. Настройте Mini App:
   - **Название:** Yo Store
   - **Описание:** Магазин электроники с автоматическим обновлением цен
   - **Фото:** Загрузите логотип из `static/images/logo.jpg`
   - **Web App URL:** `https://your-app-name.railway.app/webapp`

## 🧪 Локальное тестирование (опционально)

Если хотите протестировать локально:
```bash
# Запустить Docker Compose
./docker-test.sh

# Или вручную
docker-compose up --build
```

Доступные URL:
- **Web App:** http://localhost:8000/webapp
- **API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

## 📱 Использование в Telegram

1. Найдите вашего бота в Telegram
2. Отправьте `/start`
3. Нажмите кнопку "🛍️ Открыть магазин"
4. Mini app откроется в Telegram!

## 🎉 Результат

После настройки у вас будет:
- **Telegram Bot** с командами и кнопками
- **Mini App** в Telegram с полным интерфейсом магазина
- **Автоматическое обновление цен** каждые 10 минут
- **База данных** с товарами электроники
- **API** для интеграции с другими сервисами

## 🔧 Возможные проблемы

### Docker не запускается
```bash
# Запустить Docker Desktop
open -a Docker

# Подождать 30 секунд и повторить
docker --version
```

### Ошибка сборки на Railway
- Проверьте, что все файлы загружены в GitHub
- Убедитесь, что Dockerfile находится в корне репозитория
- Проверьте логи в Railway Dashboard

### Telegram Bot не работает
- Проверьте токен в переменных окружения
- Убедитесь, что URL правильный
- Проверьте логи в Railway Dashboard

## 📞 Поддержка

При проблемах:
1. Проверьте логи в Railway Dashboard
2. Убедитесь, что все переменные окружения настроены
3. Проверьте, что база данных подключена
4. Убедитесь, что Dockerfile корректен

## 🎯 Готово!

Ваш Yo Store будет доступен по URL:
`https://your-app-name.railway.app/webapp`

И в Telegram как полноценный mini app! 🚀
