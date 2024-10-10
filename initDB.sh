#!/bin/bash

# Variables
DB_NAME="kahiin-db"
DB_USER="admin"
DB_PASS="password"

# Commandes SQL
SQL_COMMANDS="
CREATE DATABASE IF NOT EXISTS $DB_NAME;
CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASS';
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';
FLUSH PRIVILEGES;
USE $DB_NAME;

"

# Exécution des commandes SQL
mysql -u root -p -e "$SQL_COMMANDS"

echo "Databased initialized with success."