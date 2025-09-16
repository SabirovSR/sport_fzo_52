#!/bin/bash

# FOK Bot Restore Script

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup_file.gz>"
    echo "Available backups:"
    ls -la backups/fok_bot_backup_*.gz 2>/dev/null || echo "No backups found"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "🔄 Starting restore process..."
echo "📁 Backup file: $BACKUP_FILE"

# Confirm restore
read -p "⚠️  This will overwrite the current database. Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Restore cancelled"
    exit 1
fi

# Stop bot to prevent data corruption
echo "🛑 Stopping bot..."
docker-compose -f docker-compose.prod.yml stop bot celery_worker celery_beat

# Restore MongoDB
echo "📥 Restoring MongoDB..."
docker-compose -f docker-compose.prod.yml exec -T mongodb mongorestore \
    --db fok_bot_prod \
    --archive="/backups/$(basename "$BACKUP_FILE")" \
    --gzip \
    --drop

if [ $? -eq 0 ]; then
    echo "✅ Database restore completed"
else
    echo "❌ Database restore failed"
    exit 1
fi

# Restart services
echo "🚀 Starting services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services
echo "⏳ Waiting for services to start..."
sleep 10

# Verify restore
echo "🔍 Verifying restore..."
USER_COUNT=$(docker-compose -f docker-compose.prod.yml exec -T mongodb mongosh fok_bot_prod --quiet --eval "db.users.countDocuments({})")
FOK_COUNT=$(docker-compose -f docker-compose.prod.yml exec -T mongodb mongosh fok_bot_prod --quiet --eval "db.foks.countDocuments({})")
APP_COUNT=$(docker-compose -f docker-compose.prod.yml exec -T mongodb mongosh fok_bot_prod --quiet --eval "db.applications.countDocuments({})")

echo "📊 Restore verification:"
echo "Users: $USER_COUNT"
echo "FOKs: $FOK_COUNT" 
echo "Applications: $APP_COUNT"

echo "✅ Restore process completed!"