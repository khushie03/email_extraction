import os
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
import mysql.connector
from summarizer import token_count
from main import extraction_and_summarization

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = 'supersecretkey'

# Establishing connection to MySQL database
cnx = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Prusshita@1234",
    database="email_extractor"  # Adjust database name as per your setup
)

# Creating table if not exists
create_table_query = """
CREATE TABLE IF NOT EXISTS user_details (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_type VARCHAR(50) NOT NULL,
    password VARCHAR(100) NOT NULL,
    number_of_tokens INT DEFAULT 0,
    session_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    file_name VARCHAR(255) NOT NULL
);
"""
cursor = cnx.cursor()
cursor.execute(create_table_query)
cursor.close()
cnx.commit()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    # Dummy login logic for demonstration
    user_type = request.form['user_type']
    password = request.form['password']

    # Assuming a simple check, replace with secure authentication logic
    if user_type == 'admin' and password == 'adminpass':
        session['user_type'] = user_type
        return redirect(url_for('user_data'))
    elif user_type == 'user' and password == 'userpass':
        session['user_type'] = user_type
        return redirect(url_for('user_data'))
    else:
        return "Invalid credentials. Please try again."

@app.route('/user_data')
def user_data():
    return render_template('user_data.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'pdf_file' not in request.files:
        return redirect(request.url)

    file = request.files['pdf_file']
    user_type = session.get('user_type')
    password = 'dummy'  # Password should ideally be fetched from session or database

    if file.filename == '':
        return redirect(request.url)

    if file and file.filename.endswith('.pdf'):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        summary_file_path = extraction_and_summarization(file_path)
        session['summary_file_path'] = summary_file_path
        session['file_name'] = filename

        return redirect(url_for('result'))

@app.route('/result', methods=['GET', 'POST'])
def result():
    user_type = session.get('user_type')
    password = 'dummy'  # Password should ideally be fetched from session or database

    summary_file_path = session.get('summary_file_path', '')
    file_name = session.get('file_name', '')

    cursor = cnx.cursor(dictionary=True)
    query = """SELECT password FROM login_status WHERE user_type = %s"""
    cursor.execute(query, (user_type,))
    result = cursor.fetchone()

    if result is None:
        cursor.close()
        return "User type not found."

    if password != result['password']:
        cursor.close()
        return "Incorrect password."

    if summary_file_path:
        with open(summary_file_path, 'r', encoding='utf-8') as file:
            summary_text = file.read()

        token_count_value = token_count(summary_text)
        print(f"User Type: {user_type}, Token Count: {token_count_value}")

        # Inserting user details into the database
        query_insert = """INSERT INTO user_details (user_type, password, number_of_tokens, file_name) 
                          VALUES (%s, %s, %s, %s)"""
        cursor.execute(query_insert, (user_type, password, token_count_value, file_name))
        cnx.commit()
        cursor.close()

        if user_type == 'admin':
            return redirect(url_for('admin'))
        else:
            return render_template('result.html', text=summary_text, token_count=token_count_value)
    else:
        cursor.close()
        return "Summary file path not found."

@app.route('/admin')
def admin():
    cursor = cnx.cursor(dictionary=True)
    cursor.execute("SELECT * FROM user_details")
    users = cursor.fetchall()
    cursor.close()
    return render_template('admin.html', users=users)

if __name__ == '__main__':
    app.run(debug=True)
