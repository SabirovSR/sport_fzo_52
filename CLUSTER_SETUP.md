# FOK Bot Cluster Setup 🚀

Это руководство по настройке высокодоступного кластера FOK Bot с мониторингом, логированием, репликацией MongoDB, Redis Cluster и балансировкой нагрузки.

## 🏗️ Архитектура кластера

### Компоненты

1. **Мониторинг и логирование**
   - **Prometheus** - сбор метрик
   - **Grafana** - визуализация и дашборды
   - **Loki** - централизованное логирование
   - **Promtail** - агент сбора логов
   - **Alertmanager** - управление алертами

2. **База данных (MongoDB Replica Set)**
   - **Primary** - основной узел (порт 27017)
   - **Secondary 1** - реплика 1 (порт 27018)
   - **Secondary 2** - реплика 2 (порт 27019)

3. **Кэширование (Redis Cluster)**
   - **6 узлов Redis** (3 master + 3 replica)
   - Автоматическое шардирование и репликация

4. **Приложение**
   - **3 экземпляра бота** (порты 8001-8003)
   - **2 Celery worker**
   - **1 Celery beat scheduler**

5. **Балансировка нагрузки**
   - **HAProxy** - балансировщик нагрузки
   - Sticky sessions и health checks

## 🚀 Быстрый старт

### 1. Подготовка

```bash
# Клонируйте репозиторий
git clone <repository-url>
cd fok-bot

# Создайте конфигурационный файл
cp .env.cluster.example .env.cluster
nano .env.cluster  # Настройте параметры

# Создайте keyfile для MongoDB
openssl rand -base64 756 > mongodb-keyfile
chmod 400 mongodb-keyfile

# Создайте SSL сертификаты (опционально)
mkdir -p ssl
# Поместите ваши SSL сертификаты в папку ssl/
```

### 2. Развертывание

```bash
# Развернуть полный кластер
./scripts/deploy-cluster.sh all

# Или по частям:
./scripts/deploy-cluster.sh monitoring  # Только мониторинг
./scripts/deploy-cluster.sh cluster     # Только кластер
```

### 3. Мониторинг

```bash
# Проверить статус кластера
./scripts/cluster-monitor.sh overview

# Непрерывный мониторинг
./scripts/cluster-monitor.sh monitor 30

# Просмотр логов
./scripts/cluster-monitor.sh logs bot
```

## 📊 Доступ к сервисам

### Мониторинг
- **Grafana**: http://localhost:3000 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093

### Приложение
- **Bot Instance 1**: http://localhost:8001
- **Bot Instance 2**: http://localhost:8002  
- **Bot Instance 3**: http://localhost:8003
- **Load Balancer**: http://localhost:80
- **HAProxy Stats**: http://localhost:8404/stats

### Базы данных
- **MongoDB Primary**: localhost:27017
- **MongoDB Secondary 1**: localhost:27018
- **MongoDB Secondary 2**: localhost:27019
- **Redis Node 1**: localhost:6379
- **Redis Node 2**: localhost:6380
- **Redis Node 3**: localhost:6381
- **Redis Node 4**: localhost:6382
- **Redis Node 5**: localhost:6383
- **Redis Node 6**: localhost:6384

## ⚙️ Конфигурация

### Переменные окружения (.env.cluster)

```bash
# Bot Configuration
BOT_TOKEN=your_bot_token_here
WEBHOOK_URL=https://your-domain.com/webhook
WEBHOOK_SECRET=your_webhook_secret

# Database Configuration (MongoDB Replica Set)
MONGO_HOST=mongodb-primary:27017,mongodb-secondary-1:27017,mongodb-secondary-2:27017
MONGO_USERNAME=fokbot
MONGO_PASSWORD=fokbot123

# Redis Configuration (Redis Cluster)
REDIS_HOST=redis-node-1:6379,redis-node-2:6379,redis-node-3:6379,redis-node-4:6379,redis-node-5:6379,redis-node-6:6379

# Monitoring
GRAFANA_ADMIN_PASSWORD=admin123
```

## 📈 Мониторинг и метрики

### Prometheus метрики

Приложение экспортирует следующие метрики:

- `http_requests_total` - общее количество HTTP запросов
- `telegram_updates_total` - количество обновлений от Telegram
- `telegram_messages_sent_total` - отправленные сообщения
- `active_users_total` - активные пользователи
- `database_operations_total` - операции с БД
- `celery_tasks_total` - задачи Celery
- `errors_total` - ошибки по компонентам

### Grafana дашборды

