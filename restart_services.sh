#!/bin/bash

SERVICES=("platform.service" "platform_celery.service")

for SERVICE in "${SERVICES[@]}"; do
    echo "Restarting $SERVICE..."
    sudo systemctl restart $SERVICE

    # Check if the service restarted successfully
    if systemctl is-active --quiet $SERVICE; then
        echo "$SERVICE restarted successfully."
    else
        echo "Failed to restart $SERVICE."
    fi
done
