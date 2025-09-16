#!/bin/bash

# FOK Bot Enterprise Deployment Script
# Разворачивает полную enterprise инфраструктуру с мониторингом и высокой доступностью

set -e

echo "🚀 Starting FOK Bot Enterprise deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
print_status "Checking prerequisites..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env.prod exists
if [ ! -f ".env.prod" ]; then
    print_error ".env.prod file not found! Please create it from .env.prod.example"
    exit 1
fi

print_success "Prerequisites check passed"

# Create necessary directories
print_status "Creating directories..."
mkdir -p logs exports backups ssl

# SSL certificates check
if [ ! -f "ssl/cert.pem" ] || [ ! -f "ssl/key.pem" ]; then
    print_warning "SSL certificates not found. Creating self-signed certificates..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout ssl/key.pem \
        -out ssl/cert.pem \
        -subj "/C=RU/ST=State/L=City/O=Organization/CN=localhost"
    print_success "Self-signed SSL certificates created"
fi

# Create networks
print_status "Creating Docker networks..."
docker network create fok_network 2>/dev/null || true
docker network create monitoring_network 2>/dev/null || true

# Stop existing containers
print_status "Stopping existing containers..."
docker-compose -f docker-compose.enterprise.yml down || true

# Pull latest images
print_status "Pulling latest Docker images..."
docker-compose -f docker-compose.enterprise.yml pull

# Build application images
print_status "Building application images..."
docker-compose -f docker-compose.enterprise.yml build

# Start infrastructure services first
print_status "Starting infrastructure services..."

# Start MongoDB replica set
print_status "Starting MongoDB replica set..."
docker-compose -f docker-compose.enterprise.yml up -d mongodb-primary mongodb-secondary1 mongodb-secondary2

# Wait for MongoDB to be ready
print_status "Waiting for MongoDB to be ready..."
sleep 30

# Initialize MongoDB replica set
print_status "Initializing MongoDB replica set..."
docker-compose -f docker-compose.enterprise.yml exec -T mongodb-primary mongosh --eval "
rs.initiate({
  _id: 'fok_replica',
  members: [
    { _id: 0, host: 'mongodb-primary:27017', priority: 2 },
    { _id: 1, host: 'mongodb-secondary1:27017', priority: 1 },
    { _id: 2, host: 'mongodb-secondary2:27017', priority: 1 }
  ]
});
" || print_warning "Replica set might already be initialized"

# Start Redis cluster
print_status "Starting Redis cluster..."
docker-compose -f docker-compose.enterprise.yml up -d redis-node-1 redis-node-2 redis-node-3 redis-node-4 redis-node-5 redis-node-6

# Wait for Redis nodes to be ready
print_status "Waiting for Redis nodes to be ready..."
sleep 20

# Initialize Redis cluster
print_status "Initializing Redis cluster..."
docker-compose -f docker-compose.enterprise.yml exec -T redis-node-1 redis-cli --cluster create \
    redis-node-1:7001 redis-node-2:7002 redis-node-3:7003 \
    redis-node-4:7004 redis-node-5:7005 redis-node-6:7006 \
    --cluster-replicas 1 --cluster-yes || print_warning "Redis cluster might already be initialized"

# Start monitoring stack
print_status "Starting monitoring stack..."
docker-compose -f docker-compose.enterprise.yml up -d prometheus grafana loki promtail alertmanager node_exporter cadvisor mongodb_exporter redis_exporter

# Start application services
print_status "Starting application services..."
docker-compose -f docker-compose.enterprise.yml up -d bot-1 bot-2 bot-3 celery-worker-1 celery-worker-2 celery-beat

# Start load balancer
print_status "Starting load balancer..."
docker-compose -f docker-compose.enterprise.yml up -d haproxy

# Wait for services to be ready
print_status "Waiting for all services to be ready..."
sleep 60

# Health checks
print_status "Performing health checks..."

# Check HAProxy
if curl -f -s http://localhost:8404/stats > /dev/null; then
    print_success "HAProxy is healthy"
else
    print_error "HAProxy health check failed"
fi

# Check Grafana
if curl -f -s http://localhost:3000/api/health > /dev/null; then
    print_success "Grafana is healthy"
else
    print_error "Grafana health check failed"
fi

# Check Prometheus
if curl -f -s http://localhost:9090/-/healthy > /dev/null; then
    print_success "Prometheus is healthy"
else
    print_error "Prometheus health check failed"
fi

# Check bot instances
for i in {1..3}; do
    if docker-compose -f docker-compose.enterprise.yml exec -T bot-$i curl -f -s http://localhost:800$i/health > /dev/null; then
        print_success "Bot instance $i is healthy"
    else
        print_error "Bot instance $i health check failed"
    fi
done

# Initialize sample data
print_status "Initializing sample data..."
docker-compose -f docker-compose.enterprise.yml exec -T bot-1 python scripts/init_data.py

# Show running services
print_status "Checking running services..."
docker-compose -f docker-compose.enterprise.yml ps

# Show service URLs
echo ""
print_success "🎉 Enterprise deployment completed!"
echo ""
echo "📊 Service URLs:"
echo "• Grafana Dashboard: http://localhost:3000 (admin/admin123)"
echo "• Prometheus: http://localhost:9090"
echo "• HAProxy Stats: http://localhost:8404/stats"
echo "• AlertManager: http://localhost:9093"
echo ""
echo "🔧 Management Commands:"
echo "• View logs: docker-compose -f docker-compose.enterprise.yml logs -f"
echo "• Monitor services: ./scripts/monitor-enterprise.sh"
echo "• Create admin: docker-compose -f docker-compose.enterprise.yml exec bot-1 python scripts/admin_tools.py make_admin YOUR_TELEGRAM_ID super"
echo ""
echo "📈 Monitoring:"
echo "• 3 Bot instances with load balancing"
echo "• MongoDB replica set (1 primary + 2 secondaries)"
echo "• Redis cluster (6 nodes)"
echo "• Full observability stack (Prometheus + Grafana + Loki)"
echo "• Automated alerting"
echo ""
print_warning "Don't forget to:"
print_warning "1. Set up your bot webhook URL"
print_warning "2. Create admin users"
print_warning "3. Configure SSL certificates for production"
print_warning "4. Set up backup strategy"