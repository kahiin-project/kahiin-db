import os
import mysql.connector
import configparser
from flask import Flask, request, jsonify
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
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_infos (
        id_acc INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255),
        academy VARCHAR(255)
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS connexions (
        id_acc INT AUTO_INCREMENT PRIMARY KEY,
        token BINARY(32) NOT NULL
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quiz (
        id_file INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255),
        id_acc INT,
        subject VARCHAR(255),
        language VARCHAR(255)
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS question_posts (
        id_question INT AUTO_INCREMENT PRIMARY KEY,
        id_acc INT,
        subject VARCHAR(255),
        language VARCHAR(255)
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS question_contents (
        id_question INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(255),
        shown_answers TEXT,
        correct_answer TEXT,
        duration INT,
        type VARCHAR(255)
    );
    """)

    # Retrieve the names of all tables in the database
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = %s", (config['database'],))
    tables = cursor.fetchall()

    # Print the names of all tables
    print([tables[i][0] for i in range(len(tables))])

    # Drop example_table
    # cursor.execute("DROP TABLE accounts")
    # cursor.execute("DROP TABLE user_infos")
    # cursor.execute("DROP TABLE connexions")
    # cursor.execute("DROP TABLE quiz")
    # cursor.execute("DROP TABLE question_posts")
    # cursor.execute("DROP TABLE question_contents")

    # Close the connection
    connection.close()
    print("Successfully connected to the MySQL database")
except mysql.connector.Error as err:
    print(f"Error: {err}")


app = Flask(__name__)

# Function to establish a MySQL connection
def get_db_connection():
    config = get_mysql_config()
    return mysql.connector.connect(
        host=config['host'],
        user=config['user'],
        password=config['password'],
        database=config['database']
    )

@app.route('/quiz', methods=['GET'])
def get_quiz():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if not isinstance(data, dict) or 'token' not in data or 'params' not in data:
        return jsonify({'error': 'Invalid data structure'}), 400
    if not isinstance(data['token'], str) or not isinstance(data['params'], dict):
        return jsonify({'error': 'Invalid data types'}), 400
    
    cursor.execute("SELECT * FROM quiz", ())
    rows = cursor.fetchall()

    cursor.close()
    conn.close()
    return jsonify(rows), 200

@app.route('/questions', methods=['GET'])
def get_questions():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if not isinstance(data, dict) or 'token' not in data or 'params' not in data:
        return jsonify({'error': 'Invalid data structure'}), 400
    if not isinstance(data['token'], str) or not isinstance(data['params'], dict):
        return jsonify({'error': 'Invalid data types'}), 400
    
    cursor.execute("SELECT * FROM question_posts", ())
    rows = cursor.fetchall()

    cursor.close()
    conn.close()
    return jsonify(rows), 200

@app.route('/question-content', methods=['GET'])
def get_question_content():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if not isinstance(data, dict) or 'token' not in data or 'id_question' not in data:
        return jsonify({'error': 'Invalid data structure'}), 400
    if not isinstance(data['token'], str) or not isinstance(data['id_question'], int):
        return jsonify({'error': 'Invalid data types'}), 400
    
    cursor.execute("SELECT * FROM question_contents WHERE id_question = %s", (data['id_question'],))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()
    return jsonify(rows), 200

@app.route('/', methods=['POST'])
def post_data():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print(data)

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'type': 'POST'})

@app.route('/', methods=['DELETE'])
def delete_data():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print(data)

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'type': 'DELETE'})

if __name__ == '__main__':
    app.run(debug=True, port=443)

