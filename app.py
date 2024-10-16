import os
import mysql.connector
import configparser

# Path to the configuration file
CONFIG_FILE = 'mysql_config.ini'

# Function to read connection information
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
        host = input("MySQL Host (default: localhost): ") or 'localhost'
        user = input("MySQL Username: ")
        password = input("MySQL Password: ")
        database = input("Database Name: ")

        config.add_section('mysql')
        config.set('mysql', 'host', host)
        config.set('mysql', 'user', user)
        config.set('mysql', 'password', password)
        config.set('mysql', 'database', database)

        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)

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
