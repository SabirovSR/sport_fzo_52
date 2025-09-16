# 🚀 FOK Bot Enterprise Edition

Enterprise-grade развертывание телеграм-бота с полным мониторингом, высокой доступностью и масштабируемостью.

## 🏗️ Архитектура Enterprise Edition

```
                    ┌─────────────────┐
                    │   Internet      │
                    └─────────┬───────┘
                              │
                    ┌─────────▼───────┐
                    │    HAProxy      │ ← Load Balancer + SSL
                    │   (Port 80/443) │
                    └─────────┬───────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
    ┌─────────▼───┐ ┌─────────▼───┐ ┌─────────▼───┐
    │   Bot-1     │ │   Bot-2     │ │   Bot-3     │ ← 3 Bot Instances
    │ (Port 8001) │ │ (Port 8002) │ │ (Port 8003) │
    └─────────────┘ └─────────────┘ └─────────────┘
              │               │               │
              └───────────────┼───────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                   │                    │
    ┌────▼────┐        ┌─────▼─────┐        ┌─────▼─────┐
    │MongoDB  │        │   Redis   │        │  Celery   │
    │Replica  │        │  Cluster  │        │ Workers   │
    │  Set    │        │(6 nodes)  │        │(Pool)     │
    └─────────┘        └───────────┘        └───────────┘
         │                   │                    │
         └───────────────────┼────────────────────┘
                             │
              ┌──────────────▼──────────────┐
              │      Monitoring Stack       │
              │ Prometheus + Grafana + Loki │
              └─────────────────────────────┘
```

## 🌟 Ключевые возможности Enterprise

### 🔄 **Высокая доступность**
- **3 экземпляра бота** с автоматическим переключением
- **MongoDB Replica Set** (1 Primary + 2 Secondary)
- **Redis Cluster** (6 узлов с репликацией)
- **HAProxy Load Balancer** с health checks

### 📊 **Полный мониторинг**
- **Prometheus** - сбор метрик
- **Grafana** - визуализация и дашборды
- **Loki + Promtail** - централизованные логи
- **AlertManager** - уведомления о проблемах
- **Custom метрики** приложения

### ⚡ **Масштабируемость**
- **Горизонтальное масштабирование** всех компонентов
- **Celery Workers Pool** для фоновых задач
- **Rate Limiting** и защита от перегрузок
- **Кэширование** на уровне Redis Cluster

### 🔒 **Безопасность**
- **SSL/TLS терминация** на HAProxy
- **Rate limiting** на уровне load balancer
- **Security headers** и защита от атак
- **Изоляция сервисов** через Docker networks

## 🚀 Быстрое развертывание

### 1. Подготовка окружения

```bash
# Клонируйте репозиторий
git clone <repository-url>
cd fok-bot

# Создайте production конфигурацию
cp .env.prod.example .env.prod
```

### 2. Настройка конфигурации

Отредактируйте `.env.prod`:
```env
# Обязательные параметры
BOT_TOKEN=your_production_bot_token
MONGO_USERNAME=fok_admin
MONGO_PASSWORD=your_strong_mongo_password
REDIS_PASSWORD=your_strong_redis_password
WEBHOOK_URL=https://your-domain.com/webhook
SUPER_ADMIN_IDS=your_telegram_id

# Мониторинг
GRAFANA_ADMIN_PASSWORD=your_grafana_password
```

### 3. SSL сертификаты

```bash
# Для production используйте настоящие сертификаты
mkdir -p ssl
# Скопируйте cert.pem и key.pem в папку ssl/

# Или создайте self-signed для тестирования (автоматически)
```

### 4. Развертывание

```bash
# Запуск полной enterprise инфраструктуры
./scripts/deploy-enterprise.sh
```

Скрипт автоматически:
- ✅ Создаст Docker networks
- ✅ Запустит MongoDB Replica Set
- ✅ Настроит Redis Cluster
- ✅ Развернет monitoring stack
- ✅ Запустит 3 экземпляра бота
- ✅ Настроит load balancer
- ✅ Проверит health всех сервисов

## 📊 Мониторинг и управление

### Веб-интерфейсы:
- **Grafana**: http://localhost:3000 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **HAProxy Stats**: http://localhost:8404/stats
- **AlertManager**: http://localhost:9093

### Команды мониторинга:

```bash
# Общий обзор системы
./scripts/monitor-enterprise.sh overview

# Статус инфраструктуры
./scripts/monitor-enterprise.sh infra

# Ключевые метрики
./scripts/monitor-enterprise.sh metrics

# Логи сервисов
./scripts/monitor-enterprise.sh logs [service_name]

# Активные алерты
./scripts/monitor-enterprise.sh alerts

# Полная информация
./scripts/monitor-enterprise.sh full
```

### Управление сервисами:

```bash
# Перезапуск сервиса
./scripts/monitor-enterprise.sh restart bot-1

# Масштабирование
./scripts/monitor-enterprise.sh scale celery-worker 5

# Создание бэкапа
./scripts/monitor-enterprise.sh backup
```

## 📈 Дашборды Grafana

Включены готовые дашборды:

