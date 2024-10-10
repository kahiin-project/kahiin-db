from flask import Flask, jsonify
from flask_mysqldb import MySQL

app = Flask(__name__)

# Configuration de la connexion MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'yourusername'
app.config['MYSQL_PASSWORD'] = 'yourpassword'
app.config['MYSQL_DB'] = 'yourdatabase'

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