# create the server with ubuntu 22.04 LTS
apt-get update && DEBIAN_FRONTEND=noninteractive apt-get -y -o Dpkg::Options::="--force-confnew" upgrade

## create a non-root user as marco
```
USERNAME=marco
PASSWORD=dellaBiella2!

useradd -m -d /home/$USERNAME -U -r -s /bin/bash $USERNAME
usermod -aG sudo $USERNAME


# Set the password for the user
echo "${USERNAME}:${PASSWORD}" | chpasswd

sudo rsync --archive --chown=$USERNAME:$USERNAME ~/.ssh /home/$USERNAME
```
log in as root
```
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update
apt-get -y upgrade
```
log out

log in as marco
```
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18 mssql-tools18
sudo ACCEPT_EULA=Y apt-get install -y mssql-tools18
echo 'export PATH="$PATH:/opt/mssql-tools18/bin"' >> ~/.bashrc
source ~/.bashrc
sudo apt-get install -y unixodbc-dev
```

test connection with


install pyenv
```
sudo apt install -y make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev python3-openssl git

curl https://pyenv.run | bash

echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo -e 'if command -v pyenv 1>/dev/null 2>&1; then\n eval "$(pyenv init -)"\nfi' >> ~/.bashrc
exec "$SHELL"
```

Set up the global python
```
pyenv install 3.11.4
pyenv global 3.11.4
```
Adding the server ssh key to github. First, generate the key.
```
ssh-keygen -t rsa -b 4096 -C "marcozanella@gmail.com"
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_rsa
cat ~/.ssh/id_rsa.pub
```

## Clone the repository from Github on the server
```
git clone git@github.com:marcozanella/inx_platform.git
```

### Create a Python virtual environment
```
python -m venv venv
source venv/bin/activate
```
### Install all requirements
```
pip install -r requirements.txt
```


Edit and prepare the .env for production
```
mv '.env prod' .env
nano .env
```

## Run server
to run with gunicorn
```
gunicorn -b 0.0.0.0:8000 django_inx_platform.wsgi:application
daphne --bind 0.0.0.0 --port 21013 django_inx_platform.asgi:application
```