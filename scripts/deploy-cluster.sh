#!/bin/bash

# FOK Bot Cluster Deployment Script
set -e

echo "🚀 Starting FOK Bot cluster deployment..."

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

# Check if required files exist
check_requirements() {
    print_status "Checking requirements..."
    
    if [ ! -f ".env.cluster" ]; then
        print_error "Missing .env.cluster file. Please copy .env.cluster.example and configure it."
        exit 1
    fi
    
    if [ ! -f "mongodb-keyfile" ]; then
        print_error "Missing mongodb-keyfile. Run: openssl rand -base64 756 > mongodb-keyfile && chmod 400 mongodb-keyfile"
        exit 1
    fi
    
    # Check Docker and Docker Compose
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    
    print_success "Requirements check passed"
}

# Create necessary directories
create_directories() {
    print_status "Creating directories..."
    
    mkdir -p logs exports backups ssl
    mkdir -p monitoring/{prometheus,grafana,loki,promtail,alertmanager}
    mkdir -p monitoring/grafana/{provisioning/{datasources,dashboards},dashboards}
    mkdir -p redis-cluster haproxy
    
    print_success "Directories created"
}

# Deploy monitoring stack
deploy_monitoring() {
    print_status "Deploying monitoring stack..."
    
    docker-compose -f docker-compose.monitoring.yml up -d
    
    # Wait for services to be ready
    print_status "Waiting for monitoring services to be ready..."
    sleep 30
    
    # Check if services are running
    if docker-compose -f docker-compose.monitoring.yml ps | grep -q "Up"; then
        print_success "Monitoring stack deployed successfully"
        print_status "Grafana: http://localhost:3000 (admin/admin123)"
        print_status "Prometheus: http://localhost:9090"
        print_status "Alertmanager: http://localhost:9093"
    else
        print_error "Failed to deploy monitoring stack"
        exit 1
    fi
}

# Deploy cluster infrastructure
deploy_cluster() {
    print_status "Deploying cluster infrastructure..."
    
    # Build application images
    print_status "Building application images..."
    docker-compose -f docker-compose.cluster.yml build --no-cache
    
    # Start infrastructure services first
    print_status "Starting MongoDB replica set..."
    docker-compose -f docker-compose.cluster.yml up -d mongodb-primary mongodb-secondary-1 mongodb-secondary-2
    
    # Wait for MongoDB replica set to initialize
    print_status "Waiting for MongoDB replica set to initialize..."
    sleep 60
    
    # Initialize replica set
    print_status "Initializing MongoDB replica set..."
    docker-compose -f docker-compose.cluster.yml exec mongodb-primary mongosh --eval "
        try {
            rs.status();
            print('Replica set already initialized');
        } catch (e) {
            print('Initializing replica set...');
            rs.initiate({
                _id: 'fok-replica-set',
                members: [
                    { _id: 0, host: 'mongodb-primary:27017', priority: 2 },
                    { _id: 1, host: 'mongodb-secondary-1:27017', priority: 1 },
                    { _id: 2, host: 'mongodb-secondary-2:27017', priority: 1 }
                ]
            });
            sleep(15000);
            print('Replica set initialized');
        }
    "
    
    # Start Redis cluster
    print_status "Starting Redis cluster..."
    docker-compose -f docker-compose.cluster.yml up -d redis-node-1 redis-node-2 redis-node-3 redis-node-4 redis-node-5 redis-node-6
    
    # Wait for Redis nodes to be ready
    print_status "Waiting for Redis nodes to be ready..."
    sleep 30
    
    # Initialize Redis cluster
    print_status "Initializing Redis cluster..."
    docker-compose -f docker-compose.cluster.yml up -d redis-cluster-init
    
    # Wait for cluster initialization
    sleep 30
    
    # Start application services
    print_status "Starting bot instances..."
    docker-compose -f docker-compose.cluster.yml up -d bot-1 bot-2 bot-3
    
    # Start Celery workers
    print_status "Starting Celery workers..."
    docker-compose -f docker-compose.cluster.yml up -d celery-worker-1 celery-worker-2 celery-beat
    
    # Start load balancer
    print_status "Starting load balancer..."
    docker-compose -f docker-compose.cluster.yml up -d haproxy
    
    print_success "Cluster infrastructure deployed successfully"
}

