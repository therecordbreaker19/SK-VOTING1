from flask import Flask, render_template, request, session, redirect, url_for
import sqlite3
import hashlib
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired
import os 

app = Flask(__name__)

# Your other routes and functions...

@app.route('/delete_database', methods=['POST'])
def delete_database():
    try:
        os.remove('sk_voting.db')
        return 'Database deleted successfully!'
    except Exception as e:
        return f'Error deleting database: {str(e)}'

@app.route('/user_delete_database', methods=['GET'])
def user_delete_database():
    return render_template('delete_database.html')

if __name__ == '__main__':
    app.run(debug=True)