1. **FOK Bot - Обзор**
   - Активные пользователи
   - Заявки за день
   - Время ответа
   - Ошибки

2. **FOK Bot - Инфраструктура**
   - CPU, память, диск
   - Сетевой трафик
   - MongoDB и Redis метрики

3. **FOK Bot - Заявки и пользователи**
   - Динамика заявок
   - Распределение по статусам
   - Популярные ФОКи
   - Rate limiting

4. **FOK Bot - Celery Tasks**
   - Выполненные задачи
   - Время выполнения
   - Активные воркеры
   - Очереди

## 🚨 Алертинг

Настроены автоматические уведомления:

### Критические алерты:
- 🔴 Сервис недоступен (MongoDB, Redis, Bot)
- 🔴 Мало места на диске (>90%)
- 🔴 Высокая нагрузка CPU (>80%)

### Предупреждения:
- 🟡 Высокое использование памяти (>85%)
- 🟡 Много ошибок в приложении
- 🟡 Долгое время ответа
- 🟡 Rate limit срабатывания

## 🔧 Администрирование

### Создание админа:
```bash
docker-compose -f docker-compose.enterprise.yml exec bot-1 \
    python scripts/admin_tools.py make_admin YOUR_TELEGRAM_ID super
```

### Просмотр статистики:
```bash
docker-compose -f docker-compose.enterprise.yml exec bot-1 \
    python scripts/admin_tools.py stats
```

### Бэкапы:
```bash
# Автоматический бэкап всей системы
./scripts/monitor-enterprise.sh backup

# Ручной бэкап MongoDB
docker-compose -f docker-compose.enterprise.yml exec mongodb-primary \
    mongodump --archive=/tmp/backup.gz --gzip
```

## 🔄 Масштабирование

### Добавление bot экземпляров:

```yaml
# В docker-compose.enterprise.yml
bot-4:
  build: .
  container_name: fok_bot_instance_4
  environment:
    - BOT_INSTANCE_ID=4
    - BOT_PORT=8004
  # ... остальная конфигурация
```

```bash
# В haproxy/haproxy.cfg
server bot4 bot-4:8004 check
```

### Масштабирование Celery:
```bash
./scripts/monitor-enterprise.sh scale celery-worker-1 8  # 8 воркеров
```

### Добавление Redis узлов:
```bash
# Добавить новые узлы в docker-compose.enterprise.yml
# Перебалансировать кластер
docker-compose -f docker-compose.enterprise.yml exec redis-node-1 \
    redis-cli --cluster rebalance redis-node-1:7001
```

## 📊 Производительность

### Ожидаемая производительность:
- **Запросов в секунду**: 1000+ RPS
- **Одновременных пользователей**: 10,000+
- **Заявок в день**: 100,000+
- **Время ответа**: <100ms (95th percentile)

### Рекомендуемые ресурсы:

#### Минимальные требования:
- **CPU**: 8 cores
- **RAM**: 16GB
- **Диск**: 100GB SSD
- **Сеть**: 1Gbps

#### Рекомендуемые для продакшн:
- **CPU**: 16+ cores
- **RAM**: 32GB+
- **Диск**: 500GB+ NVMe SSD
- **Сеть**: 10Gbps

## 🔧 Troubleshooting

### Проблемы с MongoDB Replica Set:
```bash
# Проверить статус репликации
docker-compose -f docker-compose.enterprise.yml exec mongodb-primary \
    mongosh --eval "rs.status()"

# Пересоздать replica set
docker-compose -f docker-compose.enterprise.yml exec mongodb-primary \
    mongosh --eval "rs.reconfig(config, {force: true})"
```

### Проблемы с Redis Cluster:
```bash
# Проверить статус кластера
docker-compose -f docker-compose.enterprise.yml exec redis-node-1 \
    redis-cli cluster nodes

# Исправить кластер
docker-compose -f docker-compose.enterprise.yml exec redis-node-1 \
    redis-cli --cluster fix redis-node-1:7001
```

### Проблемы с Load Balancer:
```bash
# Проверить конфигурацию HAProxy
docker-compose -f docker-compose.enterprise.yml exec haproxy \
    haproxy -c -f /usr/local/etc/haproxy/haproxy.cfg

# Перезагрузить конфигурацию
docker-compose -f docker-compose.enterprise.yml restart haproxy
```

## 🎯 Best Practices

### Мониторинг:
- ✅ Настройте алерты для критических метрик
- ✅ Регулярно проверяйте дашборды
- ✅ Анализируйте тренды производительности

### Безопасность:
- ✅ Используйте сильные пароли
- ✅ Регулярно обновляйте SSL сертификаты
- ✅ Ограничивайте доступ к админским интерфейсам

### Бэкапы:
- ✅ Автоматические ежедневные бэкапы
- ✅ Тестируйте восстановление
- ✅ Храните бэкапы в разных локациях

### Обновления:
- ✅ Планируйте окна обслуживания
- ✅ Тестируйте на staging окружении
- ✅ Имейте план отката

---

**🎉 Поздравляем! Ваш FOK Bot Enterprise готов к production нагрузкам!**

Для получения поддержки обращайтесь к документации или создавайте issues в репозитории.