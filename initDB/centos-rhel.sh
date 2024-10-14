#!/bin/bash

# Update packages
sudo yum update -y

# Install MySQL
sudo yum install -y mysql-server

# Start the MySQL service
sudo systemctl start mysqld

# Clean up any previous MySQL installations
sudo yum remove -y mysql-server*
sudo rm -rf /var/lib/mysql /etc/my.cnf
sudo mkdir -p /etc/my.cnf.d

# Reinstall MySQL server
sudo yum install -y mysql-server

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
read -s -p "Password: " user_pass
echo