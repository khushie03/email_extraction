import os
from flask import Flask, render_template, request, redirect, url_for, session, send_file
from werkzeug.utils import secure_filename
import mysql.connector
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

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/user')
def user():
    return render_template('user.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'pdf_file' not in request.files:
        return redirect(request.url)
    file = request.files['pdf_file']
    name = request.form['name']
    email = request.form['email']
    
    print(f"Received file: {file.filename}, Name: {name}, Email: {email}")  

    if file.filename == '':
        return redirect(request.url)
    if file and file.filename.endswith('.pdf'):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        summary_file_path = extraction_and_summarization(file_path)
        session['summary_file_path'] = summary_file_path
        session['name'] = name
        session['email'] = email
        return redirect(url_for('result'))

@app.route('/result', methods=['GET', 'POST'])
def result():
    name = session.get('name')
    email = session.get('email')
    summary_file_path = session.get('summary_file_path', '')

    if isinstance(summary_file_path, tuple):
        summary_file_path = summary_file_path[0]

    if summary_file_path:
        with open(summary_file_path, 'r', encoding='utf-8') as file:
            summary_text = file.read()
        token_count_value = token_count(summary_text)
        print(f"Name: {name}, Email: {email}, Token Count: {token_count_value}")  
        insert_user(name, email, token_count_value)  
    else:
        return "Summary file path not found."

    return render_template('result.html', text=summary_text, token_count=token_count_value)


@app.route('/download')
def download_file():
    summary_file_path = session.get('summary_file_path', '')
    if summary_file_path:
        return send_file(summary_file_path, as_attachment=True)
    return redirect(url_for('result'))
    
def insert_user(name, email, number_of_tokens):
    cursor = cnx.cursor()
    query = """INSERT INTO user_details (name, email_id, number_of_tokens) 
               VALUES (%s, %s, %s)"""
    cursor.execute(query, (name, email, number_of_tokens))
    cnx.commit()
    cursor.close()
    print("User inserted successfully.") 
    return 1

@app.route('/send_emails')
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
def admin():
    cursor = cnx.cursor(dictionary=True)
    cursor.execute("SELECT * FROM user_details")
    users = cursor.fetchall()
    cursor.close()
    return render_template('admin.html', users=users)


if __name__ == '__main__':
    app.run(debug=True)
