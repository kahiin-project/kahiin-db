#!/bin/bash

# Arrêter le service MySQL
sudo systemctl stop mysqld

# Supprimer les paquets MySQL
sudo yum remove -y mysql-server
sudo yum autoremove -y

# Supprimer les fichiers de configuration
sudo rm -rf /etc/my.cnf
sudo rm -rf /var/lib/mysql/

echo "MySQL a été complètement désinstallé."
