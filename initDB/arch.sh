#!/bin/bash

# Install MySQL
sudo pacman -S --noconfirm mysql

# Initialize the database
sudo mysql_install_db --user=mysql --basedir=/usr --datadir=/var/lib/mysql

# Start the MySQL service
sudo systemctl start mysqld

# Secure the MySQL installation
sudo mysql_secure_installation

# Function to validate database name and username
validate_alphanum() {
    if [[ "$1" =~ ^[a-zA-Z0-9_]+$ ]]; then
        return 0
    else
        return 1
    fi
}

# Function to validate email
validate_email() {
    if [[ "$1" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
        return 0
    else
        return 1
    fi
}

# Function to validate port number
validate_port() {
    if [[ "$1" =~ ^[0-9]+$ ]] && [ "$1" -ge 1 ] && [ "$1" -le 65535 ]; then
        return 0
    else
        return 1
    fi
}

# Function to validate encryption key (at least 16 characters for security)
validate_key() {
    if [ ${#1} -ge 16 ]; then
        return 0
    else
        return 1
    fi
}

# Collect database name
while true; do
    read -p "Database name: " db_name
    if validate_alphanum "$db_name"; then
        sudo mysql -e "CREATE DATABASE $db_name;"
        break
    else
        echo "Invalid database name. Only alphanumeric characters and underscores are allowed."
    fi
done

# Collect database user
while true; do
    read -p "Database username: " db_user
    if validate_alphanum "$db_user"; then
        break
    else
        echo "Invalid username. Only alphanumeric characters and underscores are allowed."
    fi
done

# Collect database password
read -sp "Database password: " db_password
echo

# Collect database host
read -p "Database host [localhost]: " db_host
db_host=${db_host:-localhost}

# Collect email
while true; do
    read -p "Email address: " email
    if validate_email "$email"; then
        break
    else
        echo "Invalid email format. Please try again."
    fi
done

# Collect email password
read -sp "Email password: " email_password
echo

# Collect SMTP server
read -p "SMTP server: " smtp_server

# Collect SMTP port
while true; do
    read -p "SMTP port [587]: " smtp_port
    smtp_port=${smtp_port:-587}
    if validate_port "$smtp_port"; then
        break
    else
        echo "Invalid port number. Please enter a number between 1 and 65535."
    fi
done

# Collect encryption key
while true; do
    read -sp "Encryption key (at least 16 characters): " encryption_key
    echo
    if validate_key "$encryption_key"; then
        break
    else
        echo "Encryption key must be at least 16 characters long for security."
    fi
done

# Create database user and grant privileges
sudo mysql -e "CREATE USER '$db_user'@'$db_host' IDENTIFIED BY '$db_password';"
sudo mysql -e "GRANT ALL PRIVILEGES ON $db_name.* TO '$db_user'@'$db_host';"
sudo mysql -e "FLUSH PRIVILEGES;"

echo "Creating encrypted configuration file..."
python config-maker.py "$db_password" "$db_host" "$db_user" "$db_name" "$email" "$email_password" "$smtp_server" "$smtp_port" "$encryption_key"

echo "Configuration complete!"