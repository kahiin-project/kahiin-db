#!/bin/bash
read -s -p "Enter password: " password
echo

if [ "$(uname)" == "Linux" ]; then
    if command -v apt-get >/dev/null 2>&1; then
        echo "Detected Debian/Ubuntu based system. Setting up the environment..."
        sudo apt-get update -qq
        sudo apt-get install -y -qq python3 python3-pip python3-venv libmysqlclient-dev
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt -q
        echo "Starting the Kahiin database..."
        python3 app.py $password
    elif command -v pacman >/dev/null 2>&1; then
        echo "Detected Arch based system. Setting up the environment..."
        sudo pacman -Syu --noconfirm > /dev/null
        sudo pacman -S --noconfirm python3 python-pip python-virtualenv mariadb-libs > /dev/null
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt -q
        echo "Starting the Kahiin database..."
        python3 app.py $password
    else
        echo "OS not supported"
    fi
else
    echo "This OS is not Linux"
fi