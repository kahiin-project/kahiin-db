#!/bin/bash

if [ "$(uname)" == "Linux" ]; then
    if command -v apt-get >/dev/null 2>&1; then
        # Debian/Ubuntu Based
        yes | sudo apt-get update
        yes | sudo apt-get install python3 python3-pip python3-venv
        yes | sudo apt-get install libmysqlclient-dev  # Ajout de cette ligne
        python3 -m venv venv
        source venv/bin/activate
        yes | pip install flask
        yes | pip install flask-mysqldb
<<<<<<< HEAD
        yes | pip install mysql-connector-python
=======
        yes | pip install python-dotenv
>>>>>>> 2bc3a4f5d7968f3021251a47a376dc78888ce76f
        sudo python3 app.py
    elif command -v pacman >/dev/null 2>&1; then
        # Arch Based
        echo
        echo Welcome to $(grep -oP '^NAME="\K[^"]+' /etc/os-release).
        echo To run this script, you need to be root.
        echo
        yes | sudo pacman -Syu
        yes | sudo pacman -S python3 python-pip python-virtualenv
        yes | sudo pacman -S mariadb-libs  # Ajout de cette ligne
        python3 -m venv venv
        source venv/bin/activate
        yes | pip install flask
        yes | pip install flask-mysqldb
<<<<<<< HEAD
        yes | pip install mysql-connector-python
=======
        yes | pip install python-dotenv
>>>>>>> 2bc3a4f5d7968f3021251a47a376dc78888ce76f
        sudo python3 app.py
    else
        echo "OS not supported"
    fi
else
    echo "This OS is not Linux"
fi