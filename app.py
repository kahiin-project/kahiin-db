import os
import mysql.connector
import configparser
from flask import Flask, request, jsonify
from flask_cors import CORS
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
        password_hash VARCHAR(64)
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_infos (
        id_acc INT PRIMARY KEY,
        name VARCHAR(255),
        academy VARCHAR(255),
        FOREIGN KEY (id_acc) REFERENCES accounts(id_acc)
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS connexions (
        id_acc INT PRIMARY KEY,
        token BINARY(32) NOT NULL,
        FOREIGN KEY (id_acc) REFERENCES accounts(id_acc)
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS verifications (
        id_acc INT PRIMARY KEY,
        token BINARY(32) NOT NULL,
        FOREIGN KEY (id_acc) REFERENCES accounts(id_acc)
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quiz (
        id_file INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255),
        id_acc INT,
        subject VARCHAR(255),
        language VARCHAR(255),
        FOREIGN KEY (id_acc) REFERENCES accounts(id_acc)
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS question_posts (
        id_question INT AUTO_INCREMENT PRIMARY KEY,
        id_acc INT,
        subject VARCHAR(255),
        language VARCHAR(255),
        FOREIGN KEY (id_acc) REFERENCES accounts(id_acc)
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS question_contents (
        id_question INT PRIMARY KEY,
        title VARCHAR(255),
        shown_answers TEXT,
        correct_answer TEXT,
        duration INT,
        type VARCHAR(255),
        FOREIGN KEY (id_question) REFERENCES question_posts(id_question)
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
    # cursor.execute("DROP TABLE verifications")
    # cursor.execute("DROP TABLE quiz")
    # cursor.execute("DROP TABLE question_posts")
    # cursor.execute("DROP TABLE question_contents")

    # Close the connection
    connection.close()
    print("Successfully connected to the MySQL database")
except mysql.connector.Error as err:
    print(f"Error: {err}")


app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'quizFiles')

# Function to establish a MySQL connection
def get_db_connection():
    config = get_mysql_config()
    return mysql.connector.connect(
        host=config['host'],
        user=config['user'],
        password=config['password'],
        database=config['database']
    )

def is_hex(s):
    # Check if the string is a valid hexadecimal string
    try:
        bytes.fromhex(s)
        return True
    except ValueError:
        return False

def is_valid_token(token):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM connexions WHERE token = %s", (bytes.fromhex(token),))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return len(rows) > 0

@app.route('/quiz', methods=['GET'])
def get_quiz():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if not isinstance(data, dict) or 'token' not in data or 'params' not in data:
        return jsonify({'error': 'Invalid data structure'}), 400
    if not isinstance(data['token'], str) or not isinstance(data['params'], dict):
        return jsonify({'error': 'Invalid data types'}), 400
    
    if not is_hex(data['token']):
        return jsonify({'error': 'Token not hexadecimal'}), 401
    if not is_valid_token(data['token']):
        return jsonify({'error': 'Invalid token'}), 401
    
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
    
    if not is_hex(data['token']):
        return jsonify({'error': 'Token not hexadecimal'}), 401
    if not is_valid_token(data['token']):
        return jsonify({'error': 'Invalid token'}), 401
    
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
    
    if not is_hex(data['token']):
        return jsonify({'error': 'Token not hexadecimal'}), 401
    if not is_valid_token(data['token']):
        return jsonify({'error': 'Invalid token'}), 401
    
    cursor.execute("SELECT * FROM question_contents WHERE id_question = %s", (data['id_question'],))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()
    return jsonify(rows), 200

@app.route('/quiz', methods=['POST'])
def post_quiz():
    token = request.form.get('token')
    filename = request.form.get('filename')
    file = request.files.get('file')

    if not token or not filename or not file:
        return jsonify({'error': 'Invalid data structure'}), 400
    if not isinstance(token, str) or not isinstance(filename, str):
        return jsonify({'error': 'Invalid data types'}), 400
    
    if not is_hex(token):
        return jsonify({'error': 'Token not hexadecimal'}), 401
    if not is_valid_token(token):
        return jsonify({'error': 'Invalid token'}), 401

    # Save the file
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    # Process the file or save the file path to the database
    # ...

    return jsonify({'message': 'Quiz uploaded successfully'}), 200

@app.route('/question', methods=['POST'])
def post_question():
    data = request.get_json()
    token = data.get('token')
    question = data.get('question')

    if not token or not question:
        return jsonify({'error': 'Invalid data structure'}), 400
    if not isinstance(token, str):
        return jsonify({'error': 'Invalid data type for token'}), 400
    if not isinstance(question, dict):
        return jsonify({'error': 'Invalid data type for question'}), 400

    required_fields = ['subject', 'language', 'title', 'shown_answers', 'correct_answers', 'duration', 'type']
    for field in required_fields:
        if field not in question:
            return jsonify({'error': f'Missing field: {field}'}), 400
        if field == 'duration' and not isinstance(question[field], int):
            return jsonify({'error': f'Invalid data type for {field}'}), 400
        elif field != 'duration' and not isinstance(question[field], str):
            return jsonify({'error': f'Invalid data type for {field}'}), 400
    
    if not is_hex(token):
        return jsonify({'error': 'Token not hexadecimal'}), 401
    if not is_valid_token(token):
        return jsonify({'error': 'Invalid token'}), 401

    # Process the question data or save it to the database
    # ...

    return jsonify({'message': 'Question uploaded successfully'}), 200

@app.route('/login', methods=['POST'])
def post_login():
    data = request.get_json()
    email = data.get('email')
    password_hash = data.get('password_hash')

    if not email or not password_hash:
        return jsonify({'error': 'Invalid data structure'}), 400
    if not isinstance(email, str):
        return jsonify({'error': 'Invalid data type for email'}), 400
    if not isinstance(password_hash, str):
        return jsonify({'error': 'Invalid data type for password_hash'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM accounts WHERE email = %s AND password_hash = %s", (email, password_hash))
    rows = cursor.fetchall()
    if(len(rows) == 0):
        return jsonify({'error': 'Invalid email or password'}), 401

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'message': 'Login successful'}), 200

@app.route('/signup', methods=['POST'])
def post_signup():
    data = request.get_json()
    email = data.get('email')
    password_hash = data.get('password_hash')

    if not email or not password_hash:
        return jsonify({'error': 'Invalid data structure'}), 400
    if not isinstance(email, str):
        return jsonify({'error': 'Invalid data type for email'}), 400
    if not isinstance(password_hash, str):
        return jsonify({'error': 'Invalid data type for password_hash'}), 400

    # Process the signup data or create a new user
    # ...

    return jsonify({'message': 'Signup successful'}), 200

@app.route('/account', methods=['DELETE'])
def delete_account():
    data = request.json
    token = data.get('token')
    
    if not token:
        return jsonify({'error': 'Invalid data structure'}), 400
    if not isinstance(token, str):
        return jsonify({'error': 'Invalid data type for token'}), 400

    if not is_hex(data['token']):
        return jsonify({'error': 'Token not hexadecimal'}), 401
    if not is_valid_token(data['token']):
        return jsonify({'error': 'Invalid token'}), 401

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Delete the account

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Account deleted successfully'}), 200

@app.route('/quiz', methods=['DELETE'])
def delete_quiz():
    data = request.json
    token = data.get('token')
    id_file = data.get('id_file')
    
    if not token or not id_file:
        return jsonify({'error': 'Invalid data structure'}), 400
    if not isinstance(token, str) or not isinstance(id_file, int):
        return jsonify({'error': 'Invalid data types'}), 400

    if not is_hex(data['token']):
        return jsonify({'error': 'Token not hexadecimal'}), 401
    if not is_valid_token(data['token']):
        return jsonify({'error': 'Invalid token'}), 401

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Delete the quiz

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Quiz deleted successfully'}), 200

@app.route('/question', methods=['DELETE'])
def delete_question():
    data = request.json
    token = data.get('token')
    id_question = data.get('id_question')
    
    if not token or not id_question:
        return jsonify({'error': 'Invalid data structure'}), 400
    if not isinstance(token, str) or not isinstance(id_question, int):
        return jsonify({'error': 'Invalid data types'}), 400

    if not is_hex(data['token']):
        return jsonify({'error': 'Token not hexadecimal'}), 401
    if not is_valid_token(data['token']):
        return jsonify({'error': 'Invalid token'}), 401

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Delete the question

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Question deleted successfully'}), 200

if __name__ == '__main__':
    app.run(debug=True)

