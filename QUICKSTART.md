# 🚀 Быстрый запуск FOK Bot

## Минимальная настройка для тестирования

### 1. Создайте Telegram бота
1. Найдите @BotFather в Telegram
2. Создайте нового бота: `/newbot`
3. Скопируйте токен бота

### 2. Настройте конфигурацию
```bash
# Скопируйте пример конфигурации
cp .env.example .env

# Отредактируйте файл .env
nano .env
```

**Обязательно укажите:**
```env
BOT_TOKEN=your_bot_token_here
SUPER_ADMIN_IDS=your_telegram_id_here
```

### 3. Запустите приложение
```bash
# Запуск всех сервисов
docker-compose up -d

# Дождитесь запуска (30-60 секунд)
docker-compose logs -f bot
```

### 4. Инициализируйте данные
```bash
# Создайте базовые данные (районы, виды спорта, примеры ФОКов)
docker-compose exec bot python scripts/init_data.py

# Сделайте себя администратором
docker-compose exec bot python scripts/admin_tools.py make_admin YOUR_TELEGRAM_ID super
```

### 5. Протестируйте бота
1. Найдите вашего бота в Telegram
2. Отправьте `/start`
3. Пройдите регистрацию
4. Проверьте функционал

## 🔧 Основные команды

### Управление сервисами
```bash
# Статус сервисов
docker-compose ps

# Логи
docker-compose logs -f

# Перезапуск
docker-compose restart

# Остановка
docker-compose down
```

### Администрирование
```bash
# Статистика бота
docker-compose exec bot python scripts/admin_tools.py stats

# Список пользователей
docker-compose exec bot python scripts/admin_tools.py list_users

# Информация о пользователе
docker-compose exec bot python scripts/admin_tools.py user_info TELEGRAM_ID
```

### Мониторинг
```bash
# Полная информация о системе
./scripts/monitor.sh full

# Только статус
./scripts/monitor.sh status

# Ошибки
./scripts/monitor.sh errors
```

## 🐛 Решение проблем

### Бот не отвечает
```bash
# Проверьте токен в .env файле
cat .env | grep BOT_TOKEN

# Проверьте логи
docker-compose logs bot

# Перезапустите бота
docker-compose restart bot
```

### Проблемы с базой данных
```bash
# Проверьте статус MongoDB
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"

# Перезапустите базу
docker-compose restart mongodb
```

### Очистка и переустановка
```bash
# Остановить и удалить все
docker-compose down -v

# Удалить образы
docker-compose down --rmi all

# Запустить заново
docker-compose up -d --build
```

## 📱 Тестирование функций

### Пользовательские функции:
1. **Регистрация**: `/start` → введите имя → поделитесь телефоном
2. **Каталог**: Главное меню → "Каталог ФОКов"
3. **Поиск**: Главное меню → "Поиск по видам спорта"
4. **Заявка**: Выберите ФОК → "Оставить заявку"
5. **Мои заявки**: Главное меню → "Мои заявки"

### Админские функции:
1. **Админ-панель**: Отправьте `/admin` или используйте кнопку в меню
2. **Управление заявками**: Админ-панель → "Управление заявками"
3. **Статистика**: Админ-панель → "Статистика"
4. **Управление ФОКами**: Админ-панель → "Управление ФОКами"

## 🌐 Production развертывание

Для продакшен среды используйте:
```bash
# Скопируйте production конфигурацию
cp .env.prod.example .env.prod

# Настройте production параметры
nano .env.prod

# Запустите production версию
./scripts/deploy.sh
```

## 📞 Поддержка

Если возникли проблемы:
1. Проверьте логи: `docker-compose logs -f`
2. Посмотрите статус: `./scripts/monitor.sh status`
3. Изучите документацию в `README.md`

---
**Готово! Ваш FOK Bot запущен и готов к работе! 🎉**