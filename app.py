<<<<<<< HEAD
import os
import mysql.connector
import configparser
=======
from flask import Flask, jsonify
from flask_mysqldb import MySQL
from dotenv import load_dotenv
import os

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()
>>>>>>> 2bc3a4f5d7968f3021251a47a376dc78888ce76f

# Chemin du fichier de configuration
CONFIG_FILE = 'mysql_config.ini'

<<<<<<< HEAD
# Fonction pour lire les informations de connexion
def get_mysql_config():
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
        return {
            'host': config.get('mysql', 'host', fallback='localhost'),
            'user': config.get('mysql', 'user'),
            'password': config.get('mysql', 'password'),
            'database': config.get('mysql', 'database')
        }
    else:
        host = input("Hôte MySQL (par défaut: localhost): ") or 'localhost'
        user = input("Nom d'utilisateur MySQL: ")
        password = input("Mot de passe MySQL: ")
        database = input("Nom de la base de données: ")
=======
# Configuration de la connexion MySQL en utilisant les variables d'environnement
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
>>>>>>> 2bc3a4f5d7968f3021251a47a376dc78888ce76f

        config.add_section('mysql')
        config.set('mysql', 'host', host)
        config.set('mysql', 'user', user)
        config.set('mysql', 'password', password)
        config.set('mysql', 'database', database)

        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)

<<<<<<< HEAD
        return {
            'host': host,
            'user': user,
            'password': password,
            'database': database
        }

# Existing code to get MySQL configuration
config = get_mysql_config()

try:
    # Connect to the MySQL database
    connection = mysql.connector.connect(**config)
    cursor = connection.cursor()

    # Create a table named example_table
    cursor.execute("""
    CREATE TABLE example_table (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        age INT NOT NULL
    )
    """)

    # Insert some sample data into example_table
    cursor.execute("INSERT INTO example_table (name, age) VALUES ('Alice', 30)")
    cursor.execute("INSERT INTO example_table (name, age) VALUES ('Bob', 25)")
    cursor.execute("INSERT INTO example_table (name, age) VALUES ('Charlie', 35)")
    connection.commit()

    # Retrieve and print the data from example_table
    cursor.execute("SELECT * FROM example_table")
    rows = cursor.fetchall()
    for row in rows:
        print(row)

    # Drop example_table
    cursor.execute("DROP TABLE example_table")

    # Close the connection
    connection.close()
    print("Connexion réussie à la base de données MySQL")
except mysql.connector.Error as err:
    print(f"Erreur: {err}")
=======
if __name__ == '__main__':
    app.run(debug=True, port=443)
>>>>>>> 2bc3a4f5d7968f3021251a47a376dc78888ce76f
