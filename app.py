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

    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id_acc INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(255),
            password VARCHAR(64)
        );
        CREATE TABLE IF NOT EXISTS user_infos (
            id_acc INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            academy VARCHAR(255)
        );
        CREATE TABLE IF NOT EXISTS connexions (
            id_acc INT AUTO_INCREMENT PRIMARY KEY,
            token BINARY(32) NOT NULL
        );
        CREATE TABLE IF NOT EXISTS quiz (
            id_file INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            id_acc INT,
            subject VARCHAR(255),
            language VARCHAR(255)
        );
        CREATE TABLE IF NOT EXISTS question_posts (
            id_question INT AUTO_INCREMENT PRIMARY KEY,
            id_acc INT,
            subject VARCHAR(255),
            language VARCHAR(255)
        );
        CREATE TABLE IF NOT EXISTS question_contents (
            id_question INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255),
            shown_answers TEXT,
            correct_answers TEXT,
            duration INT,
            type VARCHAR(255)
        );
    """)

    # Drop example_table
    cursor.execute("DROP TABLE accounts")
    cursor.execute("DROP TABLE user_infos")
    cursor.execute("DROP TABLE connexions")
    cursor.execute("DROP TABLE quiz")
    cursor.execute("DROP TABLE question_posts")
    cursor.execute("DROP TABLE question_contents")

    # Close the connection
    connection.close()
    print("Successfully connected to the MySQL database")
except mysql.connector.Error as err:
    print(f"Error: {err}")
