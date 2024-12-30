import os
import mysql.connector
import configparser
from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import mysql.connector
import configparser
import hashlib
import secrets
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import xml.etree.ElementTree as ET
import json
import uuid
import base64
import sys
import uuid
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

password = sys.argv[1]
salt = ""

# Modifier la fonction de vérification du hash
def check_password_hash(stored_hash, password_hash):
    """
    Check if the provided password hash matches the stored hash with salt.

    Args:
        stored_hash (str): The stored salted hash in the database
        password_hash (str): The SHA256 hash from client side

    Returns:
        bool: True if the password matches, False otherwise
    """
    # Add server-side salt and hash again
    salted_hash = hashlib.sha256((password_hash + salt).encode()).hexdigest()
    return salted_hash == stored_hash


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

def parse_answers(answers):
    """
    Parses the answers if they are in string format.

    Args:
        answers (str or list): The answers to parse.

    Returns:
        list: The parsed answers.
    """
    if isinstance(answers, str):
        try:
            return json.loads(answers)
        except json.JSONDecodeError:
            return []
    return answers

# Path to the configuration file
CONFIG_FILE = 'config.ini'

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'quizFiles')

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
        type VARCHAR(255) NOT NULL,
        FOREIGN KEY (id_acc) REFERENCES accounts(id_acc) ON DELETE CASCADE
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS waiting_passwords (
        id_acc INT PRIMARY KEY,
        password_hash VARCHAR(64) NOT NULL,
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
        correct_answers TEXT,
        duration INT,
        type VARCHAR(255),
        FOREIGN KEY (id_question) REFERENCES question_posts(id_question) ON DELETE CASCADE
    );
    """)

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
    Retrieves all quizzes from the database based on provided parameters.

    Returns:
        Response: A JSON response containing the quizzes or an error message.
    """
    token = request.args.get('token')
    params = request.args.to_dict(flat=False)
    params.pop('token', None)

    if not token:
        return jsonify({'error': 'Invalid data structure'}), 400
    if not isinstance(token, str):
        return jsonify({'error': 'Invalid data types'}), 400
    
    if not is_hex(token):
        return jsonify({'error': 'Token not hexadecimal'}), 401
    if not is_valid_token(token):
        return jsonify({'error': 'Invalid token'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Build the SQL query dynamically based on the provided parameters
    query = """
    SELECT q.*, ui.name AS username, ui.academy AS user_academy
    FROM quiz q
    JOIN user_infos ui ON q.id_acc = ui.id_acc
    WHERE 1=1
    """
    query_params = []

    for key, value in params.items():
        if value:
            if key == "id_acc":
                value = [v for v in value if v.isdigit()]
                if value != []:
                    query += f" AND q.id_acc = %s"
                    query_params.append(int(value[0]))
            elif key == "id_question":
                value = [v for v in value if v.isdigit()]
                if value != []:
                    query += f" AND id_question = %s"
                    query_params.append(int(value[0]))
            else:
                query += f" AND {key} LIKE %s"
                if value != []:
                    query_params.append(f"%{value[0]}%")

    try:
        cursor.execute(query, query_params)
    except mysql.connector.Error as err:
        return jsonify({'error': f"{err}"}), 500

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
    token = request.args.get('token')
    params = request.args.to_dict(flat=False)
    params.pop('token', None)

    if not token:
        return jsonify({'error': 'Invalid data structure'}), 400
    if not isinstance(token, str):
        return jsonify({'error': 'Invalid data types'}), 400
    
    if not is_hex(token):
        return jsonify({'error': 'Token not hexadecimal'}), 401
    if not is_valid_token(token):
        return jsonify({'error': 'Invalid token'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Build the SQL query dynamically based on the provided parameters
    query = """
    SELECT qp.*, qc.title, qc.correct_answers, qc.shown_answers, qc.duration, qc.type, ui.name AS username, ui.academy AS user_academy
    FROM question_posts qp
    JOIN question_contents qc ON qp.id_question = qc.id_question
    JOIN user_infos ui ON qp.id_acc = ui.id_acc
    WHERE 1=1
    """
    query_params = []

    for key, value in params.items():
        if value:
            if key in ["id_question", "id_acc"]:
                value = [v for v in value if v.isdigit()]
                if value != []:
                    query += f" AND qp.{key} = %s"
                    query_params.append(int(value[0]))
            else:
                query += f" AND {key} LIKE %s"
                if value != []:
                    query_params.append(f"%{value[0]}%")

    try:
        cursor.execute(query, query_params)
    except mysql.connector.Error as err:
        return jsonify({'error': f"{err}"}), 500 
    except:
        raise RuntimeError("Curious error")
    
    rows = cursor.fetchall()

    for row in rows:
        if 'shown_answers' in row:
            row['shown_answers'] = parse_answers(row['shown_answers'])
        if 'correct_answers' in row:
            row['correct_answers'] = parse_answers(row['correct_answers'])

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
    token = request.args.get('token')
    id_question = request.args.get('id_question')

    if not token:
        return jsonify({'error': 'Invalid data structure'}), 400
    if not isinstance(token, str) or not id_question.isdigit():
        return jsonify({'error': 'Invalid data types'}), 400
    
    if not is_hex(token):
        return jsonify({'error': 'Token not hexadecimal'}), 401
    if not is_valid_token(token):
        return jsonify({'error': 'Invalid token'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM question_contents WHERE id_question = %s", (id_question,))
    rows = cursor.fetchall()

    for row in rows:
        row['shown_answers'] = parse_answers(row['shown_answers'])
        row['correct_answers'] = parse_answers(row['correct_answers'])

    cursor.close()
    conn.close()
    return jsonify(rows), 200

@app.route('/myposts', methods=['GET'])
def get_myposts():
    """
    Retrieves all posts by the user based on the provided token.

    Returns:
        Response: A JSON response containing the posts or an error message.
    """
    token = request.args.get('token')

    if not token:
        return jsonify({'error': 'Invalid data structure'}), 400
    if not isinstance(token, str):
        return jsonify({'error': 'Invalid data type for token'}), 400
    
    if not is_hex(token):
        return jsonify({'error': 'Token not hexadecimal'}), 401
    if not is_valid_token(token):
        return jsonify({'error': 'Invalid token'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT qp.*, qc.* FROM question_posts qp JOIN question_contents qc ON qp.id_question = qc.id_question WHERE id_acc IN (SELECT id_acc FROM connexions WHERE token = %s)", (pad_binary_data(bytes.fromhex(token), 32),))
    questions = cursor.fetchall()
    cursor.execute("SELECT * FROM quiz WHERE id_acc IN (SELECT id_acc FROM connexions WHERE token = %s)", (pad_binary_data(bytes.fromhex(token), 32),))
    quizzes = cursor.fetchall()

    for question in questions:
        question['shown_answers'] = parse_answers(question['shown_answers'])
        question['correct_answers'] = parse_answers(question['correct_answers'])

    cursor.close()
    conn.close()
    return jsonify({'questions': questions, 'quizzes': quizzes}), 200

def verify_xml_structure(xml_file) -> bool:
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        if root.tag != 'quiz':
            return False

        questions_sections = root.findall('questions')
        if not questions_sections:
            return False

        for questions in questions_sections:
            question_list = questions.findall('question')

            for question in question_list:
                if 'type' not in question.attrib or 'duration' not in question.attrib:
                    return False

                if question.find('title') is None or \
                   question.find('shown_answers') is None or \
                   question.find('correct_answers') is None:
                    return False

        return True
    except ET.ParseError:
        print('ET.ParseError')
        return False

def get_quiz_subject_and_language(xml_file):
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        subject = root.find('subject').text
        language = root.find('language').text
        return (subject, language)
    except:
        return (None, None)

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

    conn = get_db_connection()
    cursor = conn.cursor()

    # Save the file
    cursor.execute("SELECT MAX(id_file) FROM quiz")
    max_id_file = cursor.fetchone()[0] or 0
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], str(max_id_file + 1))
    file.save(file_path)

    conn.commit()
    cursor.close()
    conn.close()

    # Verify the XML structure and get the quiz subject and language
    with open(file_path, 'r') as f:
        if not verify_xml_structure(f):
            return jsonify({'error': 'Invalid XML structure'}), 400
    with open(file_path, 'r') as f:
        subject, language = get_quiz_subject_and_language(f)

    if subject is None or language is None:
        os.remove(file_path)
        return jsonify({'error': 'Missing subject or language'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Save file data to the database
    cursor.execute("INSERT INTO quiz (id_file, name, id_acc, subject, language) VALUES (%s, %s, (SELECT id_acc FROM connexions WHERE token = %s), %s, %s)", (max_id_file + 1, filename, pad_binary_data(bytes.fromhex(token), 32), subject, language))

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

    # Convert shown_answers and correct_answers to lists
    shown_answers = parse_answers(question['shown_answers'])
    correct_answers = parse_answers(question['correct_answers'])
    if isinstance(shown_answers, dict) and "answer" in shown_answers:
        shown_answers = shown_answers["answer"]
    if isinstance(correct_answers, dict) and "answer" in correct_answers:
        correct_answers = correct_answers["answer"]
    question['shown_answers'] = str(shown_answers)
    question['correct_answers'] = str(correct_answers)

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

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO question_posts (id_acc, subject, language) VALUES ((SELECT id_acc FROM connexions WHERE token = %s), %s, %s)", (pad_binary_data(bytes.fromhex(token), 32), question['subject'], question['language'],))
    cursor.execute("INSERT INTO question_contents (id_question, title, shown_answers, correct_answers, duration, type) VALUES (LAST_INSERT_ID(), %s, %s, %s, %s, %s)", (question['title'], json.dumps(shown_answers), json.dumps(correct_answers), question['duration'], question['type'],))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'message': 'Question uploaded successfully'}), 200

@app.route('/login', methods=['POST']) 
def post_login():
    """Handles user login with token management"""
    data = request.get_json()
    email = data.get('email')
    password_hash = data.get('password_hash')

    if not email or not password_hash:
        return jsonify({'error': 'Invalid data structure'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify credentials
    cursor.execute("SELECT * FROM accounts WHERE email = %s", (email,))
    account = cursor.fetchone()
    if not account or not check_password_hash(account[2], password_hash):
        return jsonify({'error': 'Invalid email or password'}), 401

    # Generate new token
    new_token = secrets.token_bytes(32)
    
    # Update or insert token
    cursor.execute("SELECT token FROM connexions WHERE id_acc = %s", (account[0],))
    existing_token = cursor.fetchone()
    
    if existing_token:
        # Update existing token entry
        cursor.execute("UPDATE connexions SET token = %s WHERE id_acc = %s", 
                      (new_token, account[0]))
    else:
        # Create new token entry
        cursor.execute("INSERT INTO connexions (id_acc, token) VALUES (%s, %s)",
                      (account[0], new_token))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'token': new_token.hex()}), 200

def get_email_config():
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
        if 'email' in config:
            return {
                'sender': config.get('email', 'sender'),
                'password': config.get('email', 'password'),
                'smtp_server': config.get('email', 'smtp_server'),
                'smtp_port': config.getint('email', 'smtp_port')
            }
    
    # If the section does not exist or the file does not exist, ask the user for input
    email = input("Email: ")
    password = input("Email Password: ")
    smtp_server = input("SMTP Server: ")
    smtp_port = int(input("SMTP Port: "))

    config.add_section('email')
    config.set('email', 'sender', email)
    config.set('email', 'password', password)
    config.set('email', 'smtp_server', smtp_server)
    config.set('email', 'smtp_port', str(smtp_port))

    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)

    return {
        'sender': email,
        'password': password,
        'smtp_server': smtp_server,
        'smtp_port': smtp_port
    }

email_config = get_email_config()
def send_email(subject, message, recipient):
    sender = email_config['sender']
    password = email_config['password']
    smtp_server = email_config['smtp_server']
    smtp_port = email_config['smtp_port']

    # SMTP server configuration
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()  # Pour activer TLS

    # Login to the server
    server.login(sender, password)

    # Create the email
    email = MIMEMultipart()
    email["From"] = sender
    email["To"] = recipient
    email["Subject"] = subject

    # Attach the HTML message body
    email.attach(MIMEText(message, "html"))

    # Send the email
    server.send_message(email)

    # Disconnect
    server.quit()

def is_authorized_email(email):
    with open('authorized_emails.json', 'r') as f:
        authorized_emails = json.load(f)
    for e in authorized_emails:
        if e in email:
            return True
    return False

@app.route('/signup', methods=['POST'])
def post_signup():
    """
    Registers a new user by saving their email and password hash to the database.

    Returns:
        Response: A JSON response indicating success or an error message.
    """
    data = request.get_json()
    email = data.get('email')
    password_hash = data.get('password_hash') # Hash from client

    if password_hash == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855":
        return jsonify({'error': 'Password can\'t be empty'}), 400

    if not email or not password_hash:
        return jsonify({'error': 'Invalid data structure'}), 400
    
    if not isinstance(email, str):
        return jsonify({'error': 'Invalid data type for email'}), 400
    if not is_authorized_email(email):
        return jsonify({'error': 'Unauthorized email'}), 401
    
    if not isinstance(password_hash, str):
        return jsonify({'error': 'Invalid data type for password_hash'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM accounts WHERE email = %s", (email,))
    rows = cursor.fetchall()
    if(len(rows) > 0):
        return jsonify({'error': 'Email already in use'}), 409
    
    # Add salt and hash again for storage
    salted_hash = hashlib.sha256((password_hash + salt).encode()).hexdigest()
    
    cursor.execute("INSERT INTO accounts (email, password_hash) VALUES (%s, %s)", 
                  (email, salted_hash))
    
    cursor.execute("INSERT INTO user_infos (id_acc, name, academy) VALUES ((SELECT id_acc FROM accounts WHERE email = %s), %s, %s)", (email, "", ""))
    token = secrets.token_bytes(32)
    cursor.execute("INSERT INTO verifications (id_acc, token, type) VALUES ((SELECT id_acc FROM accounts WHERE email = %s), %s, %s)", (email, token, 'signup'))

    html_message = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f4;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    width: 100%;
                    background-color: #ffffff;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    background-color: #424242;
                    color: white;
                    text-align: center;
                    padding-top: 10px;
                    padding-bottom: 10px;
                }}
                .content {{
                    padding: 20px;
                }}
                .content h1 {{
                    color: #333333;
                }}
                .content p {{
                    color: #666666;
                    line-height: 1.5;
                }}
                .button {{
                    display: inline-block;
                    padding: 10px 20px;
                    margin: 20px 0;
                    background-color: #424242;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                }}
                .footer {{
                    text-align: center;
                    padding: 10px;
                    color: #999999;
                    font-size: 12px;
                }}
                img {{
                    width: 200px;
                    height: 200px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>You're almost member of the kahiin-db!</h1>
                </div>
                <div class="content">
                    <h1>Thank you for signing up!</h1>
                    <p>We are excited to have you on board. Click the button below to verify your account and get started:</p>
                    <a href="http://localhost:5000/verif?token={token.hex()}" class="button" style="color:white;">Verify Your Account</a>
                </div>
                <div class="footer">
                    <p>If you did not sign up for this account, please ignore this email.</p>
                </div>{token.hex()}
            </div>
        </body>
        </html>
    """

    send_email("Account Verification", html_message, email)

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'message': 'Email sent successfully'}), 200

@app.route('/reset-password', methods=['POST'])
def post_reset_password():
    """
    Sends a password reset email to the user based on their email.

    Returns:
        Response: A JSON response indicating success or an error message.
    """
    data = request.get_json()
    token = data.get('token')

    if not token:
        return jsonify({'error': 'Invalid data structure'}), 400
    if not is_hex(token):
        return jsonify({'error': 'Token not hexadecimal'}), 401
    if not is_valid_token(token):
        return jsonify({'error': 'Invalid token'}), 401

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT email FROM accounts WHERE id_acc IN (SELECT id_acc FROM connexions WHERE token = %s)", (pad_binary_data(bytes.fromhex(token), 32),))
    email = cursor.fetchone()[0]

    if not email:
        return jsonify({'error': 'Email not found'}), 404
    
    new_password_hash = data.get('new_password_hash') # Hash from client
    salted_hash = hashlib.sha256((new_password_hash + salt).encode()).hexdigest()

    if not new_password_hash:
        return jsonify({'error': 'New password hash is required'}), 400
    if not isinstance(new_password_hash, str):
        return jsonify({'error': 'Invalid data type for new_password_hash'}), 400
    
    token = secrets.token_bytes(32)
    cursor.execute("INSERT INTO verifications (id_acc, token, type) VALUES ((SELECT id_acc FROM accounts WHERE email = %s), %s, %s)", (email, token, 'reset_password'))
    # Check if an entry already exists in waiting_passwords
    cursor.execute("SELECT id_acc FROM waiting_passwords WHERE id_acc = (SELECT id_acc FROM accounts WHERE email = %s)", (email,))
    existing_entry = cursor.fetchone()
    salted_hash = hashlib.sha256((new_password_hash + salt).encode()).hexdigest()
    if existing_entry:
        cursor.execute("UPDATE waiting_passwords SET password_hash = %s WHERE id_acc = %s", (salted_hash, existing_entry[0]))
    else:
        cursor.execute("INSERT INTO waiting_passwords (id_acc, password_hash) VALUES ((SELECT id_acc FROM accounts WHERE email = %s), %s)", (email, salted_hash))

    html_message = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f4;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    width: 100%;
                    background-color: #ffffff;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    background-color: #424242;
                    color: white;
                    text-align: center;
                    padding-top: 10px;
                    padding-bottom: 10px;
                }}
                .content {{
                    padding: 20px;
                }}
                .content h1 {{
                    color: #333333;
                }}
                .content p {{
                    color: #666666;
                    line-height: 1.5;
                }}
                .button {{
                    display: inline-block;
                    padding: 10px 20px;
                    margin: 20px 0;
                    background-color: #424242;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                }}
                .footer {{
                    text-align: center;
                    padding: 10px;
                    color: #999999;
                    font-size: 12px;
                }}
                img {{
                    width: 200px;
                    height: 200px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Reset Your Password</h1>
                </div>
                <div class="content">
                    <h1>Forgot your password?</h1>
                    <p>Click the button below to reset your password:</p>
                    <a href="http://localhost:5000/verif?token={token.hex()}" class="button" style="color:white;">Reset Password</a>
                </div>
                <div class="footer">
                    <p>If you did not request a password reset, please ignore this email.</p>
                </div>
            </div>
        </body>
        </html>
    """

    send_email("Password Reset", html_message, email)

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'message': 'Email sent successfully'}), 200

@app.route('/editInfos', methods=['POST'])
def post_edit_infos():
    """
    Edit a user info in the database based on the provided information (name and academy).

    Returns:
        Response: A JSON response indicating success or an error message.
    """
    data = request.get_json()
    token = data.get('token')
    name = data.get('name')
    academy = data.get('academy')
    
    if not token:
        return jsonify({'error': 'Invalid data structure'}), 400
    if not is_hex(token):
        return jsonify({'error': 'Token not hexadecimal'}), 401
    if not is_valid_token(token):
        return jsonify({'error': 'Invalid token'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE user_infos SET name = %s , academy = %s WHERE id_acc IN (SELECT id_acc FROM connexions WHERE token = %s)", (name, academy, pad_binary_data(bytes.fromhex(token), 32),))

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': "Account's informations  edited successfully"}), 200

@app.route('/getInfos', methods=['POST'])
def get_infos():
    """
    Get a user info from the database based on the provided token.

    Returns:
        Response: A JSON response with the user informations.
    """
    data = request.get_json()
    token = data.get('token')
    
    if not token:
        return jsonify({'error': 'Invalid data structure'}), 400
    if not is_hex(token):
        return jsonify({'error': 'Token not hexadecimal'}), 401
    if not is_valid_token(token):
        return jsonify({'error': 'Invalid token'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name, academy FROM user_infos WHERE id_acc IN (SELECT id_acc FROM connexions WHERE token = %s)", (pad_binary_data(bytes.fromhex(token), 32),))
    informations = cursor.fetchone()
    name = informations[0]
    academy = informations[1]

    cursor.close()
    conn.close()
    return jsonify({'name': name, 'academy': academy}), 200


# Modifier la route delete account  
@app.route('/account', methods=['DELETE']) 
def delete_account():
    """
    Deletes a user account based on the provided token and password.

    Returns:
        Response: A JSON response indicating success or an error message.
    """
    data = request.json
    token = data.get('token')
    password_hash = data.get('password') # Hash from client
    
    if not token or not password_hash:
        return jsonify({'error': 'Invalid data structure'}), 400
    if not isinstance(token, str) or not isinstance(password, str):
        return jsonify({'error': 'Invalid data type for token or password'}), 400

    if not is_hex(token):
        return jsonify({'error': 'Token not hexadecimal'}), 401
    if not is_valid_token(token):
        return jsonify({'error': 'Invalid token'}), 401

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT password_hash FROM accounts WHERE id_acc IN (SELECT id_acc FROM connexions WHERE token = %s)", 
                  (pad_binary_data(bytes.fromhex(token), 32),))
    stored_hash = cursor.fetchone()[0]

    if not check_password_hash(stored_hash, password_hash):
        return jsonify({'error': 'Invalid password'}), 401

    cursor.execute("DELETE FROM accounts WHERE id_acc IN (SELECT id_acc FROM connexions WHERE token = %s)", (pad_binary_data(bytes.fromhex(token), 32),))

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

    if not is_hex(token):
        return jsonify({'error': 'Token not hexadecimal'}), 401
    if not is_valid_token(token):
        return jsonify({'error': 'Invalid token'}), 401

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM quiz WHERE id_file = %s", (id_file,))
    rows = cursor.fetchall()
    if len(rows) == 0:
        return jsonify({'error': 'Quiz not found'}), 404

    cursor.execute("SELECT c.id_acc FROM connexions c JOIN quiz q ON c.id_acc = q.id_acc WHERE q.id_file = %s AND c.token = %s", (id_file, pad_binary_data(bytes.fromhex(token), 32),))
    rows = cursor.fetchall()
    if len(rows) == 0:
        return jsonify({'error': 'Unauthorized to delete quiz'}), 401

    cursor.execute("DELETE FROM quiz WHERE id_file = %s", (id_file,))

    # Delete the file from the quizFiles directory
    file_path = os.path.join('quizFiles', f'{id_file}')
    if os.path.exists(file_path):
        os.remove(file_path)

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

    if not is_hex(token):
        return jsonify({'error': 'Token not hexadecimal'}), 401
    if not is_valid_token(token):
        return jsonify({'error': 'Invalid token'}), 401

    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM question_posts WHERE id_question = %s", (id_question,))
    rows = cursor.fetchall()
    if len(rows) == 0:
        return jsonify({'error': 'Question not found'}), 404

    cursor.execute("SELECT c.id_acc FROM connexions c JOIN question_posts q ON c.id_acc = q.id_acc WHERE q.id_question = %s AND c.token = %s", (id_question, pad_binary_data(bytes.fromhex(token), 32),))
    rows = cursor.fetchall()
    if len(rows) == 0:
        return jsonify({'error': 'Unauthorized to delete question'}), 401

    cursor.execute("DELETE FROM question_posts WHERE id_question = %s", (id_question,))

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Question deleted successfully'}), 200

@app.route('/verif', methods=['GET'])
def verification_attempt():
    """
    Verifies the account based on the provided token.
    """
    token = request.args.get('token')
    if not token:
        return jsonify({'error': 'Token is required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM verifications WHERE token = %s", (pad_binary_data(bytes.fromhex(token), 32), ))
    rows = cursor.fetchall()
    if len(rows) == 0:
        return jsonify({'error': 'Invalid token'}), 401
    
    type = rows[0][2]

    match(type):
        case 'signup':
            cursor.execute("DELETE FROM verifications WHERE token = %s", (pad_binary_data(bytes.fromhex(token), 32),))
            cursor.execute("INSERT INTO connexions (id_acc, token) VALUES (%s, %s)", (rows[0][0], pad_binary_data(bytes.fromhex(token), 32),))
            conn.commit()
            cursor.close()
            conn.close()
            return render_template("account_created.html"), 200
        case 'reset_password':
            cursor.execute("DELETE FROM verifications WHERE token = %s", (pad_binary_data(bytes.fromhex(token), 32),))
            cursor.execute("SELECT password_hash FROM waiting_passwords WHERE id_acc = %s", (rows[0][0],))
            new_password_hash = cursor.fetchone()[0]
            cursor.execute("UPDATE accounts SET password_hash = %s WHERE id_acc = %s", (new_password_hash, rows[0][0]))
            cursor.execute("DELETE FROM waiting_passwords WHERE id_acc = %s", (rows[0][0],))
            cursor.execute("UPDATE connexions SET token = %s WHERE id_acc = %s", (pad_binary_data(secrets.token_bytes(32), 32), rows[0][0]))
            conn.commit()
            cursor.close()
            conn.close()
            return render_template("password_reset.html"), 200
        case _:
            return jsonify({'error': 'Invalid type'}), 400

@app.route('/download', methods=['GET'])
def download():
    """
    Downloads a quiz file based on the provided quiz ID and token.

    Returns:
        Response: A file download response or an error message.
    """
    token = request.args.get('token')
    id_file = request.args.get('id_file')
    if not token or not id_file:
        return jsonify({'error': 'Token and Quiz ID are required'}), 400

    if not is_hex(token):
        return jsonify({'error': 'Token not hexadecimal'}), 401
    if not is_valid_token(token):
        return jsonify({'error': 'Invalid token'}), 401

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM quiz WHERE id_file = %s", (id_file,))
    rows = cursor.fetchall()
    if len(rows) == 0:
        return jsonify({'error': 'Quiz not found'}), 404

    cursor.close()
    conn.close()
    return send_file(f'quizFiles/{id_file}', as_attachment=True)

if __name__ == '__main__':
    kbf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'',
        iterations=400000,
    )
    key = base64.urlsafe_b64encode(kbf.derive(password.encode()))
    if not password:
        print("No password provided")
        sys.exit(1)
    if not os.path.exists('.passwordcheck'):
        fernet = Fernet(key)
        encrypted = fernet.encrypt((password + str(uuid.getnode())).encode())
        with open('.passwordcheck', 'w') as f:
            f.write(encrypted.decode())
        with open('.passwordcheck', 'w') as f:
            f.write(encrypted.decode())
    with open('.passwordcheck', 'r') as f:
        fernet = Fernet(key)
        try:
            decrypted = fernet.decrypt(f.read().encode())
        except:
            print("Invalid password")
            sys.exit(1)
        salt = hashlib.sha256(password.encode()).hexdigest()
    
    print("Password is correct", salt)
    app.run(host="0.0.0.0", port=5000, threaded=True, debug=True)

