import asyncio
import sys
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiohttp import web
from loguru import logger

from app.config import settings
from app.utils.logging import setup_logging
from app.database.connection import init_database, close_database
from app.middlewares import RateLimitMiddleware, UserMiddleware
from app.handlers import start_router, catalog_router, applications_router, admin_router, health_router


async def on_startup():
    """Bot startup handler"""
    logger.info("Starting FOK Bot...")
    
    # Initialize database
    await init_database()
    logger.info("Database initialized")
    
    # Set bot commands
    await bot.set_my_commands([
        {"command": "start", "description": "🏠 Начать работу с ботом"},
        {"command": "menu", "description": "📋 Главное меню"},
        {"command": "help", "description": "❓ Помощь"},
    ])
    
    logger.info("Bot started successfully!")


async def on_shutdown():
    """Bot shutdown handler"""
    logger.info("Shutting down FOK Bot...")
    
    # Close database connection
    await close_database()
    
    # Close bot session
    await bot.session.close()
    
    logger.info("Bot shutdown complete")


async def main():
    """Main function"""
    
    # Setup logging
    setup_logging()
    
    # Create bot and dispatcher
    global bot, dp
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
            link_preview_is_disabled=True
        )
    )
    dp = Dispatcher()
    
    # Register middlewares
    dp.message.middleware(RateLimitMiddleware())
    dp.callback_query.middleware(RateLimitMiddleware())
    dp.message.middleware(UserMiddleware())
    dp.callback_query.middleware(UserMiddleware())
    
    # Register routers
    dp.include_router(start_router)
    dp.include_router(catalog_router)
    dp.include_router(applications_router)
    dp.include_router(admin_router)
    dp.include_router(health_router)
    
    # Register startup and shutdown handlers
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    try:
        if settings.WEBHOOK_URL:
            # Webhook mode
            logger.info(f"Starting webhook mode: {settings.WEBHOOK_URL}")
            
            # Set webhook
            await bot.set_webhook(
                url=settings.WEBHOOK_URL,
                secret_token=settings.WEBHOOK_SECRET
            )
            
            # Create web application
            app = web.Application()
            
            # Setup health check routes
            from app.web import setup_health_routes
            setup_health_routes(app)
            
            # Create webhook handler
            webhook_requests_handler = SimpleRequestHandler(
                dispatcher=dp,
                bot=bot,
                secret_token=settings.WEBHOOK_SECRET
            )
            
            # Register webhook handler
            webhook_requests_handler.register(app, path="/webhook")
            
            # Setup application
            setup_application(app, dp, bot=bot)
            
            # Start web server
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, "0.0.0.0", 8000)
            await site.start()
            
            logger.info("Webhook server started on port 8000")
            
            # Keep running
            await asyncio.Future()
            
        else:
            # Polling mode
            logger.info("Starting polling mode")
            await dp.start_polling(bot)
            
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
        sys.exit(1)
    finally:
        await on_shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)