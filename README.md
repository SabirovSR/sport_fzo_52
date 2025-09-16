# FOK Bot - Каталог ФОКов

Enterprise-grade телеграм-бот для каталога физкультурно-оздоровительных комплексов с полным функционалом управления заявками, админ-панелью и системой отчетности.

## 🚀 Возможности

### Для пользователей:
- 📝 Регистрация с именем и номером телефона
- 🏢 Каталог ФОКов с пагинацией по районам
- 🔍 Поиск по видам спорта
- 📋 Подача заявок в ФОКи
- 📊 Отслеживание статуса заявок
- 📱 Уведомления об изменении статуса

### Для администраторов:
- 👑 Многоуровневая система администрирования
- 🏢 Управление ФОКами (CRUD операции)
- 📋 Управление заявками с изменением статусов
- 👥 Управление пользователями
- 📊 Детальная статистика и аналитика
- 📈 Автоматические еженедельные отчеты в Excel
- 🔍 Поиск заявок и пользователей
- 📁 Управление справочниками (районы, виды спорта)

### Технические возможности:
- 🐳 Полная контейнеризация с Docker
- 📊 MongoDB для хранения данных
- 🚀 Redis для кэширования и очередей
- ⚡ Celery для фоновых задач
- 🔒 Rate limiting и защита от спама
- 📝 Структурированное логирование
- 🔄 Автоматические бэкапы
- 📈 Мониторинг состояния системы

## 🏗️ Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Telegram Bot  │────│     Nginx       │────│   Users/Admins  │
│    (aiogram)    │    │  (Reverse Proxy)│    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Redis       │────│   Application   │────│    MongoDB      │
│   (Cache/Queue) │    │     Logic       │    │   (Database)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐    ┌─────────────────┐
│     Celery      │    │   Monitoring    │
│   (Background   │    │   & Logging     │
│     Tasks)      │    │                 │
└─────────────────┘    └─────────────────┘
```

## 🛠️ Установка и запуск

### Требования
- Docker и Docker Compose
- Минимум 2GB RAM
- 10GB свободного места на диске
- Домен с SSL сертификатом (для production)

### Новые возможности v1.1.0
- ✅ **Автоматическое тестирование** с pytest и aiogram mocks
- ✅ **SSL сертификаты** с автоматическим обновлением через Let's Encrypt
- ✅ **Мониторинг ошибок** с Sentry интеграцией
- ✅ **CI/CD pipeline** с GitHub Actions
- ✅ **Security scanning** и автоматические обновления зависимостей

### Быстрый запуск (Development)

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd fok-bot
```

2. Создайте файл конфигурации:
```bash
cp .env.example .env
```

3. Отредактируйте `.env` файл:
```bash
nano .env
```

Укажите обязательные параметры:
- `BOT_TOKEN` - токен вашего Telegram бота
- `ADMIN_CHAT_ID` - ID чата для админских уведомлений
- `SUPER_ADMIN_IDS` - ID супер-администраторов через запятую

4. Запустите приложение:
```bash
docker-compose up -d
```

5. Инициализируйте данные:
```bash
docker-compose exec bot python scripts/init_data.py
```

6. Создайте админа:
```bash
docker-compose exec bot python scripts/admin_tools.py make_admin YOUR_TELEGRAM_ID super
```

### Production развертывание с SSL

1. Создайте production конфигурацию:
```bash
cp .env.example .env
```

2. Настройте переменные окружения:
```bash
nano .env
```

Обязательные параметры для production:
- `BOT_TOKEN` - токен Telegram бота
- `WEBHOOK_URL` - https://your-domain.com/webhook
- `SSL_DOMAIN` - your-domain.com
- `SSL_EMAIL` - admin@your-domain.com
- `SENTRY_DSN` - для мониторинга ошибок (опционально)

3. Запустите с SSL поддержкой:
```bash
docker-compose -f docker-compose.ssl.yml up -d
```

4. Проверьте SSL сертификат:
```bash
python scripts/ssl_manager.py --domain your-domain.com --email admin@your-domain.com --check
```

### CI/CD настройка

1. **Настройте GitHub Secrets** (см. [.github/SECRETS.md](.github/SECRETS.md)):
   - `BOT_TOKEN` - токен Telegram бота
   - `DOCKER_USERNAME` - Docker Hub username
   - `DOCKER_PASSWORD` - Docker Hub password
   - `SLACK_WEBHOOK_URL` - для уведомлений (опционально)

2. **Настройте Environments**:
   - `staging` - для тестирования
   - `production` - для продакшена

3. **Автоматические процессы**:
   - Тестирование при каждом push/PR
   - Security scanning еженедельно
   - SSL сертификаты обновляются автоматически
   - Docker образы публикуются автоматически

## 📋 Управление

