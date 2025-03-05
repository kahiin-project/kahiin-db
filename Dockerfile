FROM python:3.13.2-slim-bookworm

WORKDIR /kahiin-db

COPY . .

RUN apt-get update && \
    apt-get install -y mariadb-server pkg-config libmariadb-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# Créer un répertoire pour les scripts d'initialisation
RUN mkdir -p /docker-entrypoint-initdb.d

# Configurer le dossier de données MariaDB comme volume
# Mais ce volume sera remplacé lors de l'exécution
VOLUME ["/var/lib/mysql"]

RUN pip3 install --no-cache-dir --upgrade pip
RUN pip3 install --no-cache-dir mysqlclient -r requirements.txt

EXPOSE 5000

ARG DB_NAME
ARG DB_USER
ARG DB_PASSWORD
ARG DB_HOST
ARG CONFIG_ENCRYPTION_KEY
ARG EMAIL
ARG EMAIL_PASSWORD
ARG SMTP_SERVER
ARG SMTP_PORT

ENV DB_NAME=${DB_NAME}
ENV DB_USER=${DB_USER}
ENV DB_PASSWORD=${DB_PASSWORD}
ENV DB_HOST=${DB_HOST}
ENV CONFIG_ENCRYPTION_KEY=${CONFIG_ENCRYPTION_KEY}
ENV EMAIL=${EMAIL}
ENV EMAIL_PASSWORD=${EMAIL_PASSWORD}
ENV SMTP_SERVER=${SMTP_SERVER}
ENV SMTP_PORT=${SMTP_PORT}

# Créer le script d'initialisation de la base de données
RUN echo "#!/bin/bash" > /docker-entrypoint-initdb.d/init-db.sh && \
    echo "mysql -u root -e \"CREATE DATABASE IF NOT EXISTS \${DB_NAME};\"" >> /docker-entrypoint-initdb.d/init-db.sh && \
    echo "mysql -u root -e \"CREATE USER IF NOT EXISTS '\${DB_USER}'@'%' IDENTIFIED BY '\${DB_PASSWORD}';\"" >> /docker-entrypoint-initdb.d/init-db.sh && \
    echo "mysql -u root -e \"GRANT ALL PRIVILEGES ON \${DB_NAME}.* TO '\${DB_USER}'@'%';\"" >> /docker-entrypoint-initdb.d/init-db.sh && \
    echo "mysql -u root -e \"FLUSH PRIVILEGES;\"" >> /docker-entrypoint-initdb.d/init-db.sh && \
    chmod +x /docker-entrypoint-initdb.d/init-db.sh

# Créer la configuration chiffrée
RUN python3 initDB/config-maker.py "${DB_PASSWORD}" "${DB_HOST}" "${DB_USER}" "${DB_NAME}" "${EMAIL}" "${EMAIL_PASSWORD}" "${SMTP_SERVER}" "${SMTP_PORT}" "${CONFIG_ENCRYPTION_KEY}"

# Créer le script d'entrée
RUN echo '#!/bin/bash' > /docker-entrypoint.sh && \
    echo '# Démarrer MariaDB' >> /docker-entrypoint.sh && \
    echo 'service mariadb start' >> /docker-entrypoint.sh && \
    echo 'sleep 5' >> /docker-entrypoint.sh && \
    echo '# Vérifier et initialiser la base de données si nécessaire' >> /docker-entrypoint.sh && \
    echo 'if ! mysql -u root -e "USE ${DB_NAME}" 2>/dev/null; then' >> /docker-entrypoint.sh && \
    echo '  echo "Initialisation de la base de données..."' >> /docker-entrypoint.sh && \
    echo '  bash /docker-entrypoint-initdb.d/init-db.sh' >> /docker-entrypoint.sh && \
    echo 'fi' >> /docker-entrypoint.sh && \
    echo 'exec python3 /kahiin-db/app.py "${CONFIG_ENCRYPTION_KEY}"' >> /docker-entrypoint.sh && \
    chmod +x /docker-entrypoint.sh

# Une seule commande CMD
CMD ["/docker-entrypoint.sh"]