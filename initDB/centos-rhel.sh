#!/bin/bash

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

# Start MySQL service
sudo systemctl start mysqld
sudo systemctl enable mysqld

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

# Function to validate encryption key
validate_key() {
    if [ ${#1} -ge 16 ]; then
        return 0
    else
        return 1
    fi
}

# Create a new database
while true; do
    read -p "Database name: " db_name
    if validate_alphanum "$db_name"; then
        sudo mysql -e "CREATE DATABASE $db_name;"
        break
    else
        echo "Invalid database name. Only alphanumeric characters and underscores are allowed."
    fi
done

# Create a new user
while true; do
    read -p "Database username: " user_name
    if validate_alphanum "$user_name"; then
        break
    else
        echo "Invalid username. Only alphanumeric characters and underscores are allowed."
    fi
done

# Collect database password
read -s -p "Database password: " user_pass
echo

# Collect database host
read -p "Database host [localhost]: " db_host
db_host=${db_host:-localhost}

# Grant privileges to the new user
sudo mysql -e "CREATE USER '$user_name'@'$db_host' IDENTIFIED BY '$user_pass';"
sudo mysql -e "GRANT ALL PRIVILEGES ON $db_name.* TO '$user_name'@'$db_host';"
sudo mysql -e "FLUSH PRIVILEGES;"

# Collect email information
while true; do
    read -p "Email address: " email
    if validate_email "$email"; then
        break
    else
        echo "Invalid email format. Please try again."
    fi
done

# Collect email password
read -s -p "Email password: " email_password
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
    read -s -p "Encryption key (at least 16 characters): " encryption_key
    echo
    if validate_key "$encryption_key"; then
        break
    else
        echo "Encryption key must be at least 16 characters long for security."
    fi
done

# Create the encrypted configuration file
echo "Creating encrypted configuration file..."
python config-maker.py "$user_pass" "$db_host" "$user_name" "$db_name" "$email" "$email_password" "$smtp_server" "$smtp_port" "$encryption_key"

echo "Configuration complete!"