"""
Prometheus metrics for FOK Bot monitoring
"""
import time
from functools import wraps
from typing import Dict, Any, Optional, Callable
from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry, generate_latest
from prometheus_client.openmetrics.exposition import CONTENT_TYPE_LATEST
from loguru import logger

# Create a custom registry for the bot metrics
bot_registry = CollectorRegistry()

# Bot-specific metrics
bot_info = Info(
    'fok_bot_info',
    'Information about the FOK Bot',
    registry=bot_registry
)

# HTTP metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'handler', 'status'],
    registry=bot_registry
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'handler'],
    registry=bot_registry
)

# Bot interaction metrics
telegram_updates_total = Counter(
    'telegram_updates_total',
    'Total Telegram updates received',
    ['update_type'],
    registry=bot_registry
)

telegram_messages_sent_total = Counter(
    'telegram_messages_sent_total',
    'Total messages sent by bot',
    ['chat_type'],
    registry=bot_registry
)

telegram_commands_total = Counter(
    'telegram_commands_total',
    'Total commands processed',
    ['command'],
    registry=bot_registry
)

telegram_callback_queries_total = Counter(
    'telegram_callback_queries_total',
    'Total callback queries processed',
    ['action'],
    registry=bot_registry
)

# User metrics
active_users_total = Gauge(
    'active_users_total',
    'Total number of active users',
    registry=bot_registry
)

user_registrations_total = Counter(
    'user_registrations_total',
    'Total user registrations',
    registry=bot_registry
)

# Application metrics
applications_submitted_total = Counter(
    'applications_submitted_total',
    'Total applications submitted',
    ['sport', 'district'],
    registry=bot_registry
)

applications_processed_total = Counter(
    'applications_processed_total',
    'Total applications processed',
    ['status'],
    registry=bot_registry
)

# Database metrics
database_operations_total = Counter(
    'database_operations_total',
    'Total database operations',
    ['operation', 'collection'],
    registry=bot_registry
)

database_operation_duration_seconds = Histogram(
    'database_operation_duration_seconds',
    'Database operation duration in seconds',
    ['operation', 'collection'],
    registry=bot_registry
)

database_connections_active = Gauge(
    'database_connections_active',
    'Active database connections',
    registry=bot_registry
)

# Cache metrics
cache_operations_total = Counter(
    'cache_operations_total',
    'Total cache operations',
    ['operation', 'result'],
    registry=bot_registry
)

cache_operation_duration_seconds = Histogram(
    'cache_operation_duration_seconds',
    'Cache operation duration in seconds',
    ['operation'],
    registry=bot_registry
)

# Celery metrics (will be handled by celery-prometheus-exporter)
celery_tasks_total = Counter(
    'celery_tasks_total',
    'Total Celery tasks',
    ['task_name', 'state'],
    registry=bot_registry
)

celery_task_duration_seconds = Histogram(
    'celery_task_duration_seconds',
    'Celery task duration in seconds',
    ['task_name'],
    registry=bot_registry
)

celery_queue_length = Gauge(
    'celery_queue_length',
    'Current Celery queue length',
    ['queue'],
    registry=bot_registry
)

# Error metrics
errors_total = Counter(
    'errors_total',
    'Total errors',
    ['error_type', 'component'],
    registry=bot_registry
)

# Rate limiting metrics
rate_limit_hits_total = Counter(
    'rate_limit_hits_total',
    'Total rate limit hits',
    ['user_id', 'action'],
    registry=bot_registry
)


