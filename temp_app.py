import os
from flask import Flask, render_template, request, redirect, url_for, session, send_file
from werkzeug.utils import secure_filename
import mysql.connector
from functools import wraps
from summarizer import token_count
from main import extraction_and_summarization
from send_message import send_message

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = 'supersecretkey'

cnx = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Prusshita@1234",
    database="email_extractor"
)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_type' not in session or 'password' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_type = request.form['user_type']
        password = request.form['password']
        session['user_type'] = user_type
        session['password'] = password

        cursor = cnx.cursor(dictionary=True)
        query = """SELECT Password FROM login_status WHERE user_type = %s"""
        cursor.execute(query, (user_type,))
        result = cursor.fetchone()
        
        if result is None:
            cursor.close()
            return "User type not found."
        
        if password != result['Password']:
            cursor.close()
            return "Incorrect password."
        
        cursor.close()
        
        if user_type == 'admin':
            return redirect(url_for('admin'))
        else:
            return redirect(url_for('user_data'))
    else:
        return render_template('user.html')

@app.route('/user', methods=['GET', 'POST'])
def user():
    if request.method == 'POST':
        user_type = request.form['user_type']
        password = request.form['password']
        session['user_type'] = user_type
        session['password'] = password

        cursor = cnx.cursor(dictionary=True)
        query = """SELECT Password FROM login_status WHERE user_type = %s"""
        cursor.execute(query, (user_type,))
        result = cursor.fetchone()
        
        if result is None:
            cursor.close()
            return "User type not found."
        
        if password != result['Password']:
            cursor.close()
            return "Incorrect password."
        
        cursor.close()
        if user_type == 'admin':
            return redirect(url_for('admin'))
        else:
            return redirect(url_for('user_data'))
    else:
        return render_template('user.html')

@app.route('/result', methods=['GET', 'POST'])
@login_required
def result():
    user_type = session.get('user_type')
    password = session.get('password')
    filename = session.get('filename')
    summary_file_path = session.get('summary_file_path', '')
    if user_type != 'admin':
        redirect(url_for('login'))
    if user_type != 'user':
        redirect(url_for('login'))
    if isinstance(summary_file_path, tuple):
        summary_file_path = summary_file_path[0]
    cursor = cnx.cursor(dictionary=True)
    query = """SELECT Password FROM login_status WHERE user_type = %s"""
    cursor.execute(query, (user_type,))
    result = cursor.fetchone()
    
    if result is None:
        cursor.close()
        return "User type not found."
    
    if password != result['Password']:
        cursor.close()
        return "Incorrect password."
    if summary_file_path:
        with open(summary_file_path, 'r', encoding='utf-8') as file:
            summary_text = file.read()
        token_count_value = token_count(summary_text)
        print(f"User Type: {user_type}, Token Count: {token_count_value}")
        if filename:
            query_insert = """INSERT INTO user_details (user_type, password, number_of_tokens, session_time, file_name) 
                              VALUES (%s, %s, %s, CURRENT_TIMESTAMP, %s)"""
            cursor.execute(query_insert, (user_type, password, token_count_value, filename))
            cnx.commit()
        else:
            cursor.close()
            return "Filename is missing or invalid."

        cursor.close()
        print(f"Received file: {filename}, User Type: {user_type}")
        if user_type == 'admin':
            return redirect(url_for('admin'))
        else:
            return render_template('result.html', text=summary_text, token_count=token_count_value)
    else:
        cursor.close()
        return "Summary file path not found."

@app.route('/user_data', methods=['GET', 'POST'])
@login_required
def user_data():
    if request.method == 'POST':
        session['user_type'] = request.form['user_type']
        session['password'] = request.form['password']
        return redirect(url_for('summarizer'))
    else:
        
        return render_template('user_data.html')

@app.route('/user_selected', methods=['GET'])
@login_required
def user_selected():
    if session.get('user_type') != 'user':
        return redirect(url_for('login'))
    password = session.get('password')
    cursor = cnx.cursor(dictionary=True)
    cursor.execute(f"SELECT id, number_of_tokens, session_time, file_name FROM user_details WHERE password = %s", (password,))
    users = cursor.fetchall()
    cursor.close()
    return render_template('user_selected.html', users=users)

@app.route('/summarizer', methods=['GET', 'POST'])
@login_required
def summarizer():
    if request.method == 'POST':
        if 'pdf_file' not in request.files:
            return "No file part"
        file = request.files['pdf_file']
        if file.filename == '':
            return "No selected file"
        if file and file.filename.endswith('.pdf'):
            
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            summary_text = extraction_and_summarization(file_path)
            summary_file_path = os.path.join(app.config['UPLOAD_FOLDER'], f'summary_{filename}.txt')
            with open(summary_file_path, 'w', encoding='utf-8') as summary_file:
                summary_file.write(summary_text)
            
            session['filename'] = filename
            session['summary_file_path'] = summary_file_path
            session['summary_text'] = summary_text
            
            user_type = session.get('user_type')
            password = session.get('password')
            token_count_value = token_count(summary_text)

            cursor = cnx.cursor()
            query_insert = """INSERT INTO user_details (user_type, password, number_of_tokens, session_time, file_name) 
                              VALUES (%s, %s, %s, CURRENT_TIMESTAMP, %s)"""
            cursor.execute(query_insert, (user_type, password, token_count_value, filename))
            cnx.commit()
            cursor.close()
            
            return render_template('summarizer.html', summary_text=summary_text, summary_file_path=summary_file_path)
    
    session.pop('summary_text', None)
    session.pop('summary_file_path', None)
    
    return render_template('summarizer.html', summary_text='')

@app.route('/download')
@login_required
def download_file():
    summary_file_path = session.get('summary_file_path', '')
    if summary_file_path:
        return send_file(summary_file_path, as_attachment=True)
    return redirect(url_for('result'))

@app.route('/send_emails')
@login_required
def send_emails():
    cursor = cnx.cursor()
    cursor.execute("SELECT name, email_id, number_of_tokens FROM user_details")
    users = cursor.fetchall()
    cursor.close()

    for user in users:
        name, email, token_count_value = user
        send_message(name, email, token_count_value)
    return "Emails sent successfully."

@app.route('/admin')
@login_required
def admin():
    if session.get('user_type') != 'admin':
        return redirect(url_for('login'))
    cursor = cnx.cursor(dictionary=True)
    cursor.execute("SELECT * FROM user_details")
    users = cursor.fetchall()
    cursor.close()
    return render_template('admin.html', users=users)

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
