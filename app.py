from flask import Flask, jsonify
from flask_mysqldb import MySQL
from dotenv import load_dotenv
import os

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

app = Flask(__name__)

# Configuration de la connexion MySQL en utilisant les variables d'environnement
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')

mysql = MySQL(app)

@app.route('/')
def index():
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM yourtable''')
    results = cur.fetchall()
    cur.close()
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True, port=443)
