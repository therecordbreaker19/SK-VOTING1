from flask import Flask
import sqlite3

app = Flask(__name__)

# Function to initialize the database


def init_database():
    conn = sqlite3.connect('sk_voting.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NULL,
            password TEXT NULL,
            skchairman TEXT NULL,
            skkagawad1 TEXT NULL,
            skkagawad2 TEXT NULL,
            skkagawad3 TEXT NULL,
            skkagawad4 TEXT NULL,
            skkagawad5 TEXT NULL,
            skkagawad6 TEXT NULL,
            skkagawad7 TEXT NULL,
            has_voted INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            publish_date TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS skchairman (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skchairman TEXT NOT NULL,
            votes INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS skkagawad (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skkagawad TEXT NOT NULL,
            votes INTEGER DEFAULT 0
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pending_registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            last_name TEXT,
            gender TEXT,
            age INTEGER,
            cell_number TEXT,
            email TEXT,
            address TEXT,
            registered TEXT
        )
    ''')

    conn.commit()
    conn.close()


if __name__ == '__main__':
    init_database()
    print("Database initialized successfully!")



