#!/usr/bin/env python3
"""
Script to initialize database with sample data
"""
import asyncio
import sys
import os

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database.connection import init_database
from app.database.repositories import district_repo, sport_repo, fok_repo
from app.models import District, Sport, FOK


async def init_sample_data():
    """Initialize database with sample data"""
    print("Initializing database...")
    await init_database()
    
    # Sample districts
    districts_data = [
        {"name": "Центральный район", "sort_order": 1},
        {"name": "Северный район", "sort_order": 2},
        {"name": "Южный район", "sort_order": 3},
        {"name": "Восточный район", "sort_order": 4},
        {"name": "Западный район", "sort_order": 5},
        {"name": "Ленинский район", "sort_order": 6},
        {"name": "Октябрьский район", "sort_order": 7},
        {"name": "Советский район", "sort_order": 8},
    ]
    
    print("Creating districts...")
    for district_data in districts_data:
        existing = await district_repo.find_by_name(district_data["name"])
        if not existing:
            district = District(**district_data)
            await district_repo.create(district)
            print(f"Created district: {district.name}")
    
    # Sample sports
    sports_data = [
        {"name": "Футбол", "icon": "⚽", "sort_order": 1},
        {"name": "Баскетбол", "icon": "🏀", "sort_order": 2},
        {"name": "Волейбол", "icon": "🏐", "sort_order": 3},
        {"name": "Плавание", "icon": "🏊", "sort_order": 4},
        {"name": "Теннис", "icon": "🎾", "sort_order": 5},
        {"name": "Хоккей", "icon": "🏒", "sort_order": 6},
        {"name": "Гимнастика", "icon": "🤸", "sort_order": 7},
        {"name": "Борьба", "icon": "🤼", "sort_order": 8},
        {"name": "Бокс", "icon": "🥊", "sort_order": 9},
        {"name": "Легкая атлетика", "icon": "🏃", "sort_order": 10},
        {"name": "Тяжелая атлетика", "icon": "🏋️", "sort_order": 11},
        {"name": "Фитнес", "icon": "💪", "sort_order": 12},
    ]
    
    print("Creating sports...")
    for sport_data in sports_data:
        existing = await sport_repo.find_by_name(sport_data["name"])
        if not existing:
            sport = Sport(**sport_data)
            await sport_repo.create(sport)
            print(f"Created sport: {sport.name}")
    
    # Sample FOKs
    foks_data = [
        {
            "name": "Спортивный комплекс 'Олимп'",
            "district": "Центральный район",
            "address": "ул. Спортивная, 1",
            "description": "Современный спортивный комплекс с бассейном и тренажерным залом",
            "sports": ["Плавание", "Фитнес", "Волейбол"],
            "contacts": [
                {"type": "phone", "value": "+7 (495) 123-45-67", "is_primary": True},
                {"type": "email", "value": "olimp@sport.ru"}
            ],
            "working_hours": "Пн-Вс: 06:00-23:00",
            "featured": True
        },
        {
            "name": "ФОК 'Динамо'",
            "district": "Северный район", 
            "address": "пр. Ленина, 45",
            "description": "Физкультурно-оздоровительный комплекс с универсальным игровым залом",
            "sports": ["Баскетбол", "Волейбол", "Футбол"],
            "contacts": [
                {"type": "phone", "value": "+7 (495) 234-56-78", "is_primary": True}
            ],
            "working_hours": "Пн-Пт: 07:00-22:00, Сб-Вс: 08:00-21:00"
        },
        {
            "name": "Центр единоборств 'Боец'",
            "district": "Южный район",
            "address": "ул. Победы, 12",
            "description": "Специализированный центр для занятий единоборствами",
            "sports": ["Бокс", "Борьба", "Фитнес"],
            "contacts": [
                {"type": "phone", "value": "+7 (495) 345-67-89", "is_primary": True},
                {"type": "website", "value": "https://boec-sport.ru"}
            ],
            "working_hours": "Пн-Вс: 08:00-22:00"
        },
        {
            "name": "Легкоатлетический манеж",
            "district": "Восточный район",
            "address": "ул. Стадионная, 8",
            "description": "Манеж для занятий легкой атлетикой с беговыми дорожками",
            "sports": ["Легкая атлетика", "Фитнес"],
            "contacts": [
                {"type": "phone", "value": "+7 (495) 456-78-90", "is_primary": True}
            ],
            "working_hours": "Пн-Пт: 06:00-23:00, Сб-Вс: 07:00-22:00",
            "featured": True
        },
        {
            "name": "Теннисный центр 'Корт'",
            "district": "Западный район",
            "address": "ул. Теннисная, 5",
            "description": "Современные теннисные корты для игры круглый год",
            "sports": ["Теннис"],
            "contacts": [
                {"type": "phone", "value": "+7 (495) 567-89-01", "is_primary": True},
                {"type": "email", "value": "info@kort-tennis.ru"}
            ],
            "working_hours": "Пн-Вс: 07:00-23:00"
        },
        {
            "name": "Ледовый дворец 'Кристалл'",
            "district": "Ленинский район",
            "address": "пр. Мира, 33",
            "description": "Ледовая арена для хоккея и фигурного катания",
            "sports": ["Хоккей"],
            "contacts": [
                {"type": "phone", "value": "+7 (495) 678-90-12", "is_primary": True}
            ],
            "working_hours": "Пн-Вс: 06:00-24:00"
        }
    ]
    
    print("Creating FOKs...")
    for fok_data in foks_data:
        # Check if FOK already exists
        existing_foks = await fok_repo.get_by_district(fok_data["district"])
        exists = any(fok.name == fok_data["name"] for fok in existing_foks)
        
        if not exists:
            fok = FOK(**fok_data)
            await fok_repo.create(fok)
            print(f"Created FOK: {fok.name}")
    
    print("Sample data initialization completed!")


if __name__ == "__main__":
    asyncio.run(init_sample_data())