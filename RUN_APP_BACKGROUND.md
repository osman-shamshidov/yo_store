# Запуск app.py в фоновом режиме на сервере

## ⚠️ Важно для REG.RU хостинга

**Для REG.RU с Passenger НЕ нужно запускать `app.py` вручную!**

Passenger автоматически управляет процессом через `passenger_wsgi.py`. Если вы запускаете `app.py` вручную, это может:
- Конфликтовать с Passenger
- Создавать дублирующие процессы
- Использовать лишние ресурсы

## Если все же нужно запустить для тестирования

### Вариант 1: Использование nohup (простой способ)

```bash
cd /var/www/u3324585/data
source venv/bin/activate
nohup python3 app.py > app.log 2>&1 &
echo $! > app.pid
```

**Проверка:**
```bash
# Проверить, что процесс запущен
ps aux | grep app.py

# Посмотреть логи
tail -f app.log

# Остановить процесс
kill $(cat app.pid)
```

### Вариант 2: Использование screen (рекомендуется для тестирования)

```bash
# Установить screen (если нет)
# На REG.RU обычно уже установлен

# Создать новую сессию screen
screen -S yo-store

# В сессии screen:
cd /var/www/u3324585/data
source venv/bin/activate
python3 app.py

# Отключиться от screen (процесс продолжит работать)
# Нажмите: Ctrl+A, затем D

# Вернуться к сессии
screen -r yo-store

# Завершить сессию
screen -X -S yo-store quit
```

### Вариант 3: Использование tmux

```bash
# Создать новую сессию tmux
tmux new -s yo-store

# В сессии tmux:
cd /var/www/u3324585/data
source venv/bin/activate
python3 app.py

# Отключиться от tmux (процесс продолжит работать)
# Нажмите: Ctrl+B, затем D

# Вернуться к сессии
tmux attach -t yo-store

# Завершить сессию
tmux kill-session -t yo-store
```

### Вариант 4: Использование готовых скриптов

```bash
# Сделать скрипты исполняемыми
chmod +x start_app_background.sh
chmod +x stop_app.sh

# Запустить
./start_app_background.sh

# Остановить
./stop_app.sh
```

## Проверка работы

```bash
# Проверить, что процесс запущен
ps aux | grep "python3 app.py"

# Проверить, что приложение отвечает
curl http://localhost:8000/health

# Посмотреть логи
tail -f app.log
```

## Остановка процесса

```bash
# Найти PID процесса
ps aux | grep "python3 app.py"

# Остановить по PID
kill <PID>

# Или использовать скрипт
./stop_app.sh
```

## Почему процесс может падать?

1. **Ошибки в коде** - проверьте логи: `tail -f app.log`
2. **Проблемы с базой данных** - проверьте подключение к БД
3. **Нехватка памяти** - проверьте: `free -h`
4. **Порт занят** - проверьте: `netstat -tulpn | grep 8000`
5. **Отсутствие зависимостей** - проверьте: `pip list`

## Рекомендация

Для продакшена на REG.RU используйте **только Passenger** - он автоматически:
- Запускает приложение при старте сервера
- Перезапускает при сбоях
- Управляет процессами
- Логирует ошибки

Не запускайте `app.py` вручную, если используете Passenger!

