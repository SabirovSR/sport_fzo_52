"""Pytest configuration and fixtures for FOK Bot tests."""

import asyncio
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from typing import AsyncGenerator, Generator
from faker import Faker

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from motor.motor_asyncio import AsyncIOMotorClient
from redis.asyncio import Redis

from app.config import Settings
from app.database.connection import init_database, close_database
from app.models import User, District, FOK, Sport, Application


# Test settings
@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Create test settings."""
    return Settings(
        BOT_TOKEN="test_token",
        MONGO_HOST="localhost",
        MONGO_PORT=27017,
        MONGO_DB_NAME="fok_bot_test",
        REDIS_HOST="localhost",
        REDIS_PORT=6379,
        DEBUG=True,
        LOG_LEVEL="DEBUG"
    )


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def bot(test_settings: Settings) -> Bot:
    """Create test bot instance."""
    return Bot(
        token=test_settings.BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
            link_preview_is_disabled=True
        )
    )


@pytest.fixture
async def dispatcher() -> Dispatcher:
    """Create test dispatcher instance."""
    return Dispatcher()


@pytest.fixture
async def mock_database() -> AsyncMock:
    """Create mock database connection."""
    mock_db = AsyncMock()
    mock_collection = AsyncMock()
    mock_db.users = mock_collection
    mock_db.districts = mock_collection
    mock_db.foks = mock_collection
    mock_db.sports = mock_collection
    mock_db.applications = mock_collection
    return mock_db


@pytest.fixture
async def mock_redis() -> AsyncMock:
    """Create mock Redis connection."""
    mock_redis = AsyncMock(spec=Redis)
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.delete = AsyncMock(return_value=1)
    mock_redis.exists = AsyncMock(return_value=False)
    mock_redis.expire = AsyncMock(return_value=True)
    return mock_redis


@pytest.fixture
def fake() -> Faker:
    """Create Faker instance for generating test data."""
    return Faker('ru_RU')


@pytest.fixture
def sample_user(fake: Faker) -> User:
    """Create sample user for testing."""
    return User(
        telegram_id=fake.random_int(min=100000, max=999999),
        username=fake.user_name(),
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        display_name=fake.name(),
        phone=fake.phone_number(),
        language_code="ru",
        is_admin=False,
        is_super_admin=False,
        is_blocked=False,
        registration_completed=True,
        phone_shared=True,
        total_applications=0
    )


@pytest.fixture
def sample_district(fake: Faker) -> District:
    """Create sample district for testing."""
    return District(
        name=fake.city(),
        description=fake.text(max_nb_chars=200),
        is_active=True
    )


@pytest.fixture
def sample_fok(fake: Faker, sample_district: District) -> FOK:
    """Create sample FOK for testing."""
    return FOK(
        name=fake.company(),
        district_id=sample_district.id,
        address=fake.address(),
        description=fake.text(max_nb_chars=500),
        phone=fake.phone_number(),
        email=fake.email(),
        website=fake.url(),
        latitude=fake.latitude(),
        longitude=fake.longitude(),
        is_active=True
    )


@pytest.fixture
def sample_sport(fake: Faker) -> Sport:
    """Create sample sport for testing."""
    return Sport(
        name=fake.word().title(),
        description=fake.text(max_nb_chars=200),
        is_active=True
    )


@pytest.fixture
def sample_application(fake: Faker, sample_user: User, sample_fok: FOK) -> Application:
    """Create sample application for testing."""
    return Application(
        user_id=sample_user.id,
        fok_id=sample_fok.id,
        status="pending",
        message=fake.text(max_nb_chars=300),
        admin_notes=""
    )


# Database setup/teardown
@pytest.fixture(scope="function")
async def test_database(test_settings: Settings) -> AsyncGenerator[AsyncIOMotorClient, None]:
    """Setup test database connection."""
    client = AsyncIOMotorClient(test_settings.mongo_url)
    db = client[test_settings.MONGO_DB_NAME]
    
    # Clear test database
    await db.drop_collection("users")
    await db.drop_collection("districts")
    await db.drop_collection("foks")
    await db.drop_collection("sports")
    await db.drop_collection("applications")
    
    yield client
    
    # Cleanup
    await client.close()


# Mock external services
@pytest.fixture
def mock_telegram_api():
    """Mock Telegram API responses."""
    mock = MagicMock()
    mock.get_me = AsyncMock(return_value={
        "id": 123456789,
        "is_bot": True,
        "first_name": "Test Bot",
        "username": "test_bot"
    })
    mock.send_message = AsyncMock(return_value={
        "message_id": 1,
        "chat": {"id": 123456, "type": "private"},
        "text": "Test message"
    })
    mock.edit_message_text = AsyncMock(return_value=True)
    mock.answer_callback_query = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_celery():
    """Mock Celery task execution."""
    mock = MagicMock()
    mock.send_task = AsyncMock(return_value=MagicMock(id="test-task-id"))
    mock.AsyncResult = MagicMock(return_value=MagicMock(status="PENDING"))
    return mock