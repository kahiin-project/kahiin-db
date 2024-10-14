#!/bin/bash

# Update packages
sudo apt-get update

# Install MySQL
sudo apt-get install -y mysql-server

# Clean up any previous MySQL installations
sudo apt autoremove --purge -y mysql-server* mariadb-server*
sudo rm -rf /var/lib/mysql /etc/mysql/
sudo mkdir -p /etc/mysql/conf.d

# Reinstall MySQL server
sudo apt install -y mysql-server

# Start the MySQL service
sudo systemctl start mysql

# Function to validate database name
validate_db_name() {
    if [[ "$1" =~ ^[a-zA-Z0-9_]+$ ]]; then
        return 0
    else
        return 1
    fi
}

# Create a new database
while true; do
    read -p "Database name: " db_name
    if validate_db_name "$db_name"; then
        sudo mysql -e "CREATE DATABASE $db_name;"
        break
    else
        echo "Invalid database name. Only alphanumeric characters and underscores are allowed."
    fi
done

# Create a new user
read -p "Username: " user_name
read -p "Password: " user_pass
sudo mysql -e "CREATE USER '$user_name'@'localhost' IDENTIFIED BY '$user_pass';"
sudo mysql -e "GRANT ALL PRIVILEGES ON $db_name.* TO '$user_name'@'localhost';"

echo "MySQL has been successfully installed and configured!"