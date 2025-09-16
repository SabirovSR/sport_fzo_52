#!/usr/bin/env python3
"""
Admin tools for managing the bot
"""
import asyncio
import sys
import os
from typing import Optional

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database.connection import init_database
from app.database.repositories import user_repo
from app.models import User
from app.config import settings


async def make_admin(telegram_id: int, is_super_admin: bool = False):
    """Make user an admin"""
    await init_database()
    
    user = await user_repo.find_by_telegram_id(telegram_id)
    if not user:
        print(f"User with Telegram ID {telegram_id} not found")
        return
    
    user.is_admin = True
    if is_super_admin:
        user.is_super_admin = True
    
    await user_repo.update(user)
    
    admin_type = "super admin" if is_super_admin else "admin"
    print(f"User {user.display_name} ({telegram_id}) is now an {admin_type}")


async def remove_admin(telegram_id: int):
    """Remove admin privileges from user"""
    await init_database()
    
    user = await user_repo.find_by_telegram_id(telegram_id)
    if not user:
        print(f"User with Telegram ID {telegram_id} not found")
        return
    
    user.is_admin = False
    user.is_super_admin = False
    await user_repo.update(user)
    
    print(f"Admin privileges removed from {user.display_name} ({telegram_id})")


async def list_admins():
    """List all admins"""
    await init_database()
    
    admins = await user_repo.get_admins()
    super_admins = await user_repo.get_super_admins()
    
    print("=== SUPER ADMINS ===")
    for admin in super_admins:
        print(f"- {admin.display_name} (@{admin.username or 'N/A'}) - {admin.telegram_id}")
    
    print("\n=== ADMINS ===")
    for admin in admins:
        if not admin.is_super_admin:
            print(f"- {admin.display_name} (@{admin.username or 'N/A'}) - {admin.telegram_id}")
    
    print(f"\nConfigured super admin IDs: {settings.super_admin_ids_list}")


async def get_user_info(telegram_id: int):
    """Get user information"""
    await init_database()
    
    user = await user_repo.find_by_telegram_id(telegram_id)
    if not user:
        print(f"User with Telegram ID {telegram_id} not found")
        return
    
    print(f"=== USER INFO ===")
    print(f"Name: {user.display_name}")
    print(f"Username: @{user.username or 'N/A'}")
    print(f"Telegram ID: {user.telegram_id}")
    print(f"Phone: {user.phone or 'N/A'}")
    print(f"Registration completed: {user.registration_completed}")
    print(f"Phone shared: {user.phone_shared}")
    print(f"Is admin: {user.is_admin}")
    print(f"Is super admin: {user.is_super_admin}")
    print(f"Is blocked: {user.is_blocked}")
    print(f"Total applications: {user.total_applications}")
    print(f"Created: {user.created_at}")
    print(f"Last activity: {user.last_activity or 'N/A'}")


async def list_users(limit: int = 50):
    """List recent users"""
    await init_database()
    
    from app.database.connection import get_database
    db = await get_database()
    
    cursor = db.users.find({}).sort("created_at", -1).limit(limit)
    users = [User(**doc) async for doc in cursor]
    
    print(f"=== RECENT {len(users)} USERS ===")
    for user in users:
        status = []
        if user.is_super_admin:
            status.append("SUPER_ADMIN")
        elif user.is_admin:
            status.append("ADMIN")
        if user.is_blocked:
            status.append("BLOCKED")
        if not user.registration_completed:
            status.append("INCOMPLETE")
        
        status_str = f" [{', '.join(status)}]" if status else ""
        print(f"- {user.display_name} (@{user.username or 'N/A'}) - {user.telegram_id}{status_str}")


async def block_user(telegram_id: int):
    """Block user"""
    await init_database()
    
    user = await user_repo.find_by_telegram_id(telegram_id)
    if not user:
        print(f"User with Telegram ID {telegram_id} not found")
        return
    
    user.is_blocked = True
    await user_repo.update(user)
    
    print(f"User {user.display_name} ({telegram_id}) has been blocked")


async def unblock_user(telegram_id: int):
    """Unblock user"""
    await init_database()
    
    user = await user_repo.find_by_telegram_id(telegram_id)
    if not user:
        print(f"User with Telegram ID {telegram_id} not found")
        return
    
    user.is_blocked = False
    await user_repo.update(user)
    
    print(f"User {user.display_name} ({telegram_id}) has been unblocked")


async def get_stats():
    """Get bot statistics"""
    await init_database()
    
    from app.database.repositories import application_repo, fok_repo
    from datetime import datetime, timedelta
    
    total_users = await user_repo.count()
    active_users_30d = await user_repo.get_active_users_count(30)
    active_users_7d = await user_repo.get_active_users_count(7)
    
    total_applications = await application_repo.count()
    apps_30d = await application_repo.get_statistics(30)
    
    total_foks = await fok_repo.count({"is_active": True})
    
    print("=== BOT STATISTICS ===")
    print(f"Total users: {total_users}")
    print(f"Active users (30d): {active_users_30d}")
    print(f"Active users (7d): {active_users_7d}")
    print(f"Total applications: {total_applications}")
    print(f"Total active FOKs: {total_foks}")
    
    if apps_30d:
        print("\nApplications by status (30d):")
        for status, count in apps_30d.items():
            print(f"  {status}: {count}")


def main():
    """Main CLI function"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python admin_tools.py make_admin <telegram_id> [super]")
        print("  python admin_tools.py remove_admin <telegram_id>")
        print("  python admin_tools.py list_admins")
        print("  python admin_tools.py user_info <telegram_id>")
        print("  python admin_tools.py list_users [limit]")
        print("  python admin_tools.py block_user <telegram_id>")
        print("  python admin_tools.py unblock_user <telegram_id>")
        print("  python admin_tools.py stats")
        return
    
    command = sys.argv[1]
    
    if command == "make_admin":
        if len(sys.argv) < 3:
            print("Usage: python admin_tools.py make_admin <telegram_id> [super]")
            return
        telegram_id = int(sys.argv[2])
        is_super = len(sys.argv) > 3 and sys.argv[3] == "super"
        asyncio.run(make_admin(telegram_id, is_super))
    
    elif command == "remove_admin":
        if len(sys.argv) < 3:
            print("Usage: python admin_tools.py remove_admin <telegram_id>")
            return
        telegram_id = int(sys.argv[2])
        asyncio.run(remove_admin(telegram_id))
    
    elif command == "list_admins":
        asyncio.run(list_admins())
    
    elif command == "user_info":
        if len(sys.argv) < 3:
            print("Usage: python admin_tools.py user_info <telegram_id>")
            return
        telegram_id = int(sys.argv[2])
        asyncio.run(get_user_info(telegram_id))
    
    elif command == "list_users":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        asyncio.run(list_users(limit))
    
    elif command == "block_user":
        if len(sys.argv) < 3:
            print("Usage: python admin_tools.py block_user <telegram_id>")
            return
        telegram_id = int(sys.argv[2])
        asyncio.run(block_user(telegram_id))
    
    elif command == "unblock_user":
        if len(sys.argv) < 3:
            print("Usage: python admin_tools.py unblock_user <telegram_id>")
            return
        telegram_id = int(sys.argv[2])
        asyncio.run(unblock_user(telegram_id))
    
    elif command == "stats":
        asyncio.run(get_stats())
    
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()