#!/bin/bash

# FOK Bot Deployment Script

set -e

echo "🚀 Starting FOK Bot deployment..."

# Check if .env.prod exists
if [ ! -f ".env.prod" ]; then
    echo "❌ .env.prod file not found! Please create it from .env.prod.example"
    exit 1
fi

# Check if SSL certificates exist for production
if [ -f "docker-compose.prod.yml" ] && [ ! -d "ssl" ]; then
    echo "⚠️  SSL certificates not found. Creating self-signed certificates for testing..."
    mkdir -p ssl
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout ssl/key.pem \
        -out ssl/cert.pem \
        -subj "/C=RU/ST=State/L=City/O=Organization/CN=localhost"
    echo "✅ Self-signed SSL certificates created"
fi

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down || true

# Build and start containers
echo "🔨 Building and starting containers..."
docker-compose -f docker-compose.prod.yml up --build -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 30

# Check service health
echo "🔍 Checking service health..."

# Check MongoDB
if docker-compose -f docker-compose.prod.yml exec -T mongodb mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
    echo "✅ MongoDB is healthy"
else
    echo "❌ MongoDB health check failed"
fi

# Check Redis
if docker-compose -f docker-compose.prod.yml exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is healthy"
else
    echo "❌ Redis health check failed"
fi

# Initialize database with sample data
echo "📊 Initializing database with sample data..."
docker-compose -f docker-compose.prod.yml exec -T bot python scripts/init_data.py

# Show running services
echo "📋 Running services:"
docker-compose -f docker-compose.prod.yml ps

# Show logs
echo "📜 Recent logs:"
docker-compose -f docker-compose.prod.yml logs --tail=20

echo "🎉 Deployment completed!"
echo ""
echo "📝 Next steps:"
echo "1. Check logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "2. Create admin user: docker-compose -f docker-compose.prod.yml exec bot python scripts/admin_tools.py make_admin YOUR_TELEGRAM_ID"
echo "3. Set webhook: Set your webhook URL in Telegram Bot API"
echo "4. Monitor: Check service health regularly"