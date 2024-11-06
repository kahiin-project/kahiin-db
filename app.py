import os
import mysql.connector
import configparser
from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import configparser
import os

def pad_binary_data(data, length):
    """
    Pads the binary data to the specified length with null bytes.

    Args:
        data (bytes): The binary data to pad.
        length (int): The desired length of the padded data.

    Returns:
        bytes: The padded binary data.
    """
    if len(data) < length:
        data += b'\x00' * (length - len(data))
    return data

# Path to the configuration file
CONFIG_FILE = 'mysql_config.ini'

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'quizFiles')

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
    connection = get_db_connection()
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
        FOREIGN KEY (id_acc) REFERENCES accounts(id_acc) ON DELETE CASCADE
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS connexions (
        id_acc INT PRIMARY KEY,
        token BINARY(32) NOT NULL,
        FOREIGN KEY (id_acc) REFERENCES accounts(id_acc) ON DELETE CASCADE
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS verifications (
        id_acc INT PRIMARY KEY,
        token BINARY(32) NOT NULL,
        FOREIGN KEY (id_acc) REFERENCES accounts(id_acc) ON DELETE CASCADE
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quiz (
        id_file INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255),
        id_acc INT,
        subject VARCHAR(255),
        language VARCHAR(255),
        FOREIGN KEY (id_acc) REFERENCES accounts(id_acc) ON DELETE CASCADE
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS question_posts (
        id_question INT AUTO_INCREMENT PRIMARY KEY,
        id_acc INT,
        subject VARCHAR(255),
        language VARCHAR(255),
        FOREIGN KEY (id_acc) REFERENCES accounts(id_acc) ON DELETE CASCADE
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
        FOREIGN KEY (id_question) REFERENCES question_posts(id_question) ON DELETE CASCADE
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

    # Deleting existing data
    cursor.execute("DELETE FROM connexions")
    cursor.execute("DELETE FROM accounts")

    # Inserting new data
    token_data = bytes.fromhex('4f3c2e1d5a6b7c8d9e0f1a2b3c4d5e6f')
    padded_token_data = pad_binary_data(token_data, 32)  # Par exemple, pour une longueur de 32 octets

    cursor.execute("INSERT INTO accounts (id_acc, email, password_hash) VALUES (%s, %s, %s)", (1, "email@example.org", "f2d81a260dea8a100dd517984e53c56a7523d96942a834b9cdc249bd4e8c7aa9",))
    cursor.execute("INSERT INTO connexions (id_acc, token) VALUES (%s, %s)", (1, padded_token_data))
    cursor.close()

    # Close the connection
    connection.close()
    print("Successfully connected to the MySQL database")
except mysql.connector.Error as err:
    print(f"Error: {err}")

def is_hex(s):
    """
    Checks if the given string is a valid hexadecimal string.

    Args:
        s (str): The string to check.

    Returns:
        bool: True if the string is a valid hexadecimal string, False otherwise.
    """
    try:
        bytes.fromhex(s)
        return True
    except ValueError:
        return False

def is_valid_token(token):
    """
    Checks if the given token is valid by querying the database.

    Args:
        token (str): The token to check.

    Returns:
        bool: True if the token is valid, False otherwise.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Retrieving data for verification
    cursor.execute("SELECT * FROM connexions")
    rows = cursor.fetchall()

    # Comparing binary data
    cursor.execute("SELECT * FROM connexions WHERE token = %s", (pad_binary_data(bytes.fromhex(token), 32),))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()
    
    return len(rows) > 0

@app.route('/quiz', methods=['GET'])
def get_quiz():
    """
    Retrieves all quizzes from the database.

    Returns:
        Response: A JSON response containing the quizzes or an error message.
    """
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
    """
    Retrieves all questions from the database.

    Returns:
        Response: A JSON response containing the questions or an error message.
    """
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
    """
    Retrieves the content of a specific question from the database.

    Returns:
        Response: A JSON response containing the question content or an error message.
    """
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
    """
    Uploads a new quiz file and saves its information to the database.

    Returns:
        Response: A JSON response indicating success or an error message.
    """
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

    conn = get_db_connection()
    cursor = conn.cursor()

    # Save file data to the database
    cursor.execute("INSERT INTO quiz (name, id_acc) VALUES (%s, (SELECT id_acc FROM connexions WHERE token = %s))", (filename, bytes.fromhex(token),))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'message': 'Quiz uploaded successfully'}), 200

@app.route('/question', methods=['POST'])
def post_question():
    """
    Uploads a new question and saves its information to the database.

    Returns:
        Response: A JSON response indicating success or an error message.
    """
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
    """
    Authenticates a user by checking their email and password hash.

    Returns:
        Response: A JSON response indicating success or an error message.
    """
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
    """
    Registers a new user by saving their email and password hash to the database.

    Returns:
        Response: A JSON response indicating success or an error message.
    """
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
    """
    Deletes a user account based on the provided token.

    Returns:
        Response: A JSON response indicating success or an error message.
    """
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
    
    cursor.execute("DELETE FROM accounts WHERE id_acc = (SELECT id_acc FROM connexions WHERE token = %s)", (bytes.fromhex(token),))

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Account deleted successfully'}), 200

@app.route('/quiz', methods=['DELETE'])
def delete_quiz():
    """
    Deletes a quiz based on the provided token and quiz ID.

    Returns:
        Response: A JSON response indicating success or an error message.
    """
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

    cursor.execute("SELECT * FROM quiz WHERE id_file = %s", (id_file,))
    rows = cursor.fetchall()
    if len(rows) == 0:
        return jsonify({'error': 'Quiz not found'}), 404
    cursor.execute("DELETE FROM quiz WHERE id_file = %s", (id_file,))

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Quiz deleted successfully'}), 200

@app.route('/question', methods=['DELETE'])
def delete_question():
    """
    Deletes a question based on the provided token and question ID.

    Returns:
        Response: A JSON response indicating success or an error message.
    """
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
    
    cursor.execute("SELECT * FROM question_posts WHERE id_question = %s", (id_question,))
    rows = cursor.fetchall()
    if len(rows) == 0:
        return jsonify({'error': 'Question not found'}), 404
    cursor.execute("DELETE FROM question_posts WHERE id_question = %s", (id_question,))

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Question deleted successfully'}), 200

if __name__ == '__main__':
    app.run(debug=True)

