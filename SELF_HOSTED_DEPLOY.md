# 🖥️ Развертывание Yo Store на собственном сервере

## 📋 Требования

- Сервер с Linux (Ubuntu/Debian рекомендуется)
- Python 3.9 или выше
- Nginx (для проксирования)
- Домен (опционально, но рекомендуется)
- SSL сертификат (Let's Encrypt бесплатный)

## 🚀 Пошаговая инструкция

### 1. Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Python и pip
sudo apt install python3 python3-pip python3-venv -y

# Установка Nginx
sudo apt install nginx -y

# Установка Git (если еще не установлен)
sudo apt install git -y
```

### 2. Клонирование проекта

```bash
# Создайте директорию для приложения
sudo mkdir -p /var/www/yo-store
sudo chown $USER:$USER /var/www/yo-store

# Клонируйте репозиторий
cd /var/www/yo-store
git clone https://github.com/osman-shamshidov/yo_store.git .

# Или загрузите файлы через SCP/SFTP
```

### 3. Создание виртуального окружения

```bash
cd /var/www/yo-store

# Создайте виртуальное окружение
python3 -m venv venv

# Активируйте его
source venv/bin/activate

# Установите зависимости
pip install -r requirements.txt
```

### 4. Настройка переменных окружения

```bash
# Создайте файл .env
nano .env
```

Добавьте в файл `.env`:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=ваш_токен_от_botfather
TELEGRAM_WEBHOOK_URL=https://ваш-домен.com/webhook

# Database Configuration
DATABASE_URL=sqlite:///./electronics_store.db

# App Configuration
SECRET_KEY=сгенерируйте_случайный_ключ_здесь
DEBUG=False
HOST=127.0.0.1
PORT=8000
```

**Важно:** Сгенерируйте безопасный SECRET_KEY:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 5. Инициализация базы данных

```bash
# Активируйте виртуальное окружение
source venv/bin/activate

# Инициализируйте базу данных
python3 -c "from database import init_database; init_database()"

# Создайте каталог товаров (опционально)
python3 init_db_for_production.py
```

### 6. Создание systemd сервиса

```bash
sudo nano /etc/systemd/system/yo-store.service
```

Добавьте следующее содержимое:

```ini
[Unit]
Description=Yo Store Mini App
After=network.target

[Service]
Type=simple
User=ваш_пользователь
WorkingDirectory=/var/www/yo-store
Environment="PATH=/var/www/yo-store/venv/bin"
ExecStart=/var/www/yo-store/venv/bin/python3 app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Важно:** Замените `ваш_пользователь` на ваше имя пользователя (например, `ubuntu` или `www-data`)

```bash
# Перезагрузите systemd
sudo systemctl daemon-reload

# Включите автозапуск
sudo systemctl enable yo-store

# Запустите сервис
sudo systemctl start yo-store

# Проверьте статус
sudo systemctl status yo-store
```

### 7. Настройка Nginx

```bash
sudo nano /etc/nginx/sites-available/yo-store
```

Добавьте следующую конфигурацию:

```nginx
server {
    listen 80;
    server_name ваш-домен.com www.ваш-домен.com;

    # Если используете IP вместо домена
    # server_name _;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Статические файлы
    location /static {
        alias /var/www/yo-store/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

```bash
# Создайте символическую ссылку
sudo ln -s /etc/nginx/sites-available/yo-store /etc/nginx/sites-enabled/

# Удалите дефолтную конфигурацию (опционально)
sudo rm /etc/nginx/sites-enabled/default

# Проверьте конфигурацию Nginx
sudo nginx -t

# Перезапустите Nginx
sudo systemctl restart nginx
```

### 8. Настройка SSL (Let's Encrypt)

```bash
# Установите Certbot
sudo apt install certbot python3-certbot-nginx -y

# Получите SSL сертификат
sudo certbot --nginx -d ваш-домен.com -d www.ваш-домен.com

# Certbot автоматически обновит конфигурацию Nginx
# И настроит автоматическое обновление сертификата
```

### 9. Настройка файрвола

```bash
# Разрешите HTTP и HTTPS
sudo ufw allow 'Nginx Full'

# Или отдельно
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Включите файрвол (если еще не включен)
sudo ufw enable
```

### 10. Проверка работы

1. **Проверьте API:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Проверьте веб-приложение:**
   Откройте в браузере: `http://ваш-домен.com/webapp` или `http://ваш-IP/webapp`

3. **Проверьте логи:**
   ```bash
   # Логи приложения
   sudo journalctl -u yo-store -f

   # Логи Nginx
   sudo tail -f /var/log/nginx/error.log
   ```

## 🔧 Полезные команды

### Управление сервисом

```bash
# Запуск
sudo systemctl start yo-store

# Остановка
sudo systemctl stop yo-store

# Перезапуск
sudo systemctl restart yo-store

# Статус
sudo systemctl status yo-store

# Логи
sudo journalctl -u yo-store -f
```

### Обновление приложения

```bash
cd /var/www/yo-store

# Получите последние изменения
git pull origin main

# Активируйте виртуальное окружение
source venv/bin/activate

# Обновите зависимости (если нужно)
pip install -r requirements.txt

# Перезапустите сервис
sudo systemctl restart yo-store
```

### Резервное копирование базы данных

```bash
# Создайте скрипт для бэкапа
nano /var/www/yo-store/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/yo-store"
mkdir -p $BACKUP_DIR
cp /var/www/yo-store/electronics_store.db $BACKUP_DIR/electronics_store_$(date +%Y%m%d_%H%M%S).db
# Удалите старые бэкапы (старше 7 дней)
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
```

```bash
# Сделайте скрипт исполняемым
chmod +x /var/www/yo-store/backup.sh

# Добавьте в cron для ежедневного бэкапа
crontab -e
# Добавьте строку:
0 2 * * * /var/www/yo-store/backup.sh
```

## 🔒 Безопасность

1. **Измените права доступа к .env:**
   ```bash
   chmod 600 .env
   ```

2. **Используйте сильный SECRET_KEY**

3. **Настройте регулярные обновления:**
   ```bash
   sudo apt install unattended-upgrades
   ```

4. **Ограничьте доступ к SSH:**
   - Используйте ключи вместо паролей
   - Измените стандартный порт SSH

## 📱 Настройка Telegram Mini App

1. Найдите [@BotFather](https://t.me/botfather) в Telegram
2. Отправьте команду `/newapp`
3. Выберите вашего бота
4. Настройте Mini App:
   - **Название:** Yo Store
   - **Описание:** Магазин электроники
   - **Фото:** Загрузите логотип
   - **Web App URL:** `https://ваш-домен.com/webapp`

## 🚨 Решение проблем

### Приложение не запускается

```bash
# Проверьте логи
sudo journalctl -u yo-store -n 50

# Проверьте, что порт свободен
sudo netstat -tulpn | grep 8000

# Проверьте права доступа
ls -la /var/www/yo-store
```

### Nginx возвращает 502 Bad Gateway

1. Проверьте, что приложение запущено:
   ```bash
   sudo systemctl status yo-store
   ```

2. Проверьте, что порт правильный в конфигурации Nginx

3. Проверьте логи Nginx:
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

### База данных не работает

```bash
# Проверьте права доступа к файлу БД
ls -la electronics_store.db

# Пересоздайте БД (осторожно - удалит данные!)
python3 -c "from database import init_database; init_database()"
```

## 📞 Поддержка

При проблемах:
1. Проверьте логи: `sudo journalctl -u yo-store -f`
2. Проверьте конфигурацию Nginx: `sudo nginx -t`
3. Убедитесь, что все переменные окружения настроены
4. Проверьте файрвол: `sudo ufw status`

## 🎉 Готово!

После настройки ваш Yo Store будет доступен по адресу:
- **HTTP:** `http://ваш-домен.com/webapp`
- **HTTPS:** `https://ваш-домен.com/webapp` (после настройки SSL)

И вы сможете использовать его в Telegram Mini App!

