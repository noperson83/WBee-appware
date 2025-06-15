#!/bin/bash
# Service Status Checker - Shows detailed status of all services

echo "🔍 Worker Bee Service Status Check:"
echo "=================================="

# Array of services to check
services=(
    "postgresql"
    "nginx" 
    "redis-server"
    "supervisor"
    "docker"
)

# Function to check service status with colors
check_service() {
    local service=$1
    local status=$(systemctl is-active $service 2>/dev/null)
    local enabled=$(systemctl is-enabled $service 2>/dev/null)
    
    if [ "$status" = "active" ]; then
        echo "✅ $service: ACTIVE ($enabled)"
    elif [ "$status" = "inactive" ]; then
        echo "❌ $service: INACTIVE ($enabled)"
    elif [ "$status" = "failed" ]; then
        echo "🔥 $service: FAILED ($enabled)"
    else
        echo "❓ $service: $status ($enabled)"
    fi
}

# Check each service
for service in "${services[@]}"; do
    check_service $service
done

echo ""
echo "📊 Summary:"
echo "----------"

# Count active services
active_count=0
total_count=${#services[@]}

for service in "${services[@]}"; do
    if systemctl is-active --quiet $service; then
        ((active_count++))
    fi
done

echo "Active: $active_count/$total_count services"

# Show any failed services
echo ""
echo "🔧 Quick Actions:"
echo "----------------"

for service in "${services[@]}"; do
    status=$(systemctl is-active $service 2>/dev/null)
    if [ "$status" != "active" ]; then
        echo "To start $service: sudo systemctl start $service"
        echo "To enable $service: sudo systemctl enable $service"
    fi
done

# Show service logs for failed services
echo ""
echo "📋 Check logs for failed services:"
echo "----------------------------------"
for service in "${services[@]}"; do
    status=$(systemctl is-active $service 2>/dev/null)
    if [ "$status" = "failed" ]; then
        echo "sudo journalctl -u $service --no-pager -n 20"
    fi
done

# Show listening ports
echo ""
echo "🌐 Listening Ports:"
echo "------------------"
if command -v ss >/dev/null 2>&1; then
    echo "Port 80 (HTTP): $(sudo ss -tulpn | grep ':80 ' | wc -l) connections"
    echo "Port 443 (HTTPS): $(sudo ss -tulpn | grep ':443 ' | wc -l) connections"
    echo "Port 5432 (PostgreSQL): $(sudo ss -tulpn | grep ':5432 ' | wc -l) connections"
    echo "Port 6379 (Redis): $(sudo ss -tulpn | grep ':6379 ' | wc -l) connections"
else
    echo "Port 80 (HTTP): $(sudo netstat -tlnp | grep ':80 ' | wc -l) connections"
    echo "Port 443 (HTTPS): $(sudo netstat -tlnp | grep ':443 ' | wc -l) connections"
    echo "Port 5432 (PostgreSQL): $(sudo netstat -tlnp | grep ':5432 ' | wc -l) connections"
    echo "Port 6379 (Redis): $(sudo netstat -tlnp | grep ':6379 ' | wc -l) connections"
fi

# Check if Worker Bee processes are running
echo ""
echo "🐝 Worker Bee Processes:"
echo "------------------------"
if pgrep -f "workerbee" > /dev/null; then
    echo "✅ Worker Bee processes running:"
    ps aux | grep -E "(workerbee|gunicorn|celery)" | grep -v grep
else
    echo "❌ No Worker Bee processes found"
    echo "To start: sudo supervisorctl start workerbee_django"
fi
