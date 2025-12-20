#!/bin/bash
# Zeus System Monitor Script
# Usage: ./health_check.sh

echo "Starting Zeus Infrastructure Check..."

# Check memory usage
echo "Checking Memory Usage..."
free -h

# Check Disk Space
echo "Checking Disk Space..."
df -h

# Check if Docker daemon is active
if systemctl is-active --quiet docker; then
    echo "Docker is running."
else
    echo "ALERT: Docker is NOT running."
fi

echo "Zeus Check Complete."
