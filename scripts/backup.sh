#!/bin/bash

# FOK Bot Backup Script

set -e

BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="fok_bot_backup_${TIMESTAMP}"

echo "📦 Starting backup process..."

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup MongoDB
echo "💾 Backing up MongoDB..."
docker-compose -f docker-compose.prod.yml exec -T mongodb mongodump \
    --db fok_bot_prod \
    --archive="/backups/${BACKUP_NAME}.gz" \
    --gzip

if [ $? -eq 0 ]; then
    echo "✅ MongoDB backup completed: ${BACKUP_NAME}.gz"
else
    echo "❌ MongoDB backup failed"
    exit 1
fi

# Backup application logs
echo "📋 Backing up logs..."
tar -czf "${BACKUP_DIR}/${BACKUP_NAME}_logs.tar.gz" logs/ 2>/dev/null || echo "⚠️  No logs to backup"

# Backup configuration files
echo "⚙️  Backing up configuration..."
tar -czf "${BACKUP_DIR}/${BACKUP_NAME}_config.tar.gz" \
    .env.prod \
    docker-compose.prod.yml \
    nginx.conf \
    2>/dev/null || echo "⚠️  Some config files missing"

# Clean up old backups (keep last 7)
echo "🧹 Cleaning up old backups..."
ls -t "${BACKUP_DIR}"/fok_bot_backup_*.gz 2>/dev/null | tail -n +8 | xargs -r rm
ls -t "${BACKUP_DIR}"/fok_bot_backup_*_logs.tar.gz 2>/dev/null | tail -n +8 | xargs -r rm
ls -t "${BACKUP_DIR}"/fok_bot_backup_*_config.tar.gz 2>/dev/null | tail -n +8 | xargs -r rm

# Show backup info
echo "📊 Backup summary:"
echo "Database backup: ${BACKUP_NAME}.gz ($(du -h "${BACKUP_DIR}/${BACKUP_NAME}.gz" 2>/dev/null | cut -f1 || echo "Unknown size"))"
echo "Total backups: $(ls "${BACKUP_DIR}"/fok_bot_backup_*.gz 2>/dev/null | wc -l)"

echo "✅ Backup process completed!"