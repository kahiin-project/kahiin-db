import os
import mysql.connector
import configparser
import mysql.connector
import configparser
import os

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

# Function to establish a MySQL connection
def get_db_connection():
    """
    Establishes a connection to the MySQL database using the configuration file.

    Returns:
        mysql.connector.connection.MySQLConnection: The MySQL database connection.
    """
    config = get_mysql_config()
    return mysql.connector.connect(
        host=config['host'],
        user=config['user'],
        password=config['password'],
        database=config['database']
    )

if __name__ == "__main__":
    # Connect to the MySQL database
    connection = get_db_connection()
    cursor = connection.cursor()

    # Disable foreign key checks
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

    # Get the list of all tables
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()

    # Drop each table
    for (table_name,) in tables:
        cursor.execute(f"DROP TABLE {table_name}")

    # Enable foreign key checks
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

    # Close the connection
    connection.commit()
    cursor.close()
    connection.close()