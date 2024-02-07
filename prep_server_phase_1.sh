#!/bin/bash
# Create user marco
useradd -m -d /home/marco -U -r -s /bin/bash marco
# Add marco to sudo group
usermod -aG sudo marco
# Set password for marco
echo "dellaBiella2!" | passwd --stdin marco
# Copy SSH keys to marco's home directory
sudo rsync --archive --chown=marco:marco ~/.ssh /home/marco
# Update system packages
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update
apt-get -y upgrade
# Install MS ODBC SQL
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18
sudo ACCEPT_EULA=Y apt-get install -y mssql-tools18

# Edit sudoers file to allow root to switch to marco without password
echo "root    ALL=(marco) NOPASSWD: ALL" >> /etc/sudoers
su - marco

# Add MS SQL tools to PATH
echo 'export PATH="$PATH:/opt/mssql-tools18/bin"' >> ~/.bashrc
source ~/.bashrc
# Install UnixODBC development files
sudo apt-get install -y unixodbc-dev

# Install prerequisites for PyEnv
sudo apt install -y make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev python3-openssl git

# Install PyEnv
curl https://pyenv.run | bash

# Add PyEnv to PATH
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo -e 'if command -v pyenv 1>/dev/null 2>&1; then\n eval "$(pyenv init -)"\nfi' >> ~/.bashrc
exec "$SHELL"
# Install Python 3.11.4
pyenv install 3.11.4
# Set global Python version to 3.11.4
pyenv global 3.11.4
# Generate SSH key for marco
ssh-keygen -t rsa -b 4096 -C "marcozanella@gmail.com"
# Start SSH agent
eval "$(ssh-agent -s)"
# Add SSH key to SSH agent
ssh-add ~/.ssh/id_rsa
# Display SSH public key
cat ~/.ssh/id_rsa.pub
# Display message
echo "This SSH public key must be copied to Github to allow cloning from this server"