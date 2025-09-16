"""Sentry integration for error monitoring and performance tracking."""

import os
import logging
from typing import Optional, Dict, Any
from sentry_sdk import init, capture_exception, capture_message, add_breadcrumb
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration

from app.config import settings

logger = logging.getLogger(__name__)


class SentryManager:
    """Manages Sentry integration for error monitoring."""
    
    def __init__(self, dsn: Optional[str] = None, environment: str = "production"):
        self.dsn = dsn or os.getenv("SENTRY_DSN")
        self.environment = environment
        self.is_initialized = False
        
    def initialize(self) -> bool:
        """Initialize Sentry SDK."""
        if not self.dsn:
            logger.warning("Sentry DSN not provided, skipping Sentry initialization")
            return False
            
        if self.is_initialized:
            logger.warning("Sentry already initialized")
            return True
            
        try:
            # Configure logging integration
            logging_integration = LoggingIntegration(
                level=logging.INFO,        # Capture info and above as breadcrumbs
                event_level=logging.ERROR  # Send errors as events
            )
            
            # Initialize Sentry
            init(
                dsn=self.dsn,
                environment=self.environment,
                integrations=[
                    logging_integration,
                    RedisIntegration(),
                    CeleryIntegration(),
                    AioHttpIntegration(),
                    AsyncioIntegration(),
                ],
                traces_sample_rate=0.1,  # 10% of transactions
                profiles_sample_rate=0.1,  # 10% of transactions
                send_default_pii=False,  # Don't send personally identifiable information
                attach_stacktrace=True,
                release=self._get_release(),
                before_send=self._before_send,
            )
            
            self.is_initialized = True
            logger.info("Sentry initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Sentry: {e}")
            return False
    
    def _get_release(self) -> Optional[str]:
        """Get application release version."""
        # Try to get version from environment or git
        version = os.getenv("APP_VERSION")
        if version:
            return version
            
        # Try to get from git
        try:
            import subprocess
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()[:8]  # Short commit hash
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None
    
    def _before_send(self, event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Filter and modify events before sending to Sentry."""
        # Filter out certain exceptions
        if 'exc_info' in hint:
            exc_type, exc_value, exc_traceback = hint['exc_info']
            
            # Skip certain exceptions
            skip_exceptions = (
                KeyboardInterrupt,
                SystemExit,
            )
            
            if isinstance(exc_value, skip_exceptions):
                return None
                
            # Skip aiogram specific exceptions that are not critical
            if hasattr(exc_value, '__module__'):
                if exc_value.__module__.startswith('aiogram.exceptions'):
                    # Only send critical aiogram exceptions
                    if 'RetryAfter' in str(type(exc_value)):
                        return None  # Skip rate limiting errors
                    if 'BadRequest' in str(type(exc_value)):
                        return None  # Skip bad request errors
        
        # Add custom tags
        event.setdefault('tags', {}).update({
            'bot_instance': settings.BOT_INSTANCE_ID,
            'worker_id': settings.WORKER_ID,
        })
        
        # Add custom context
        event.setdefault('contexts', {}).update({
            'bot': {
                'instance_id': settings.BOT_INSTANCE_ID,
                'worker_id': settings.WORKER_ID,
                'debug_mode': settings.DEBUG,
            }
        })
        
        return event
    
    def capture_exception(self, exception: Exception, **kwargs) -> Optional[str]:
        """Capture an exception."""
        if not self.is_initialized:
            logger.warning("Sentry not initialized, cannot capture exception")
            return None
            
        try:
            return capture_exception(exception, **kwargs)
        except Exception as e:
            logger.error(f"Failed to capture exception: {e}")
            return None
    
    def capture_message(self, message: str, level: str = "info", **kwargs) -> Optional[str]:
        """Capture a message."""
        if not self.is_initialized:
            logger.warning("Sentry not initialized, cannot capture message")
            return None
            
        try:
            return capture_message(message, level=level, **kwargs)
        except Exception as e:
            logger.error(f"Failed to capture message: {e}")
            return None
    
    def add_breadcrumb(self, message: str, category: str = "default", level: str = "info", **kwargs):
        """Add a breadcrumb."""
        if not self.is_initialized:
            return
            
        try:
            add_breadcrumb(
                message=message,
                category=category,
                level=level,
                **kwargs
            )
        except Exception as e:
            logger.error(f"Failed to add breadcrumb: {e}")
    
    def set_user_context(self, user_id: int, username: Optional[str] = None, **kwargs):
        """Set user context for error tracking."""
        if not self.is_initialized:
            return
            
        try:
            from sentry_sdk import set_user
            set_user({
                "id": str(user_id),
                "username": username,
                **kwargs
            })
        except Exception as e:
            logger.error(f"Failed to set user context: {e}")
    
    def set_extra_context(self, **kwargs):
        """Set extra context for error tracking."""
        if not self.is_initialized:
            return
            
        try:
            from sentry_sdk import set_extra
            set_extra(kwargs)
        except Exception as e:
            logger.error(f"Failed to set extra context: {e}")
    
    def set_tag(self, key: str, value: str):
        """Set a tag for error tracking."""
        if not self.is_initialized:
            return
            
        try:
            from sentry_sdk import set_tag
            set_tag(key, value)
        except Exception as e:
            logger.error(f"Failed to set tag: {e}")


# Global Sentry manager instance
sentry_manager = SentryManager(
    environment="production" if not settings.DEBUG else "development"
)


def initialize_sentry() -> bool:
    """Initialize Sentry integration."""
    return sentry_manager.initialize()


def capture_error(exception: Exception, **kwargs) -> Optional[str]:
    """Capture an error with Sentry."""
    return sentry_manager.capture_exception(exception, **kwargs)


def capture_info(message: str, **kwargs) -> Optional[str]:
    """Capture an info message with Sentry."""
    return sentry_manager.capture_message(message, level="info", **kwargs)


def capture_warning(message: str, **kwargs) -> Optional[str]:
    """Capture a warning message with Sentry."""
    return sentry_manager.capture_message(message, level="warning", **kwargs)


def add_breadcrumb(message: str, category: str = "default", level: str = "info", **kwargs):
    """Add a breadcrumb to Sentry."""
    sentry_manager.add_breadcrumb(message, category, level, **kwargs)


def set_user_context(user_id: int, username: Optional[str] = None, **kwargs):
    """Set user context for Sentry."""
    sentry_manager.set_user_context(user_id, username, **kwargs)


def set_extra_context(**kwargs):
    """Set extra context for Sentry."""
    sentry_manager.set_extra_context(**kwargs)


def set_tag(key: str, value: str):
    """Set a tag for Sentry."""
    sentry_manager.set_tag(key, value)