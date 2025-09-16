from .start import router as start_router
from .catalog import router as catalog_router
from .applications import router as applications_router
from .admin import router as admin_router
from .health import router as health_router

__all__ = ['start_router', 'catalog_router', 'applications_router', 'admin_router', 'health_router']