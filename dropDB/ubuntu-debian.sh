#!/bin/bash

# Stop the MySQL service
sudo systemctl stop mysql

# Remove MySQL packages
sudo apt-get remove -y mysql-server
sudo apt-get purge -y mysql-server
sudo apt-get autoremove -y

# Remove configuration files
sudo rm -rf /etc/mysql/
sudo rm -rf /var/lib/mysql/

echo "MySQL has been completely uninstalled."