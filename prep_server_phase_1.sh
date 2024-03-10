#!/bin/bash
USERNAME=marco
PASSWORD=dellaBiella2!

useradd -m -d /home/$USERNAME -U -r -s /bin/bash $USERNAME && usermod -aG sudo $USERNAME


# Set the password for the user
echo "${USERNAME}:${PASSWORD}" | chpasswd

sudo rsync --archive --chown=$USERNAME:$USERNAME ~/.ssh /home/$USERNAME

curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update && DEBIAN_FRONTEND=noninteractive apt-get -y -o Dpkg::Options::="--force-confnew" upgrade

su - marco