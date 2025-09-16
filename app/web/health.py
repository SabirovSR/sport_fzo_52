from aiohttp import web
from datetime import datetime
import json
from loguru import logger

from app.database.connection import check_database_health, get_database_stats
from app.utils.metrics import get_metrics


async def health_check(request):
    """HTTP health check endpoint"""
    try:
        # Check database
        db_healthy = await check_database_health()
        
        # Get basic stats (optional, for detailed health check)
        try:
            stats = await get_database_stats()
        except Exception:
            stats = {}
        
        # Prepare response
        health_data = {
            "status": "healthy" if db_healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": {
                "status": "healthy" if db_healthy else "unhealthy"
            },
            "version": "1.0.0"
        }
        
        # Add stats if available
        if stats and stats.get('collections'):
            health_data["stats"] = {
                "users": stats['collections'].get('users', 0),
                "foks": stats['collections'].get('foks', 0),
                "applications": stats['collections'].get('applications', 0)
            }
        
        status_code = 200 if db_healthy else 503
        
        return web.json_response(
            health_data,
            status=status_code,
            headers={'Content-Type': 'application/json'}
        )
        
    except Exception as e:
        logger.error(f"Health check endpoint error: {e}")
        return web.json_response(
            {
                "status": "error",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            },
            status=500
        )


async def ready_check(request):
    """HTTP readiness check endpoint"""
    try:
        # Simple readiness check - just return OK
        return web.json_response(
            {
                "status": "ready",
                "timestamp": datetime.utcnow().isoformat()
            },
            status=200
        )
    except Exception as e:
        logger.error(f"Ready check endpoint error: {e}")
        return web.json_response(
            {
                "status": "not_ready",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            },
            status=503
        )


async def metrics_endpoint(request):
    """Prometheus metrics endpoint"""
    try:
        # Update metrics before serving
        from app.utils.metrics import update_application_metrics, update_user_metrics
        await update_application_metrics()
        await update_user_metrics()
        
        # Get metrics
        metrics_data = get_metrics()
        
        return web.Response(
            text=metrics_data,
            content_type='text/plain; version=0.0.4; charset=utf-8'
        )
    except Exception as e:
        logger.error(f"Metrics endpoint error: {e}")
        return web.Response(
            text=f"# Error generating metrics: {e}\n",
            status=500,
            content_type='text/plain'
        )


def setup_health_routes(app: web.Application):
    """Setup health check routes"""
    app.router.add_get('/health', health_check)
    app.router.add_get('/ready', ready_check)
    app.router.add_get('/healthz', health_check)  # Kubernetes style
    app.router.add_get('/readyz', ready_check)   # Kubernetes style
    app.router.add_get('/metrics', metrics_endpoint)  # Prometheus metrics