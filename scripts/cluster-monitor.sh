#!/bin/bash

# FOK Bot Cluster Monitoring Script
set -e

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
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check service health
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

# Check Docker container status
check_container_status() {
    local container_name=$1
    
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "$container_name.*Up"; then
        print_success "$container_name is running"
        return 0
    else
        print_error "$container_name is not running"
        return 1
    fi
}

# MongoDB replica set status
check_mongodb_replica() {
    print_status "Checking MongoDB Replica Set..."
    
    # Check if primary is running
    if check_container_status "fok_bot_mongodb_primary"; then
        # Check replica set status
        replica_status=$(docker exec fok_bot_mongodb_primary mongosh --quiet --eval "
            try {
                var status = rs.status();
                var primary = status.members.find(m => m.stateStr === 'PRIMARY');
                var secondaries = status.members.filter(m => m.stateStr === 'SECONDARY');
                print('Primary: ' + (primary ? primary.name : 'None'));
                print('Secondaries: ' + secondaries.length);
                print('Total Members: ' + status.members.length);
                print('OK: ' + status.ok);
            } catch (e) {
                print('ERROR: ' + e.message);
            }
        " 2>/dev/null)
        
        if echo "$replica_status" | grep -q "OK: 1"; then
            print_success "MongoDB replica set is healthy"
            echo "$replica_status" | sed 's/^/  /'
        else
            print_error "MongoDB replica set has issues"
            echo "$replica_status" | sed 's/^/  /'
        fi
    fi
}

# Redis cluster status
check_redis_cluster() {
    print_status "Checking Redis Cluster..."
    
    if check_container_status "fok_bot_redis_node_1"; then
        cluster_info=$(docker exec fok_bot_redis_node_1 redis-cli cluster info 2>/dev/null || echo "ERROR")
        cluster_nodes=$(docker exec fok_bot_redis_node_1 redis-cli cluster nodes 2>/dev/null | wc -l || echo "0")
        
        if echo "$cluster_info" | grep -q "cluster_state:ok"; then
            print_success "Redis cluster is healthy"
            echo "  Nodes: $cluster_nodes"
            echo "  State: $(echo "$cluster_info" | grep cluster_state | cut -d: -f2)"
        else
            print_error "Redis cluster has issues"
            echo "$cluster_info" | sed 's/^/  /'
        fi
    fi
}

# Bot instances status
check_bot_instances() {
    print_status "Checking Bot Instances..."
    
    for i in 1 2 3; do
        container_name="fok_bot_$i"
        health_url="http://localhost:800$i/health"
        
        if check_container_status "$container_name" && check_service_health "Bot Instance $i" "$health_url"; then
            # Get additional metrics
            metrics=$(curl -s "$health_url" 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f\"  Status: {data.get('status', 'unknown')}\")
    if 'stats' in data:
        stats = data['stats']
        print(f\"  Users: {stats.get('users', 0)}\")
        print(f\"  Applications: {stats.get('applications', 0)}\")
except:
    print('  Metrics unavailable')
" 2>/dev/null || echo "  Metrics unavailable")
            echo "$metrics"
        fi
    done
}

# Celery workers status
check_celery_workers() {
    print_status "Checking Celery Workers..."
    
    for i in 1 2; do
        container_name="fok_bot_celery_worker_$i"
        if check_container_status "$container_name"; then
            # Check worker status using celery inspect
            worker_status=$(docker exec "$container_name" celery -A app.tasks.celery_app inspect ping 2>/dev/null || echo "ERROR")
            if echo "$worker_status" | grep -q "pong"; then
                print_success "Celery Worker $i is responding"
            else
                print_error "Celery Worker $i is not responding"
            fi
        fi
    done
    
    # Check beat scheduler
    if check_container_status "fok_bot_celery_beat"; then
        if [ -f "celerybeat-schedule" ]; then
            print_success "Celery Beat scheduler is active"
        else
            print_warning "Celery Beat schedule file not found"
        fi
    fi
}

# Load balancer status
check_load_balancer() {
    print_status "Checking Load Balancer..."
    
    if check_container_status "fok_bot_haproxy"; then
        if check_service_health "HAProxy Stats" "http://localhost:8404/stats"; then
            # Get backend status
            backend_status=$(curl -s "http://localhost:8404/stats;csv" 2>/dev/null | grep "bot_webhook" | grep -v "BACKEND" | awk -F',' '{print $2 " - " $18}' || echo "Status unavailable")
            echo "  Backend Status:"
            echo "$backend_status" | sed 's/^/    /'
        fi
    fi
}

# Monitoring stack status
check_monitoring_stack() {
    print_status "Checking Monitoring Stack..."
    
    services=(
        "fok_bot_prometheus:http://localhost:9090/-/healthy"
        "fok_bot_grafana:http://localhost:3000/api/health"
        "fok_bot_loki:http://localhost:3100/ready"
        "fok_bot_alertmanager:http://localhost:9093/-/healthy"
    )
    
    for service in "${services[@]}"; do
        container_name=$(echo "$service" | cut -d: -f1)
        health_url=$(echo "$service" | cut -d: -f2-)
        service_name=$(echo "$container_name" | sed 's/fok_bot_//' | tr '[:lower:]' '[:upper:]')
        
        if check_container_status "$container_name"; then
            check_service_health "$service_name" "$health_url"
        fi
    done
}

# Resource usage
check_resource_usage() {
    print_status "Resource Usage:"
    
    # Docker stats for main containers
    echo "  Container Resource Usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" \
        fok_bot_1 fok_bot_2 fok_bot_3 \
        fok_bot_mongodb_primary fok_bot_redis_node_1 fok_bot_haproxy 2>/dev/null | sed 's/^/    /' || echo "    Stats unavailable"
    
    # Disk usage
    echo "  Disk Usage:"
    df -h . | tail -1 | awk '{print "    Available: " $4 " (" $5 " used)"}' || echo "    Disk stats unavailable"
}

# Application metrics
check_application_metrics() {
    print_status "Application Metrics:"
    
    # Try to get metrics from one of the bot instances
    metrics_data=$(curl -s "http://localhost:8001/metrics" 2>/dev/null || echo "")
    
    if [ -n "$metrics_data" ]; then
        # Extract key metrics
        echo "  HTTP Requests Total:"
        echo "$metrics_data" | grep "^http_requests_total" | head -3 | sed 's/^/    /'
        
        echo "  Telegram Updates:"
        echo "$metrics_data" | grep "^telegram_updates_total" | head -3 | sed 's/^/    /'
        
        echo "  Active Users:"
        echo "$metrics_data" | grep "^active_users_total" | sed 's/^/    /'
    else
        echo "    Metrics unavailable"
    fi
}

# Show cluster overview
show_overview() {
    echo ""
    echo "🚀 FOK Bot Cluster Monitor"
    echo "=========================="
    echo ""
    
    check_mongodb_replica
    echo ""
    
    check_redis_cluster
    echo ""
    
    check_bot_instances
    echo ""
    
    check_celery_workers
    echo ""
    
    check_load_balancer
    echo ""
    
    check_monitoring_stack
    echo ""
    
    check_resource_usage
    echo ""
    
    check_application_metrics
    echo ""
}

# Continuous monitoring mode
continuous_monitor() {
    local interval=${1:-30}
    
    print_status "Starting continuous monitoring (interval: ${interval}s)"
    print_status "Press Ctrl+C to stop"
    
    while true; do
        clear
        show_overview
        echo ""
        echo "Next update in ${interval} seconds... (Ctrl+C to stop)"
        sleep "$interval"
    done
}

# Show logs
show_logs() {
    local service=${1:-all}
    local lines=${2:-100}
    
    case "$service" in
        "bot")
            docker-compose -f docker-compose.cluster.yml logs --tail="$lines" -f bot-1 bot-2 bot-3
            ;;
        "mongodb")
            docker-compose -f docker-compose.cluster.yml logs --tail="$lines" -f mongodb-primary mongodb-secondary-1 mongodb-secondary-2
            ;;
        "redis")
            docker-compose -f docker-compose.cluster.yml logs --tail="$lines" -f redis-node-1 redis-node-2 redis-node-3
            ;;
        "celery")
            docker-compose -f docker-compose.cluster.yml logs --tail="$lines" -f celery-worker-1 celery-worker-2 celery-beat
            ;;
        "haproxy")
            docker-compose -f docker-compose.cluster.yml logs --tail="$lines" -f haproxy
            ;;
        "monitoring")
            docker-compose -f docker-compose.monitoring.yml logs --tail="$lines" -f prometheus grafana loki
            ;;
        "all")
            docker-compose -f docker-compose.cluster.yml logs --tail="$lines" -f
            ;;
        *)
            echo "Unknown service: $service"
            echo "Available services: bot, mongodb, redis, celery, haproxy, monitoring, all"
            exit 1
            ;;
    esac
}

