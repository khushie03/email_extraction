import os
from flask import Flask, render_template, request, redirect, url_for, session, send_file
from werkzeug.utils import secure_filename
import mysql.connector
from summarizer import token_count
from main import extraction_and_summarization

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = 'supersecretkey'

cnx = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Prusshita@1234",
    database="email_extractor"
)

def insert_user(name, email, number_of_tokens):
    try:
        cursor = cnx.cursor()
        query = """INSERT INTO user_details (name, email_id, number_of_tokens) 
                   VALUES (%s, %s, %s)"""
        cursor.execute(query, (name, email, number_of_tokens))
        cnx.commit()
        cursor.close()
        return 1
    except mysql.connector.Error as err:
        print("MySQL error occurred:", err)
        return -1
    except Exception as e:
        print(f"An error occurred: {e}")
        cnx.rollback()
        return -1

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/user')
def user():
    return render_template('user.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'pdf_file' not in request.files:
        return redirect(request.url)

    file = request.files['pdf_file']
    if file.filename == '':
        return redirect(request.url)

    if file and file.filename.endswith('.pdf'):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        summary_file_path = extraction_and_summarization(file_path)
        session['summary_file_path'] = summary_file_path

        return redirect(url_for('result'))

@app.route('/result', methods=['GET', 'POST'])
def result():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        summary_file_path = session.get('summary_file_path', '')

        if isinstance(summary_file_path, tuple):
            summary_file_path = summary_file_path[0]

        if summary_file_path:
            with open(summary_file_path, 'r', encoding='utf-8') as file:
                summary_text = file.read()

            token_count_value = token_count(summary_text)
            insert_user(name, email, token_count_value)

            return redirect(url_for('thank_you'))
    else:
        summary_file_path = session.get('summary_file_path', '')

        if isinstance(summary_file_path, tuple):
            summary_file_path = summary_file_path[0]

        if summary_file_path:
            with open(summary_file_path, 'r', encoding='utf-8') as file:
                summary_text = file.read()

            token_count_value = token_count(summary_text)
        else:
            summary_text = 'No summary available.'
            token_count_value = 0

        return render_template('result.html', text=summary_text, token_count=token_count_value)

@app.route('/thank_you')
def thank_you():
    return render_template('thank_you.html')

@app.route('/download')
def download_file():
    summary_file_path = session.get('summary_file_path', '')

    if summary_file_path:
        return send_file(summary_file_path, as_attachment=True)

    return redirect(url_for('result'))

if __name__ == '__main__':
    app.run(debug=True)
