import mysql.connector
import configparser
import os

# Path to the configuration file
CONFIG_FILE = 'config.ini'

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
    config = get_mysql_config()
    return mysql.connector.connect(
        host=config['host'],
        user=config['user'],
        password=config['password'],
        database=config['database']
    )

def main():
    conn = get_db_connection()
    cursor = conn.cursor()

    print("Connected to the MySQL database. Type 'exit' to quit.")
    
    while True:
        query = input("SQL> ")
        if query.lower() == 'exit':
            break
        try:
            cursor.execute(query)
            if query.strip().lower().startswith("select"):
                rows = cursor.fetchall()
                for row in rows:
                    print(row)
            else:
                conn.commit()
                print(f"Query executed successfully: {cursor.rowcount} rows affected.")
        except mysql.connector.Error as err:
            print(f"Error: {err}")

    cursor.close()
    conn.close()
    print("Connection closed.")

if __name__ == "__main__":
    main()