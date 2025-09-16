#!/bin/bash

# FOK Bot Monitoring Script

show_status() {
    echo "🔍 FOK Bot Status Check"
    echo "======================"
    
    # Service status
    echo "📋 Service Status:"
    docker-compose -f docker-compose.prod.yml ps
    echo ""
    
    # Health checks
    echo "🏥 Health Checks:"
    
    # MongoDB
    if docker-compose -f docker-compose.prod.yml exec -T mongodb mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
        echo "✅ MongoDB: Healthy"
    else
        echo "❌ MongoDB: Unhealthy"
    fi
    
    # Redis
    if docker-compose -f docker-compose.prod.yml exec -T redis redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis: Healthy"
    else
        echo "❌ Redis: Unhealthy"
    fi
    
    # Bot health endpoint
    if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Bot API: Healthy"
    else
        echo "❌ Bot API: Unhealthy"
    fi
    
    # Celery worker
    if docker-compose -f docker-compose.prod.yml exec -T celery_worker celery -A app.tasks.celery_app inspect ping > /dev/null 2>&1; then
        echo "✅ Celery Worker: Healthy"
    else
        echo "❌ Celery Worker: Unhealthy"
    fi
    
    echo ""
}

show_stats() {
    echo "📊 System Statistics:"
    
    # Database stats
    echo "💾 Database:"
    USER_COUNT=$(docker-compose -f docker-compose.prod.yml exec -T mongodb mongosh fok_bot_prod --quiet --eval "db.users.countDocuments({})" 2>/dev/null || echo "N/A")
    FOK_COUNT=$(docker-compose -f docker-compose.prod.yml exec -T mongodb mongosh fok_bot_prod --quiet --eval "db.foks.countDocuments({})" 2>/dev/null || echo "N/A")
    APP_COUNT=$(docker-compose -f docker-compose.prod.yml exec -T mongodb mongosh fok_bot_prod --quiet --eval "db.applications.countDocuments({})" 2>/dev/null || echo "N/A")
    
    echo "  Users: $USER_COUNT"
    echo "  FOKs: $FOK_COUNT"
    echo "  Applications: $APP_COUNT"
    
    # Container stats
    echo ""
    echo "🐳 Container Resources:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" $(docker-compose -f docker-compose.prod.yml ps -q) 2>/dev/null || echo "Unable to get container stats"
    
    echo ""
}

show_logs() {
    local service="$1"
    local lines="${2:-50}"
    
    if [ -z "$service" ]; then
        echo "📜 Recent logs (all services):"
        docker-compose -f docker-compose.prod.yml logs --tail="$lines"
    else
        echo "📜 Recent logs for $service:"
        docker-compose -f docker-compose.prod.yml logs --tail="$lines" "$service"
    fi
}

show_errors() {
    echo "🚨 Recent errors:"
    docker-compose -f docker-compose.prod.yml logs --tail=100 | grep -i error || echo "No recent errors found"
}

restart_service() {
    local service="$1"
    
    if [ -z "$service" ]; then
        echo "Usage: $0 restart <service_name>"
        echo "Available services: bot, celery_worker, celery_beat, mongodb, redis"
        return 1
    fi
    
    echo "🔄 Restarting $service..."
    docker-compose -f docker-compose.prod.yml restart "$service"
    echo "✅ $service restarted"
}

case "$1" in
    "status"|"")
        show_status
        ;;
    "stats")
        show_stats
        ;;
    "logs")
        show_logs "$2" "$3"
        ;;
    "errors")
        show_errors
        ;;
    "restart")
        restart_service "$2"
        ;;
    "full")
        show_status
        echo ""
        show_stats
        echo ""
        show_errors
        ;;
    *)
        echo "Usage: $0 {status|stats|logs|errors|restart|full}"
        echo ""
        echo "Commands:"
        echo "  status          - Show service status and health checks"
        echo "  stats           - Show system statistics"
        echo "  logs [service]  - Show recent logs"
        echo "  errors          - Show recent errors"
        echo "  restart <svc>   - Restart a service"
        echo "  full            - Show all information"
        exit 1
        ;;
esac