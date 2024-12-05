#!/bin/bash

# Step 1: Change current directory to /home/marco/inx_platform
cd /home/marco/inx_platform || { echo "Directory /home/marco/inx_platform not found."; exit 1; }

# Step 2: Pull the latest changes from the repository
echo "Pulling the latest changes from the repository..."
git pull || { echo "Failed to pull the latest changes."; exit 1; }

# Step 3: Activate the Python virtual environment
echo "Activating the Python virtual environment..."
source venv/bin/activate || { echo "Failed to activate the virtual environment."; exit 1; }

# Step 3.1: Install the required Python packages
echo "Installing the required Python packages..."
pip install -r requirements.txt || { echo "Failed to install the required Python packages."; exit 1; }

# Step 4: Run database migrations
echo "Running database migrations..."
python manage.py migrate || { echo "Failed to run database migrations."; exit 1; }

# Step 5: Restart services
SERVICES=("platform.service" "platform_celery.service" "platform_beat.service" "platform_flower.service")
echo $SERVICES

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
echo "Script completed."
