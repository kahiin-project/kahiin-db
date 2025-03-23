#!/bin/bash

if [ $# -ne 10 ]; then
    echo "Usage: $0 <db_name> <db_user> <db_password> <db_host> <email> <email_password> <smtp_server> <smtp_port> <encryption_key> <root_password>"
    exit 1
fi

db_name="$1"
db_user="$2"
db_password="$3"
db_host="$4"
email="$5"
email_password="$6"
smtp_server="$7"
smtp_port="$8"
encryption_key="$9"
root_password="${10}"

validate_alphanum() {
    [[ "$1" =~ ^[a-zA-Z0-9_]+$ ]]
}

validate_email() {
    [[ "$1" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]
}

validate_port() {
    [[ "$1" =~ ^[0-9]+$ ]] && [ "$1" -ge 1 ] && [ "$1" -le 65535 ]
}

validate_key() {
    [ ${#1} -ge 16 ]
}

if ! validate_alphanum "$db_name"; then
    echo "Invalid database name. Exiting."
    exit 1
fi

if ! validate_alphanum "$db_user"; then
    echo "Invalid username. Exiting."
    exit 1
fi

if ! validate_email "$email"; then
    echo "Invalid email. Exiting."
    exit 1
fi

if ! validate_port "$smtp_port"; then
    echo "Invalid port. Exiting."
    exit 1
fi

if ! validate_key "$encryption_key"; then
    echo "Invalid encryption key. Exiting."
    exit 1
fi

sudo pacman -S --noconfirm mysql > /dev/null 2>&1
sudo mysql_install_db --user=mysql --basedir=/usr --datadir=/var/lib/mysql > /dev/null 2>&1
sudo systemctl start mysqld > /dev/null 2>&1

# Automatiser la sécurisation de MariaDB
sudo mysql -e "UPDATE mysql.user SET Password=PASSWORD('$root_password') WHERE User='root';" > /dev/null 2>&1
sudo mysql -e "DELETE FROM mysql.user WHERE User='';" > /dev/null 2>&1
sudo mysql -e "DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');" > /dev/null 2>&1
sudo mysql -e "DROP DATABASE IF EXISTS test;" > /dev/null 2>&1
sudo mysql -e "DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';" > /dev/null 2>&1
sudo mysql -e "FLUSH PRIVILEGES;" > /dev/null 2>&1

sudo mysql -u root -p"$root_password" -e "CREATE DATABASE IF NOT EXISTS $db_name;" > /dev/null 2>&1
sudo mysql -u root -p"$root_password" -e "CREATE USER '$db_user'@'$db_host' IDENTIFIED BY '$db_password';" > /dev/null 2>&1
sudo mysql -u root -p"$root_password" -e "GRANT ALL PRIVILEGES ON $db_name.* TO '$db_user'@'$db_host';" > /dev/null 2>&1
sudo mysql -u root -p"$root_password" -e "FLUSH PRIVILEGES;" > /dev/null 2>&1

python config-maker.py "$db_password" "$db_host" "$db_user" "$db_name" "$email" "$email_password" "$smtp_server" "$smtp_port" "$encryption_key" > /dev/null 2>&1

echo "Configuration complete!"

exit 0