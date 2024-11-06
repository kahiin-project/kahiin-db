#!/bin/bash

# Install MySQL
sudo pacman -S --noconfirm mysql

# Initialize the database
sudo mysql_install_db --user=mysql --basedir=/usr --datadir=/var/lib/mysql

# Start the MySQL service
sudo systemctl start mysqld

# Secure the MySQL installation
sudo mysql_secure_installation

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