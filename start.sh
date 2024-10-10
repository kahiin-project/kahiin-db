#!/bin/bash

# Detect operating system
if [[ "$(uname)" == "Linux" ]]; then
    if command -v apt >/dev/null 2>&1; then
        # Debian Based
        echo 
        echo Welcome to $(grep -oP '^NAME="\K[^"]+' /etc/os-release).
        echo To run this script, you need to be root.
        echo
        yes | sudo apt update
        yes | sudo apt install python3 
        yes | sudo apt install python3-pip
        yes | sudo apt install python$(python3 -V 2>&1 | awk -F'[ .]' '{print $2"."$3}')-venv
        python3 -m venv venv
        source venv/bin/activate
        yes | sudo apt install python3
        yes | pip install flask
        yes | pip install Flask-MySQL
        sudo python3 app.py
    elif command -v pacman >/dev/null 2>&1; then
    echo 
    echo Welcome to $(grep -oP '^NAME="\K[^"]+' /etc/os-release).
    echo To run this script, you need to be root.
    echo
        # Arch Based
        yes | sudo pacman -Syu
        yes | sudo pacman -S python3
        yes | sudo pacman -S python-pip
        yes | sudo pacman -S python-virtualenv
        python3 -m venv venv
        source venv/bin/activate
        yes | sudo pacman -S python3
        yes | pip install flask
        yes | pip install Flask-MySQL
        sudo python3 app.py
    else
        echo "OS not supported"
    fi
else
    echo "This OS is not Linux"
fi