# Main function
main() {
    case "${1:-overview}" in
        "overview"|"status")
            show_overview
            ;;
        "monitor")
            continuous_monitor "${2:-30}"
            ;;
        "logs")
            show_logs "${2:-all}" "${3:-100}"
            ;;
        "mongodb")
            check_mongodb_replica
            ;;
        "redis")
            check_redis_cluster
            ;;
        "bot")
            check_bot_instances
            ;;
        "celery")
            check_celery_workers
            ;;
        "haproxy")
            check_load_balancer
            ;;
        "monitoring")
            check_monitoring_stack
            ;;
        "resources")
            check_resource_usage
            ;;
        "metrics")
            check_application_metrics
            ;;
        *)
            echo "Usage: $0 [command] [options]"
            echo ""
            echo "Commands:"
            echo "  overview     - Show cluster overview (default)"
            echo "  monitor      - Continuous monitoring mode"
            echo "  logs         - Show service logs"
            echo "  mongodb      - Check MongoDB replica set"
            echo "  redis        - Check Redis cluster"
            echo "  bot          - Check bot instances"
            echo "  celery       - Check Celery workers"
            echo "  haproxy      - Check load balancer"
            echo "  monitoring   - Check monitoring stack"
            echo "  resources    - Show resource usage"
            echo "  metrics      - Show application metrics"
            echo ""
            echo "Examples:"
            echo "  $0 monitor 60        - Monitor with 60s interval"
            echo "  $0 logs bot 200      - Show last 200 lines of bot logs"
            echo "  $0 logs mongodb      - Show MongoDB logs"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"