# Health check
health_check() {
    print_status "Performing health check..."
    
    # Check MongoDB replica set
    print_status "Checking MongoDB replica set..."
    if docker-compose -f docker-compose.cluster.yml exec mongodb-primary mongosh --quiet --eval "rs.status().ok" | grep -q "1"; then
        print_success "MongoDB replica set is healthy"
    else
        print_warning "MongoDB replica set might have issues"
    fi
    
    # Check Redis cluster
    print_status "Checking Redis cluster..."
    if docker-compose -f docker-compose.cluster.yml exec redis-node-1 redis-cli cluster info | grep -q "cluster_state:ok"; then
        print_success "Redis cluster is healthy"
    else
        print_warning "Redis cluster might have issues"
    fi
    
    # Check bot instances
    print_status "Checking bot instances..."
    for i in 1 2 3; do
        if curl -f -s "http://localhost:800$i/health" > /dev/null; then
            print_success "Bot instance $i is healthy"
        else
            print_warning "Bot instance $i might have issues"
        fi
    done
    
    # Check load balancer
    print_status "Checking load balancer..."
    if curl -f -s "http://localhost:8404/stats" > /dev/null; then
        print_success "Load balancer is healthy"
    else
        print_warning "Load balancer might have issues"
    fi
}

# Show status
show_status() {
    print_status "Cluster Status:"
    echo ""
    echo "📊 Monitoring:"
    echo "  - Grafana: http://localhost:3000"
    echo "  - Prometheus: http://localhost:9090"
    echo "  - Alertmanager: http://localhost:9093"
    echo ""
    echo "🤖 Bot Instances:"
    echo "  - Bot 1: http://localhost:8001"
    echo "  - Bot 2: http://localhost:8002"
    echo "  - Bot 3: http://localhost:8003"
    echo ""
    echo "⚖️ Load Balancer:"
    echo "  - HAProxy Stats: http://localhost:8404/stats"
    echo "  - Main Endpoint: http://localhost:80"
    echo ""
    echo "🗄️ Databases:"
    echo "  - MongoDB Primary: localhost:27017"
    echo "  - MongoDB Secondary 1: localhost:27018"
    echo "  - MongoDB Secondary 2: localhost:27019"
    echo ""
    echo "🔄 Redis Cluster:"
    echo "  - Node 1: localhost:6379"
    echo "  - Node 2: localhost:6380"
    echo "  - Node 3: localhost:6381"
    echo "  - Node 4: localhost:6382"
    echo "  - Node 5: localhost:6383"
    echo "  - Node 6: localhost:6384"
    echo ""
}

# Main deployment process
main() {
    print_status "FOK Bot Cluster Deployment"
    print_status "=========================="
    
    check_requirements
    create_directories
    
    # Deploy based on argument
    case "${1:-all}" in
        "monitoring")
            deploy_monitoring
            ;;
        "cluster")
            deploy_cluster
            ;;
        "all")
            deploy_monitoring
            deploy_cluster
            ;;
        "health")
            health_check
            ;;
        "status")
            show_status
            ;;
        *)
            echo "Usage: $0 [monitoring|cluster|all|health|status]"
            echo ""
            echo "  monitoring  - Deploy only monitoring stack"
            echo "  cluster     - Deploy only cluster infrastructure"
            echo "  all         - Deploy everything (default)"
            echo "  health      - Perform health check"
            echo "  status      - Show cluster status"
            exit 1
            ;;
    esac
    
    if [ "${1:-all}" != "health" ] && [ "${1:-all}" != "status" ]; then
        health_check
        show_status
        
        print_success "🎉 FOK Bot cluster deployment completed!"
        print_status "Run './scripts/deploy-cluster.sh status' to see all endpoints"
    fi
}

# Run main function
main "$@"