Автоматически созданные дашборды:
- **FOK Bot Overview** - общий обзор системы
- **MongoDB Metrics** - метрики базы данных
- **Redis Metrics** - метрики кэша
- **System Resources** - ресурсы системы

### Алерты

Настроенные алерты:
- Недоступность сервисов
- Высокая нагрузка на CPU/память
- Проблемы с базой данных
- Ошибки в приложении

## 🔧 Управление кластером

### Команды Docker Compose

```bash
# Запуск всех сервисов
docker-compose -f docker-compose.cluster.yml up -d

# Остановка
docker-compose -f docker-compose.cluster.yml down

# Просмотр статуса
docker-compose -f docker-compose.cluster.yml ps

# Логи
docker-compose -f docker-compose.cluster.yml logs -f bot-1

# Масштабирование (добавление экземпляров)
docker-compose -f docker-compose.cluster.yml up -d --scale bot=5
```

### Управление MongoDB Replica Set

```bash
# Подключение к primary
docker exec -it fok_bot_mongodb_primary mongosh

# Проверка статуса реплики
rs.status()

# Добавление нового узла
rs.add("new-node:27017")

# Удаление узла
rs.remove("node:27017")
```

### Управление Redis Cluster

```bash
# Подключение к узлу
docker exec -it fok_bot_redis_node_1 redis-cli

# Информация о кластере
cluster info
cluster nodes

# Добавление узла
cluster meet <ip> <port>
```

## 🛠️ Обслуживание

### Резервное копирование

```bash
# MongoDB
./scripts/backup.sh mongodb

# Redis
./scripts/backup.sh redis

# Полное резервное копирование
./scripts/backup.sh all
```

### Обновление

```bash
# Обновление образов
docker-compose -f docker-compose.cluster.yml pull

# Перезапуск с обновлением
docker-compose -f docker-compose.cluster.yml up -d --force-recreate
```

### Масштабирование

```bash
# Добавление экземпляра бота
# 1. Обновите docker-compose.cluster.yml
# 2. Обновите конфигурацию HAProxy
# 3. Перезапустите сервисы
docker-compose -f docker-compose.cluster.yml up -d
```

## 🚨 Устранение неполадок

### Проверка здоровья сервисов

```bash
# Общий статус
./scripts/cluster-monitor.sh overview

# Проверка конкретного сервиса
./scripts/cluster-monitor.sh mongodb
./scripts/cluster-monitor.sh redis
./scripts/cluster-monitor.sh bot
```

### Типичные проблемы

1. **MongoDB replica set не инициализируется**
   ```bash
   # Проверьте логи
   docker logs fok_bot_mongodb_primary
   
   # Переинициализация
   docker exec fok_bot_mongodb_primary mongosh --eval "rs.initiate()"
   ```

2. **Redis cluster не формируется**
   ```bash
   # Проверьте состояние узлов
   docker exec fok_bot_redis_node_1 redis-cli cluster nodes
   
   # Переинициализация
   docker-compose -f docker-compose.cluster.yml restart redis-cluster-init
   ```

3. **Бот не отвечает**
   ```bash
   # Проверьте логи
   docker logs fok_bot_1
   
   # Проверьте health endpoint
   curl http://localhost:8001/health
   ```

### Логи

```bash
# Все логи
./scripts/cluster-monitor.sh logs all

# Конкретный сервис
./scripts/cluster-monitor.sh logs bot
./scripts/cluster-monitor.sh logs mongodb
./scripts/cluster-monitor.sh logs redis
```

## 📋 Чек-лист развертывания

- [ ] Настроен файл `.env.cluster`
- [ ] Создан `mongodb-keyfile`
- [ ] Настроены SSL сертификаты (для production)
- [ ] Развернут мониторинг стек
- [ ] Развернут кластер приложения
- [ ] Проверено здоровье всех сервисов
- [ ] Настроены алерты
- [ ] Протестирована отказоустойчивость
- [ ] Настроено резервное копирование

## 🔐 Безопасность

1. **Смените пароли по умолчанию**
2. **Используйте SSL сертификаты**
3. **Настройте firewall**
4. **Ограничьте доступ к портам**
5. **Регулярно обновляйте образы**
6. **Мониторьте безопасность**

## 📚 Дополнительные ресурсы

- [MongoDB Replica Set](https://docs.mongodb.com/manual/replication/)
- [Redis Cluster](https://redis.io/topics/cluster-tutorial)
- [HAProxy Configuration](http://www.haproxy.org/download/2.8/doc/configuration.txt)
- [Prometheus Monitoring](https://prometheus.io/docs/)
- [Grafana Dashboards](https://grafana.com/docs/)

---

**Поздравляем! Ваш FOK Bot кластер готов к работе! 🎉**