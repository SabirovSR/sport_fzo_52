#!/bin/bash

# FOK Bot Enterprise Monitoring Script

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_service_health() {
    local service_name=$1
    local health_url=$2
    
    if curl -f -s "$health_url" > /dev/null 2>&1; then
        print_success "$service_name is healthy"
        return 0
    else
        print_error "$service_name is unhealthy"
        return 1
    fi
}

show_overview() {
    print_header "FOK Bot Enterprise - System Overview"
    
    echo "🕐 $(date)"
    echo ""
    
    # Service status
    echo "📋 Service Status:"
    docker-compose -f docker-compose.enterprise.yml ps --format "table {{.Name}}\t{{.State}}\t{{.Status}}"
    echo ""
    
    # Health checks
    echo "🏥 Health Checks:"
    check_service_health "HAProxy" "http://localhost:8404/stats"
    check_service_health "Grafana" "http://localhost:3000/api/health"
    check_service_health "Prometheus" "http://localhost:9090/-/healthy"
    
    # Check bot instances
    for i in {1..3}; do
        if docker-compose -f docker-compose.enterprise.yml exec -T bot-$i curl -f -s http://localhost:800$i/health > /dev/null 2>&1; then
            print_success "Bot Instance $i is healthy"
        else
            print_error "Bot Instance $i is unhealthy"
        fi
    done
    echo ""
}

show_infrastructure() {
    print_header "Infrastructure Status"
    
    # MongoDB Replica Set
    echo "🍃 MongoDB Replica Set:"
    if docker-compose -f docker-compose.enterprise.yml exec -T mongodb-primary mongosh --quiet --eval "
        try {
            var status = rs.status();
            print('Replica Set: ' + status.set);
            status.members.forEach(function(member) {
                print('  ' + member.name + ' - ' + member.stateStr + ' (health: ' + member.health + ')');
            });
        } catch(e) {
            print('Error: ' + e.message);
        }
    " 2>/dev/null; then
        echo ""
    else
        print_error "Could not get MongoDB replica set status"
    fi
    
    # Redis Cluster
    echo "🔴 Redis Cluster:"
    if docker-compose -f docker-compose.enterprise.yml exec -T redis-node-1 redis-cli cluster nodes 2>/dev/null | head -6; then
        echo ""
    else
        print_error "Could not get Redis cluster status"
    fi
}

show_metrics() {
    print_header "Key Metrics"
    
    # System resources
    echo "💻 System Resources:"
    echo "CPU Usage:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" $(docker-compose -f docker-compose.enterprise.yml ps -q) 2>/dev/null | head -10
    echo ""
    
    # Application metrics (if accessible)
    echo "📊 Application Metrics:"
    if curl -s http://localhost:9090/api/v1/query?query=fok_bot_active_users_total 2>/dev/null | grep -q "success"; then
        ACTIVE_USERS=$(curl -s "http://localhost:9090/api/v1/query?query=fok_bot_active_users_total" | jq -r '.data.result[0].value[1]' 2>/dev/null || echo "N/A")
        echo "Active Users: $ACTIVE_USERS"
        
        TOTAL_APPS=$(curl -s "http://localhost:9090/api/v1/query?query=fok_bot_applications_created_total" | jq -r '.data.result[0].value[1]' 2>/dev/null || echo "N/A")
        echo "Total Applications: $TOTAL_APPS"
    else
        print_warning "Metrics not available (Prometheus might be starting up)"
    fi
    echo ""
}

show_logs() {
    local service=$1
    local lines=${2:-50}
    
    if [ -z "$service" ]; then
        print_header "Recent Logs (All Services)"
        docker-compose -f docker-compose.enterprise.yml logs --tail="$lines" --timestamps
    else
        print_header "Recent Logs: $service"
        docker-compose -f docker-compose.enterprise.yml logs --tail="$lines" --timestamps "$service"
    fi
}

show_alerts() {
    print_header "Active Alerts"
    
    if curl -s http://localhost:9093/api/v1/alerts 2>/dev/null | jq -r '.data[] | select(.status.state=="active") | .labels.alertname + " - " + .annotations.summary' 2>/dev/null; then
        echo ""
    else
        print_success "No active alerts"
    fi
}

restart_service() {
    local service=$1
    
    if [ -z "$service" ]; then
        echo "Usage: $0 restart <service_name>"
        echo "Available services:"
        docker-compose -f docker-compose.enterprise.yml config --services
        return 1
    fi
    
    print_header "Restarting Service: $service"
    docker-compose -f docker-compose.enterprise.yml restart "$service"
    print_success "$service restarted"
}

scale_service() {
    local service=$1
    local replicas=$2
    
    if [ -z "$service" ] || [ -z "$replicas" ]; then
        echo "Usage: $0 scale <service_name> <replicas>"
        return 1
    fi
    
    print_header "Scaling Service: $service to $replicas replicas"
    docker-compose -f docker-compose.enterprise.yml up -d --scale "$service=$replicas"
    print_success "$service scaled to $replicas replicas"
}

show_urls() {
    print_header "Service URLs"
    
    echo "🌐 Web Interfaces:"
    echo "• Grafana Dashboard: http://localhost:3000"
    echo "• Prometheus: http://localhost:9090"
    echo "• HAProxy Stats: http://localhost:8404/stats"
    echo "• AlertManager: http://localhost:9093"
    echo ""
    echo "🔌 API Endpoints:"
    echo "• Bot Health: http://localhost/health"
    echo "• Bot Metrics: http://localhost/metrics"
    echo ""
}

backup_system() {
    print_header "Creating System Backup"
    
    # Create backup directory
    BACKUP_DIR="./backups/enterprise_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup MongoDB
    echo "📦 Backing up MongoDB..."
    docker-compose -f docker-compose.enterprise.yml exec -T mongodb-primary mongodump \
        --archive="/tmp/mongodb_backup.gz" --gzip
    docker cp fok_bot_mongodb_primary:/tmp/mongodb_backup.gz "$BACKUP_DIR/mongodb.gz"
    
    # Backup configurations
    echo "⚙️  Backing up configurations..."
    tar -czf "$BACKUP_DIR/configs.tar.gz" \
        .env.prod \
        docker-compose.enterprise.yml \
        haproxy/ \
        monitoring/ \
        2>/dev/null || true
    
    print_success "Backup created: $BACKUP_DIR"
}

case "$1" in
    "overview"|"")
        show_overview
        ;;
    "infra"|"infrastructure")
        show_infrastructure
        ;;
    "metrics")
        show_metrics
        ;;
    "logs")
        show_logs "$2" "$3"
        ;;
    "alerts")
        show_alerts
        ;;
    "restart")
        restart_service "$2"
        ;;
    "scale")
        scale_service "$2" "$3"
        ;;
    "urls")
        show_urls
        ;;
    "backup")
        backup_system
        ;;
    "full")
        show_overview
        echo ""
        show_infrastructure
        echo ""
        show_metrics
        echo ""
        show_alerts
        ;;
    *)
        echo "Usage: $0 {overview|infra|metrics|logs|alerts|restart|scale|urls|backup|full}"
        echo ""
        echo "Commands:"
        echo "  overview          - Show system overview (default)"
        echo "  infra            - Show infrastructure status"
        echo "  metrics          - Show key metrics"
        echo "  logs [service]   - Show recent logs"
        echo "  alerts           - Show active alerts"
        echo "  restart <svc>    - Restart a service"
        echo "  scale <svc> <n>  - Scale a service"
        echo "  urls             - Show service URLs"
        echo "  backup           - Create system backup"
        echo "  full             - Show all information"
        exit 1
        ;;
esac