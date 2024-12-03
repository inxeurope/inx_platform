#!/bin/bash

SERVICES=("platform.service" "platform_celery.service" "platform_beat.service")

for SERVICE in "${SERVICES[@]}"; do
    echo "Stopping $SERVICE..."
    sudo systemctl stop $SERVICE

    sudo systemctl stop $service
    if [ $? -eq 0 ]; then
        echo "$service stopped successfully."
    else
        echo "Failed to stop $service."
    fi
done