class MetricsCollector:
    """Centralized metrics collection and management"""
    
    def __init__(self):
        self.start_time = time.time()
        self._initialize_bot_info()
    
    def _initialize_bot_info(self):
        """Initialize bot information metrics"""
        bot_info.info({
            'version': '1.0.0',
            'environment': 'production',
            'start_time': str(int(self.start_time))
        })
    
    def record_http_request(self, method: str, handler: str, status: int, duration: float):
        """Record HTTP request metrics"""
        http_requests_total.labels(method=method, handler=handler, status=str(status)).inc()
        http_request_duration_seconds.labels(method=method, handler=handler).observe(duration)
    
    def record_telegram_update(self, update_type: str):
        """Record Telegram update"""
        telegram_updates_total.labels(update_type=update_type).inc()
    
    def record_message_sent(self, chat_type: str):
        """Record sent message"""
        telegram_messages_sent_total.labels(chat_type=chat_type).inc()
    
    def record_command(self, command: str):
        """Record processed command"""
        telegram_commands_total.labels(command=command).inc()
    
    def record_callback_query(self, action: str):
        """Record processed callback query"""
        telegram_callback_queries_total.labels(action=action).inc()
    
    def record_user_registration(self):
        """Record user registration"""
        user_registrations_total.inc()
    
    def update_active_users(self, count: int):
        """Update active users count"""
        active_users_total.set(count)
    
    def record_application_submitted(self, sport: str, district: str):
        """Record application submission"""
        applications_submitted_total.labels(sport=sport, district=district).inc()
    
    def record_application_processed(self, status: str):
        """Record application processing"""
        applications_processed_total.labels(status=status).inc()
    
    def record_database_operation(self, operation: str, collection: str, duration: float):
        """Record database operation"""
        database_operations_total.labels(operation=operation, collection=collection).inc()
        database_operation_duration_seconds.labels(operation=operation, collection=collection).observe(duration)
    
    def update_database_connections(self, count: int):
        """Update database connections count"""
        database_connections_active.set(count)
    
    def record_cache_operation(self, operation: str, result: str, duration: float):
        """Record cache operation"""
        cache_operations_total.labels(operation=operation, result=result).inc()
        cache_operation_duration_seconds.labels(operation=operation).observe(duration)
    
    def record_celery_task(self, task_name: str, state: str, duration: Optional[float] = None):
        """Record Celery task"""
        celery_tasks_total.labels(task_name=task_name, state=state).inc()
        if duration is not None:
            celery_task_duration_seconds.labels(task_name=task_name).observe(duration)
    
    def update_celery_queue_length(self, queue: str, length: int):
        """Update Celery queue length"""
        celery_queue_length.labels(queue=queue).set(length)
    
    def record_error(self, error_type: str, component: str):
        """Record error"""
        errors_total.labels(error_type=error_type, component=component).inc()
    
    def record_rate_limit_hit(self, user_id: str, action: str):
        """Record rate limit hit"""
        rate_limit_hits_total.labels(user_id=user_id, action=action).inc()
    
    def get_metrics(self) -> str:
        """Get all metrics in Prometheus format"""
        return generate_latest(bot_registry).decode('utf-8')


# Global metrics collector instance
metrics = MetricsCollector()


def track_time(metric: Histogram, labels: Dict[str, str] = None):
    """Decorator to track execution time"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)
        
        # Return appropriate wrapper based on function type
        if hasattr(func, '__code__') and func.__code__.co_flags & 0x80:  # CO_COROUTINE
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def track_database_operation(operation: str, collection: str):
    """Decorator to track database operations"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                metrics.record_error(type(e).__name__, 'database')
                raise
            finally:
                duration = time.time() - start_time
                metrics.record_database_operation(operation, collection, duration)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                metrics.record_error(type(e).__name__, 'database')
                raise
            finally:
                duration = time.time() - start_time
                metrics.record_database_operation(operation, collection, duration)
        
        # Return appropriate wrapper based on function type
        if hasattr(func, '__code__') and func.__code__.co_flags & 0x80:  # CO_COROUTINE
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def track_cache_operation(operation: str):
    """Decorator to track cache operations"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            result_status = 'success'
            try:
                result = await func(*args, **kwargs)
                if result is None:
                    result_status = 'miss'
                return result
            except Exception as e:
                result_status = 'error'
                metrics.record_error(type(e).__name__, 'cache')
                raise
            finally:
                duration = time.time() - start_time
                metrics.record_cache_operation(operation, result_status, duration)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            result_status = 'success'
            try:
                result = func(*args, **kwargs)
                if result is None:
                    result_status = 'miss'
                return result
            except Exception as e:
                result_status = 'error'
                metrics.record_error(type(e).__name__, 'cache')
                raise
            finally:
                duration = time.time() - start_time
                metrics.record_cache_operation(operation, result_status, duration)
        
        # Return appropriate wrapper based on function type
        if hasattr(func, '__code__') and func.__code__.co_flags & 0x80:  # CO_COROUTINE
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator