import time
from typing import Dict, Any
from functools import wraps
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
from loguru import logger

# Создаем собственный реестр метрик
REGISTRY = CollectorRegistry()

# Метрики приложения
REQUEST_COUNT = Counter(
    'fok_bot_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status'],
    registry=REGISTRY
)

REQUEST_DURATION = Histogram(
    'fok_bot_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint'],
    registry=REGISTRY
)

ERROR_COUNT = Counter(
    'fok_bot_errors_total',
    'Total number of errors',
    ['error_type', 'handler'],
    registry=REGISTRY
)

RATE_LIMIT_HITS = Counter(
    'fok_bot_rate_limit_hits_total',
    'Total number of rate limit hits',
    ['user_id'],
    registry=REGISTRY
)

ACTIVE_USERS = Gauge(
    'fok_bot_active_users_total',
    'Number of active users',
    registry=REGISTRY
)

APPLICATIONS_CREATED = Counter(
    'fok_bot_applications_created_total',
    'Total number of applications created',
    registry=REGISTRY
)

APPLICATIONS_BY_STATUS = Gauge(
    'fok_bot_applications_by_status',
    'Number of applications by status',
    ['status'],
    registry=REGISTRY
)

DATABASE_OPERATIONS = Counter(
    'fok_bot_database_operations_total',
    'Total number of database operations',
    ['operation', 'collection', 'status'],
    registry=REGISTRY
)

DATABASE_OPERATION_DURATION = Histogram(
    'fok_bot_database_operation_duration_seconds',
    'Database operation duration in seconds',
    ['operation', 'collection'],
    registry=REGISTRY
)

CELERY_TASKS = Counter(
    'fok_bot_celery_tasks_total',
    'Total number of Celery tasks',
    ['task_name', 'status'],
    registry=REGISTRY
)

CELERY_TASK_DURATION = Histogram(
    'fok_bot_celery_task_duration_seconds',
    'Celery task duration in seconds',
    ['task_name'],
    registry=REGISTRY
)

TELEGRAM_API_CALLS = Counter(
    'fok_bot_telegram_api_calls_total',
    'Total number of Telegram API calls',
    ['method', 'status'],
    registry=REGISTRY
)

TELEGRAM_API_DURATION = Histogram(
    'fok_bot_telegram_api_duration_seconds',
    'Telegram API call duration in seconds',
    ['method'],
    registry=REGISTRY
)


def track_request(method: str = "unknown", endpoint: str = "unknown"):
    """Декоратор для отслеживания HTTP запросов"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                ERROR_COUNT.labels(
                    error_type=type(e).__name__,
                    handler=func.__name__
                ).inc()
                raise
            finally:
                duration = time.time() - start_time
                REQUEST_COUNT.labels(
                    method=method,
                    endpoint=endpoint,
                    status=status
                ).inc()
                REQUEST_DURATION.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(duration)
        
        return wrapper
    return decorator


def track_database_operation(operation: str, collection: str):
    """Декоратор для отслеживания операций с базой данных"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                logger.error(f"Database operation failed: {operation} on {collection}: {e}")
                raise
            finally:
                duration = time.time() - start_time
                DATABASE_OPERATIONS.labels(
                    operation=operation,
                    collection=collection,
                    status=status
                ).inc()
                DATABASE_OPERATION_DURATION.labels(
                    operation=operation,
                    collection=collection
                ).observe(duration)
        
        return wrapper
    return decorator


def track_celery_task(task_name: str):
    """Декоратор для отслеживания Celery задач"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                logger.error(f"Celery task failed: {task_name}: {e}")
                raise
            finally:
                duration = time.time() - start_time
                CELERY_TASKS.labels(
                    task_name=task_name,
                    status=status
                ).inc()
                CELERY_TASK_DURATION.labels(
                    task_name=task_name
                ).observe(duration)
        
        return wrapper
    return decorator


def track_telegram_api(method: str):
    """Декоратор для отслеживания вызовов Telegram API"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                logger.error(f"Telegram API call failed: {method}: {e}")
                raise
            finally:
                duration = time.time() - start_time
                TELEGRAM_API_CALLS.labels(
                    method=method,
                    status=status
                ).inc()
                TELEGRAM_API_DURATION.labels(
                    method=method
                ).observe(duration)
        
        return wrapper
    return decorator


async def update_application_metrics():
    """Обновить метрики заявок"""
    try:
        from app.database.repositories import application_repo
        from app.models.application import ApplicationStatus
        
        # Получаем статистику по статусам
        stats = await application_repo.get_statistics(days=365)  # За весь период
        
        # Обновляем метрики
        for status in ApplicationStatus:
            count = stats.get(status.value, 0)
            APPLICATIONS_BY_STATUS.labels(status=status.value).set(count)
            
    except Exception as e:
        logger.error(f"Failed to update application metrics: {e}")


async def update_user_metrics():
    """Обновить метрики пользователей"""
    try:
        from app.database.repositories import user_repo
        
        # Активные пользователи за последние 24 часа
        active_count = await user_repo.get_active_users_count(days=1)
        ACTIVE_USERS.set(active_count)
        
    except Exception as e:
        logger.error(f"Failed to update user metrics: {e}")


def record_rate_limit_hit(user_id: int):
    """Записать срабатывание rate limit"""
    RATE_LIMIT_HITS.labels(user_id=str(user_id)).inc()


def record_application_created():
    """Записать создание заявки"""
    APPLICATIONS_CREATED.inc()


def get_metrics() -> str:
    """Получить метрики в формате Prometheus"""
    return generate_latest(REGISTRY).decode('utf-8')