# Шедулер обновления цен

Автоматическое обновление цен из внешнего сервиса каждые 30 минут.

## Настройка

### Переменные окружения (опционально)

```bash
# URL сервиса цен (по умолчанию: http://0.0.0.0:8005/api/prices)
export PRICE_SERVICE_URL="http://0.0.0.0:8005/api/prices"

# Токен авторизации (если требуется)
export PRICE_SERVICE_TOKEN="your-token-here"

# URL базы данных (по умолчанию из config.py)
export DATABASE_URL="sqlite:///electronics_store.db"
```

## Запуск

### Вариант 1: Запуск в терминале (для тестирования)

```bash
python3 price_updater_scheduler.py
```

### Вариант 2: Запуск в фоновом режиме

```bash
# Запуск в фоне
nohup python3 price_updater_scheduler.py > price_updater_scheduler.out 2>&1 &

# Проверка процесса
ps aux | grep price_updater_scheduler

# Остановка
pkill -f price_updater_scheduler.py
```

### Вариант 3: Запуск через screen/tmux

```bash
# Создать новую сессию screen
screen -S price_updater

# Запустить шедулер
python3 price_updater_scheduler.py

# Отключиться от сессии: Ctrl+A, затем D
# Подключиться обратно: screen -r price_updater
```

## Логи

- **price_updater_scheduler.log** - логи шедулера
- **price_updater.log** - логи обновления цен

## Поведение при ошибках

- Если сервис недоступен - цены остаются без изменений, ошибка логируется
- Если таймаут - цены остаются без изменений, ошибка логируется
- Если ошибка подключения - цены остаются без изменений, ошибка логируется
- Шедулер продолжает работу и попытается обновить цены в следующем цикле

## Расписание

- Обновление запускается **каждые 30 минут**
- Первое обновление выполняется сразу при запуске шедулера
- Время следующего обновления можно увидеть в логах

## Проверка работы

```bash
# Просмотр логов в реальном времени
tail -f price_updater_scheduler.log

# Просмотр логов обновления цен
tail -f price_updater.log

# Проверка последних обновлений
tail -50 price_updater.log | grep "Обновлена цена"
```

## Остановка

```bash
# Найти процесс
ps aux | grep price_updater_scheduler

# Остановить процесс (Ctrl+C в терминале или)
pkill -f price_updater_scheduler.py
```