### Мониторинг системы
```bash
# Проверить статус всех сервисов
./scripts/monitor.sh status

# Показать статистику
./scripts/monitor.sh stats

# Показать логи
./scripts/monitor.sh logs

# Полная информация
./scripts/monitor.sh full
```

### Управление пользователями
```bash
# Сделать пользователя администратором
docker-compose exec bot python scripts/admin_tools.py make_admin TELEGRAM_ID

# Сделать супер-администратором
docker-compose exec bot python scripts/admin_tools.py make_admin TELEGRAM_ID super

# Список администраторов
docker-compose exec bot python scripts/admin_tools.py list_admins

# Информация о пользователе
docker-compose exec bot python scripts/admin_tools.py user_info TELEGRAM_ID

# Заблокировать пользователя
docker-compose exec bot python scripts/admin_tools.py block_user TELEGRAM_ID
```

### Бэкапы и восстановление
```bash
# Создать бэкап
./scripts/backup.sh

# Восстановить из бэкапа
./scripts/restore.sh backups/fok_bot_backup_YYYYMMDD_HHMMSS.gz
```

## 📊 Структура базы данных

### Коллекции:
- `users` - Пользователи бота
- `foks` - Физкультурно-оздоровительные комплексы
- `applications` - Заявки пользователей
- `districts` - Справочник районов
- `sports` - Справочник видов спорта

### Основные модели:

#### User
```python
{
    "_id": ObjectId,
    "telegram_id": int,
    "display_name": str,
    "phone": str,
    "is_admin": bool,
    "registration_completed": bool,
    "total_applications": int
}
```

#### FOK
```python
{
    "_id": ObjectId,
    "name": str,
    "district": str,
    "address": str,
    "sports": [str],
    "contacts": [dict],
    "working_hours": str
}
```

#### Application
```python
{
    "_id": ObjectId,
    "user_id": ObjectId,
    "fok_id": ObjectId,
    "status": str,  # pending, accepted, transferred, completed, cancelled
    "created_at": datetime,
    "user_name": str,
    "user_phone": str
}
```

## 🔧 Конфигурация

### Переменные окружения

#### Обязательные:
- `BOT_TOKEN` - Токен Telegram бота
- `MONGO_USERNAME` - Пользователь MongoDB
- `MONGO_PASSWORD` - Пароль MongoDB
- `REDIS_PASSWORD` - Пароль Redis

#### Опциональные:
- `WEBHOOK_URL` - URL для webhook (если используется)
- `ADMIN_CHAT_ID` - ID чата для админских уведомлений
- `MAX_ITEMS_PER_PAGE` - Количество элементов на странице (по умолчанию: 10)
- `RATE_LIMIT_REQUESTS` - Лимит запросов в минуту (по умолчанию: 30)

### Масштабирование

Для высоких нагрузок можно:

1. Увеличить количество Celery worker'ов:
```yaml
celery_worker:
  # ...
  command: celery -A app.tasks.celery_app worker --concurrency=8
```

2. Настроить репликацию MongoDB
3. Использовать Redis Cluster
4. Добавить load balancer для нескольких экземпляров бота

## 📈 Мониторинг и логирование

### Логи
- Основные логи: `logs/bot.log`
- Ошибки: `logs/errors.log`
- Автоматическая ротация и сжатие

### Метрики
- Количество пользователей
- Количество заявок по статусам
- Популярные ФОКи
- Активность пользователей

### Алерты
- Автоматические уведомления админов о новых заявках
- Еженедельные отчеты в Excel
- Уведомления о системных ошибках

## 🔒 Безопасность

- Rate limiting для предотвращения спама
- Валидация всех входных данных
- Безопасное хранение паролей и токенов
- SSL/TLS шифрование
- Регулярные бэкапы с шифрованием
- Аудит действий администраторов

## 🆘 Устранение неполадок

### Частые проблемы:

1. **Бот не отвечает**
   - Проверьте токен бота
   - Убедитесь, что все сервисы запущены: `./scripts/monitor.sh status`

2. **Ошибки базы данных**
   - Проверьте подключение к MongoDB
   - Убедитесь в правильности учетных данных

3. **Проблемы с webhook**
   - Проверьте SSL сертификаты
   - Убедитесь, что URL доступен извне

4. **Высокая нагрузка**
   - Увеличьте количество worker'ов
   - Настройте кэширование
   - Оптимизируйте запросы к БД

### Логи и диагностика:
```bash
# Логи конкретного сервиса
docker-compose logs -f bot

# Ошибки системы
./scripts/monitor.sh errors

# Состояние базы данных
docker-compose exec mongodb mongosh --eval "db.adminCommand('serverStatus')"
```

## 📞 Поддержка

Для получения поддержки:
1. Проверьте документацию
2. Изучите логи системы
3. Создайте issue с подробным описанием проблемы

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. См. файл LICENSE для подробностей.

---

**Разработано для эффективного управления сетью ФОКов с максимальным удобством для пользователей и администраторов.**