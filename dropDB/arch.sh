#!/bin/bash

# Arrêter le service MySQL
sudo systemctl stop mysqld

# Supprimer les paquets MySQL
sudo pacman -Rs mysql

# Supprimer les fichiers de configuration
sudo rm -rf /etc/mysql/
sudo rm -rf /var/lib/mysql/

echo "MySQL a été complètement désinstallé."
