from flask import Flask, render_template, request, session, redirect, url_for, flash
import sqlite3
import hashlib
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired
from flask_socketio import SocketIO, emit
from flask import after_this_request
import functools

import os 

app = Flask(__name__)
socketio = SocketIO(app)  

app.secret_key = 'voting558231'

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

@app.route('/')
def home():
    return render_template('home.html', link_status=link_status)
    

@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = hash_password(password)
        conn = sqlite3.connect('sk_voting.db')
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO admins (username, password) VALUES (?, ?)', (username, hashed_password))
        conn.commit()
        conn.close()
        return "Admin Registration successful! Thank you."
    return render_template('admin_register.html')
#####################################################################################################
@app.route('/user/register', methods=['GET', 'POST'])
def user_register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = hash_password(password)
        conn = sqlite3.connect('sk_voting.db')
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
        conn.commit()
        conn.close()
        alert_message = "You have successfully registered."
        return render_template('admin_success.html', alert_message=alert_message)
    return render_template('user_register.html')

####################################################################################################
def get_admin_password(username):
    conn = sqlite3.connect('sk_voting.db')
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM admins WHERE username=?", (username,))
    password = cursor.fetchone()
    conn.close()
    if password:
        return password[0]
    return None

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = hash_password(password)
        stored_password = get_admin_password(username)
        if stored_password and stored_password == hashed_password:
            # Successful login
            session['admin_logged_in'] = True
            # Store the username in the session
            session['admin_username'] = username
            return redirect(url_for('admin_dashboard'))
        else:
            return "Invalid username or password. Please try again."
    return render_template('admin_login.html')
link_status = True

@app.route('/admin/logout')
def admin_logout():
    # Clear all user-related session data
    session.clear()

    # Redirect to the login page (assuming the route is named 'login')
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_logged_in' in session and session['admin_logged_in']:
        username = session['admin_username']
        return render_template('admin_dashboard.html', username=username, link_status=link_status)
    else:
        return redirect(url_for('admin_login'))

# Add a decorator to prevent caching for the /admin/dashboard route
@app.after_request
def add_no_cache(response):
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

#################################################################################################
def get_user_password(username):
    conn = sqlite3.connect('sk_voting.db')
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username=?", (username,))
    password = cursor.fetchone()
    conn.close()
    if password:
        return password[0]
    return None

@app.route('/user/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = hash_password(password)
        stored_password = get_user_password(username)
        if stored_password and stored_password == hashed_password:
            session['logged_in'] = True
            session['username'] = username  # Store the username in the session
            return redirect(url_for('user_dashboard'))
        else:
            # Invalid credentials
            return render_template('user_login.html')
    return render_template('user_login.html')

@app.route('/user/logout')
def user_logout():
    # Clear all user-related session data
    session.clear()
    return redirect(url_for('home'))

@app.route('/user/dashboard')
def user_dashboard():
    if 'logged_in' in session and session['logged_in']:
        # Retrieve the username from the session
        username = session['username']
        return render_template('user_dashboard.html', username=username)
    else:
        return redirect(url_for('user_login'))

# Add a decorator to prevent caching for the /user/dashboard route
@app.after_request
def add_no_cache(response):
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response
########################################################################################################
DB_FILE = "sk_voting.db"
def check_admin():
    if 'admin_logged_in' in session and session['admin_logged_in']:
        return True
    return False

# Decorator to check if an admin is logged in
def admin_required(func):
    @functools.wraps(func)
    def decorated_function(*args, **kwargs):
        if not check_admin():
            return redirect(url_for('admin_login'))
        return func(*args, **kwargs)
    return decorated_function

# Apply the decorator to admin-only routes
@app.route('/admin_create_announcement')
@admin_required
def admin_create_announcement():
    return render_template('admin_create_announcement.html')

@app.route('/admin_view_announcements')
@admin_required
def admin_view_announcements():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Announcements")
    Announcements = cursor.fetchall()
    conn.close()
    return render_template('admin_view_announcements.html', notices=Announcements)

# Add cache control for admin routes
@app.after_request
def add_no_cache(response):
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response




@app.route('/admin_submit_announcement', methods=['GET', 'POST'])
def submit_announcement():
    if not check_admin():
        return redirect(url_for('admin_login'))
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        # Extract data from the form submission
        title = request.form.get('title')
        content = request.form.get('content')
        publish_date = request.form.get('publish_date')
        cursor.execute("INSERT INTO Announcements (title, content, publish_date) VALUES (?, ?, ?)",
                       (title, content, publish_date))
        conn.commit()
        conn.close()
        # Pass refresh=True to trigger a refresh
        return render_template('admin_dashboard.html', refresh=True)
    except Exception as e:
        return f'Error: {str(e)}'

@app.route('/admin_delete_announcement', methods=['GET', 'POST'])
def delete_announcement():
    if not check_admin():
        return redirect(url_for('admin_login'))
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        # Extract the announcement ID from the request
        delete_id = request.form.get('delete_id')
        # Delete the announcement from the database
        cursor.execute("DELETE FROM Announcements WHERE id = ?", (delete_id,))
        # Commit the changes and close the connection
        conn.commit()
        conn.close()
        return 'Announcement deleted successfully!'
    except Exception as e:
        return f'Error: {str(e)}'

@app.route('/admin_edit_announcement', methods=['POST'])
def edit_announcement():
    if not check_admin():
        return redirect(url_for('admin_login'))
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        # Extract data from the request
        edit_id = request.form.get('edit_id')
        edited_title = request.form.get('title')
        edited_content = request.form.get('content')
        edited_publish_date = request.form.get('publish_date')
        # Update the announcement in the database
        cursor.execute("UPDATE Announcements SET title = ?, content = ?, publish_date = ? WHERE id = ?",
                       (edited_title, edited_content, edited_publish_date, edit_id))
        # Commit the changes and close the connection
        conn.commit()
        conn.close()
        return 'Announcement updated successfully!'
    except Exception as e:
        return f'Error: {str(e)}'

@app.route('/view_announcements', methods=['GET', 'POST'])
def view_announcements():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Fetch data from the database
    cursor.execute(
        "SELECT id, title, content, publish_date FROM Announcements")
    announcements = cursor.fetchall()
    conn.close()
    return render_template('view_announcements.html', announcements=announcements)
###################################################################################################

# Initialize SQLite database
def create_table():
    conn = sqlite3.connect('sk_voting.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sk_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            position TEXT,
            partylist TEXT,
            firstname TEXT,
            middlename TEXT,
            lastname TEXT
        )
    ''')
    conn.commit()
    conn.close()

create_table()

class SKForm(FlaskForm):
    position = SelectField('Position', choices=[('SK Chairman', 'SK Chairman'), ('SK Kagawad', 'SK Kagawad')])
    partylist = SelectField('Partylist', choices=[])
    firstname = StringField('First Name')
    middlename = StringField('Middle Name')
    lastname = StringField('Last Name')
    submit = SubmitField('Submit')
    
# Helper function to interact with the database and insert data
def insert_into_db(position, partylist, firstname, middlename, lastname):
    conn = sqlite3.connect('sk_voting.db')
    cursor = conn.cursor()

    if position == 'SK Chairman':
        cursor.execute('''
            INSERT INTO sskchairman (position, partylist, firstname, middlename, lastname)
            VALUES (?, ?, ?, ?, ?)
        ''', (position, partylist, firstname, middlename, lastname))
        
        cursor.execute('''
            INSERT INTO skchairman (partylist, firstname, middlename, lastname)
            VALUES (?, ?, ?, ?)
        ''', (partylist, firstname, middlename, lastname,))
    elif position == 'SK Kagawad':
        cursor.execute('''
            INSERT INTO sskkagawad (position, partylist, firstname, middlename, lastname)
            VALUES (?, ?, ?, ?, ?)
        ''', (position, partylist, firstname, middlename, lastname))

        cursor.execute('''
            INSERT INTO skkagawad (partylist, firstname, middlename, lastname)
            VALUES (?, ?, ?, ?)
        ''', (partylist, firstname, middlename, lastname,))

    conn.commit()
    conn.close()

# Route for handling the form
@app.route('/add_sk_member', methods=['GET', 'POST'])
def add_sk_member():
    form = SKForm()

    # Fetch party list choices from the database
    conn = sqlite3.connect('sk_voting.db')
    cursor = conn.cursor()
    cursor.execute("SELECT partylist_name FROM partylist")
    party_list = cursor.fetchall()
    conn.close()

    # Assign party list choices to the form
    party_list_with_labels = [(party[0], party[0]) for party in party_list]
    form.partylist.choices = party_list_with_labels

    # Handle form submission
    if request.method == 'POST' and form.validate_on_submit():
        position = request.form['position']
        partylist = request.form['partylist']
        firstname = request.form['firstname']
        middlename = request.form['middlename']
        lastname = request.form['lastname']

        # Insert data into the database based on the selected position
        insert_into_db(position, partylist, firstname, middlename, lastname)

        if position == "SK Chairman":
            return redirect(url_for('admin_dashboard'))
        elif position == "SK Kagawad":
            return redirect(url_for('admin_dashboard'))

    return render_template('admin_add_candidate.html', form=form)



#################################################################################################
class SKCouncilForm(FlaskForm):
    skchairman = SelectField('SK Chairman', coerce=int,
                             validators=[DataRequired()])
    skkagawad1 = SelectField('SK Kagawad 1', coerce=int,
                             validators=[DataRequired()])
    skkagawad2 = SelectField('SK Kagawad 2', coerce=int,
                             validators=[DataRequired()])
    skkagawad3 = SelectField('SK Kagawad 3', coerce=int,
                             validators=[DataRequired()])
    skkagawad4 = SelectField('SK Kagawad 4', coerce=int,
                             validators=[DataRequired()])
    skkagawad5 = SelectField('SK Kagawad 5', coerce=int,
                             validators=[DataRequired()])
    skkagawad6 = SelectField('SK Kagawad 6', coerce=int,
                             validators=[DataRequired()])
    skkagawad7 = SelectField('SK Kagawad 7', coerce=int,
                             validators=[DataRequired()])
    submit = SubmitField('Add SK Council')

def any_duplicate(iterable):
    # Check if there are any duplicates in the iterable
    return len(set(iterable)) != len(iterable)

@app.route('/add_sk_council', methods=['GET', 'POST'])
def add_sk_council():
    form = SKCouncilForm()

    conn = sqlite3.connect('sk_voting.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, partylist || ' ' || firstname || ' ' || middlename || ' ' || lastname AS full_name
        FROM skchairman
    ''')
    form.skchairman.choices = cursor.fetchall()

    cursor.execute('''
        SELECT id, partylist || ' ' || firstname || ' ' || middlename || ' ' || lastname AS full_name
        FROM skkagawad
    ''')
    sk_kagawad_options = cursor.fetchall()
    conn.close()

    form.skkagawad1.choices = sk_kagawad_options
    form.skkagawad2.choices = sk_kagawad_options
    form.skkagawad3.choices = sk_kagawad_options
    form.skkagawad4.choices = sk_kagawad_options
    form.skkagawad5.choices = sk_kagawad_options
    form.skkagawad6.choices = sk_kagawad_options
    form.skkagawad7.choices = sk_kagawad_options


    if request.method == 'POST' and form.validate_on_submit():
        skchairman = form.skchairman.data
        skkagawads = [
            form.skkagawad1.data, form.skkagawad2.data, form.skkagawad3.data,
            form.skkagawad4.data, form.skkagawad5.data, form.skkagawad6.data,
            form.skkagawad7.data
        ]
        username = session.get('username')
        
        if not username:
            return redirect(url_for('home'))

        conn = sqlite3.connect('sk_voting.db')
        cursor = conn.cursor()
        cursor.execute("SELECT has_voted FROM users WHERE username = ?", (username,))
        has_voted = cursor.fetchone()

        if has_voted and has_voted[0] == 1:
            conn.close()
            return redirect(url_for('home'))

        # Check for duplicates among SK Kagawads only
        if any_duplicate(skkagawads):
            # Display alert instead of flash message
            return '''
            <script>
                alert('You cannot vote for the same candidate multiple times or select duplicates.');
                window.location.href = '/add_sk_council';
            </script>
            '''

        # Update votes for SK Chairman
        cursor.execute('''
            UPDATE skchairman
            SET votes = votes + 1
            WHERE id = ?
        ''', (skchairman,))

        # Update votes for SK Kagawads
        for skkagawad in skkagawads:
            cursor.execute('''
                UPDATE skkagawad
                SET votes = votes + 1
                WHERE id = ?
            ''', (skkagawad,))

        # Update the user's has_voted status
        cursor.execute('''
            UPDATE users
            SET skchairman = ?, skkagawad1 = ?, skkagawad2 = ?, 
                skkagawad3 = ?, skkagawad4 = ?, skkagawad5 = ?, 
                skkagawad6 = ?, skkagawad7 = ?, has_voted = 1
            WHERE username = ?
        ''', (skchairman, *skkagawads, username))

        conn.commit()
        conn.close()

        # Redirect or render a success page as needed
        return redirect(url_for('vote_success'))

    return render_template('user_add_sk_council.html', form=form)

@app.route('/vote_success')
def vote_success():
    # Check if the user voted successfully
    if session.get('voted_successfully'):
        # Clear the session variable
        session.pop('voted_successfully', None)
        return '''
        <script>
            alert('You have voted successfully. Logout now.');
            window.location.href = '/logout';
        </script>
        '''
    else:
        return redirect(url_for('home'))
#########################################################################################################
@app.route('/view_users', methods=['GET'])
@admin_required  # Apply admin authentication to the route
def view_users():
    conn = sqlite3.connect('sk_voting.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users")
    users_data = cursor.fetchall()
    conn.close()
    return render_template('view_users.html', users=users_data)

# Add cache control for this route
@app.after_request
def add_no_cache(response):
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response


################################################################################################
@app.route('/display_winners_alternative')
@admin_required  # Apply admin authentication to the route
def display_winners_alternative():
    conn = sqlite3.connect('sk_voting.db')
    cursor = conn.cursor()

    # Fetch the SK Chairman and SK Kagawad candidates
    cursor.execute("SELECT id, partylist, firstname, middlename, lastname FROM skchairman")
    sk_chairman_candidates = cursor.fetchall()

    cursor.execute("SELECT id, partylist, firstname, middlename, lastname FROM skkagawad")
    sk_kagawad_candidates = cursor.fetchall()

    # Initialize vote counts for SK Chairman and SK Kagawad
    sk_chairman_vote_counts = {candidate[0]: 0 for candidate in sk_chairman_candidates}
    sk_kagawad_vote_counts = {candidate[0]: 0 for candidate in sk_kagawad_candidates}

    # Fetch votes for SK Chairman and SK Kagawad
    cursor.execute("SELECT skchairman, skkagawad1, skkagawad2, skkagawad3, skkagawad4, skkagawad5, skkagawad6, skkagawad7 FROM users")
    votes = cursor.fetchall()

    # Tally votes for SK Chairman and SK Kagawad
    for vote in votes:
        if vote[0] is not None:
            sk_chairman_vote_counts[int(vote[0])] += 1
        for sk_kagawad_id in vote[1:]:
            if sk_kagawad_id is not None:
                sk_kagawad_vote_counts[int(sk_kagawad_id)] += 1

    conn.close()

    # Determine SK Chairman winner
    sk_chairman_winner_id = max(sk_chairman_vote_counts, key=sk_chairman_vote_counts.get)
    sk_chairman_winner = next((candidate for candidate in sk_chairman_candidates if candidate[0] == sk_chairman_winner_id), None)

    # Determine SK Kagawad winners (Top 7)
    sk_kagawad_winner_ids = sorted(sk_kagawad_vote_counts, key=sk_kagawad_vote_counts.get, reverse=True)[:7]
    sk_kagawad_winners = [candidate for candidate in sk_kagawad_candidates if candidate[0] in sk_kagawad_winner_ids]

    return render_template('display_winners.html', sk_chairman_winner=sk_chairman_winner, sk_kagawad_winners=sk_kagawad_winners)


# Add cache control for this route
@app.after_request
def add_no_cache(response):
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response
######################################################################################################################

#####################################################################################################
@app.route('/admin_home')
@admin_required  # Apply admin authentication to the route
def admin_home():
    return render_template('admin_home.html', link_status=link_status)

# Add cache control for this route
@app.after_request
def add_no_cache(response):
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response
#######################################################################################################
def get_skkagawad_data():
    conn = sqlite3.connect('sk_voting.db')  # Replace 'your_database_name.db' with your actual database name
    cursor = conn.cursor()
    cursor.execute("SELECT id, partylist, firstname, middlename, lastname, votes FROM skkagawad")  # Adjust the query to match your table structure
    data = cursor.fetchall()
    conn.close()
    return data

@app.route('/display_skkagawad')
@admin_required  # Apply admin authentication to the route
def display_skkagawad():
    skkagawad_data = get_skkagawad_data()
    return render_template('skkagawad.html', skkagawad_data=skkagawad_data)

# Add cache control for this route
@app.after_request
def add_no_cache(response):
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

###################################################################################################
@app.route('/display_skchairman')
@admin_required  # Apply admin authentication to the route
def display_skchairman():
    conn = sqlite3.connect('sk_voting.db')  # Replace 'your_database_name.db' with your database name
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM skchairman")
    skchairman_data = cursor.fetchall()

    conn.close()

    return render_template('skchairman.html', skchairman_data=skchairman_data)

# Add cache control for this route
@app.after_request
def add_no_cache(response):
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response
######################################################################################################
@app.route('/delete_database', methods=['POST'])
@admin_required  # Apply admin authentication to the route
def delete_database():
    try:
        conn = sqlite3.connect('sk_voting.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        tables_to_exclude = ['admins', 'sqlite_sequence']  # Exclude specified tables
        for table in tables:
            if table[0] not in tables_to_exclude:
                cursor.execute(f"DROP TABLE {table[0]};")
        conn.commit()
        conn.close()
        return render_template('admin_dashboard.html')
    except Exception as e:
        return f'Error deleting database: {str(e)}'

# Add cache control for this route
@app.after_request
def add_no_cache(response):
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

@app.route('/delete_databases')
def delete_databases():
    return render_template('delete_database.html')
######################################################################################################
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
        CREATE TABLE IF NOT EXISTS sskchairman (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            position TEXT NOT NULL,
            partylist TEXT NOT NULL,
            firstname TEXT NOT NULL,
            middlename TEXT,
            lastname TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sskkagawad (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            position TEXT NOT NULL,
            partylist TEXT NOT NULL,
            firstname TEXT NOT NULL,
            middlename TEXT,
            lastname TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS partylist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            partylist_name TEXT NOT NULL
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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS skchairman (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            partylist TEXT NOT NULL,
            firstname TEXT NOT NULL,
            middlename TEXT NOT NULL,
            lastname TEXT NOT NULL,
            votes INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS skkagawad (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            partylist TEXT NOT NULL,
            firstname TEXT NOT NULL,
            middlename TEXT NOT NULL,
            lastname TEXT NOT NULL,
            votes INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/initialize_database', methods=['GET'])
def initialize_database():
    init_database()
    return redirect('/admin/dashboard')
######################################################################################################
@app.route('/admin_create_database', methods=['GET'])
@admin_required  # Apply admin authentication to the route
def admin_create_database():
    return render_template('create_database.html')

# Add cache control for this route
@app.after_request
def add_no_cache(response):
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response
########################################################################################################

@app.route('/enable_links')
@admin_required  # Apply admin authentication to the route
def enable_links():
    global link_status
    link_status = True
    socketio.emit('reload_page', namespace='/reload')
    return redirect('/admin/dashboard')

@app.route('/disable_links')
@admin_required  # Apply admin authentication to the route
def disable_links():
    global link_status
    link_status = False
    socketio.emit('reload_page', namespace='/reload')
    return redirect('/admin/dashboard')

@socketio.on('connect', namespace='/reload')
def reload_page():
    emit('reload', broadcast=True)

#####################################################################################################
@app.route('/users_list')
def users_list():
    conn = sqlite3.connect('sk_voting.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, has_voted FROM users')
    users_data = cursor.fetchall()

    # Calculate total users who have voted
    total_voted = sum(1 for row in users_data if row[2] == 1)

    # Calculate total users who haven't voted
    total_users = len(users_data)
    total_not_voted = total_users - total_voted

    conn.close()
    return render_template('users_list.html', users_data=users_data, total_voted=total_voted, total_not_voted=total_not_voted)

##########################################################################################
@app.route('/vote_settings')
def vote_settings():
    return render_template('vote_settings.html', link_status=link_status)
###################################################################################################
@app.route('/user_ressults')
def user_ressults():
    return render_template('user_ressults.html', link_status=link_status)
###################################################################################################
@app.route('/pendings/user/register', methods=['GET', 'POST'])
def pendings_user_register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        gender = request.form['gender']
        age = request.form['age']
        cell_number = request.form['cell_number']
        email = request.form['email']
        address = request.form['address']
        conn = sqlite3.connect('sk_voting.db')
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO pending_registrations (first_name, last_name, gender, age, cell_number, email, address) VALUES (?, ?, ?, ?, ?, ?, ?)', (first_name, last_name, gender, age, cell_number, email, address))
        conn.commit()
        conn.close()
        alert_message = "You have successfully registered Wait For The Username And Password To Be Sent To You, Using Your Cellphone Number Or Your Email Address."
        return render_template('success.html', alert_message=alert_message)
    return render_template('home.html')

@app.route('/pending/user/register')
def pending_user_register():
    return render_template('pending_users_register.html')

def get_db_connection():
    conn = sqlite3.connect('sk_voting.db')  # Replace 'your_database.db' with your database file
    conn.row_factory = sqlite3.Row
    return conn

# Route for rendering the HTML page
@app.route('/user_info_list')
def user_info_list():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pending_registrations")
    user_info_data = cursor.fetchall()
    total_users = len(user_info_data)
    conn.close()
    return render_template('user_info_list.html', user_info_data=user_info_data, total_users=total_users)

# Route to handle user deletion
@app.route('/delete_user', methods=['POST'])
def delete_user():
    if request.method == 'POST':
        user_id = int(request.form['user_id'])
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM pending_registrations WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        return render_template('admin_dashboard.html')  # Redirect to updated user list

####################################################################################################
@app.route('/edit_skkagawad_name', methods=['POST'])
def edit_skkagawad_name():
    sk_id = request.form.get('sk_id')
    new_name = request.form.get('new_name')

    conn = sqlite3.connect('sk_voting.db')
    cursor = conn.cursor()

    try:
        cursor.execute("UPDATE sk_kagawad SET SK_Name = ? WHERE ID = ?", (new_name, sk_id))
        conn.commit()
        conn.close()
        return 'SK Kagawad Name Updated'
    except sqlite3.Error as e:
        print("Update Error:", str(e))
        return 'Failed to update SK Kagawad Name'
###################################################################################################
@app.route('/admin_edit_kagawad', methods=['POST'])
def admin_edit_kagawad():
    # Fetch the data sent from the frontend
    sk_id = request.form.get('id')
    edited_firstname = request.form.get('firstname')
    edited_middlename = request.form.get('middlename')
    edited_lastname = request.form.get('lastname')

    # Log the received data to check if it's reaching the route
    print(f"ID: {sk_id}, Firstname: {edited_firstname}, Middlename: {edited_middlename}, Lastname: {edited_lastname}")

    # Perform the necessary update in your database here
    # For instance, if you're using SQLite, you might do something like this:
    conn = sqlite3.connect('sk_voting.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE skkagawad SET firstname=?, middlename=?, lastname=? WHERE id=?", (edited_firstname, edited_middlename, edited_lastname, sk_id))
    conn.commit()
    conn.close()

    # Return a success response
    return 'Details updated successfully'


@app.route('/admin_edit_chairman', methods=['POST'])
def admin_edit_chairman():
    # Fetch the data sent from the frontend
    sk_id = request.form.get('id')
    edited_firstname = request.form.get('firstname')
    edited_middlename = request.form.get('middlename')
    edited_lastname = request.form.get('lastname')

    # Log the received data to check if it's reaching the route
    print(f"ID: {sk_id}, Firstname: {edited_firstname}, Middlename: {edited_middlename}, Lastname: {edited_lastname}")

    # Perform the necessary update in your database here
    # For instance, if you're using SQLite, you might do something like this:
    conn = sqlite3.connect('sk_voting.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE skchairman SET firstname=?, middlename=?, lastname=? WHERE id=?", (edited_firstname, edited_middlename, edited_lastname, sk_id))
    conn.commit()
    conn.close()

    # Return a success response
    return 'Details updated successfully'


##################################################################################################
@app.route('/user_display_winners_alternative')
@admin_required  # Apply admin authentication to the route
def user_display_winners_alternative():
    conn = sqlite3.connect('sk_voting.db')
    cursor = conn.cursor()

    # Fetch the SK Chairman and SK Kagawad candidates
    cursor.execute("SELECT id, partylist, firstname, middlename, lastname FROM skchairman")
    sk_chairman_candidates = cursor.fetchall()

    cursor.execute("SELECT id, partylist, firstname, middlename, lastname FROM skkagawad")
    sk_kagawad_candidates = cursor.fetchall()

    # Initialize vote counts for SK Chairman and SK Kagawad
    sk_chairman_vote_counts = {candidate[0]: 0 for candidate in sk_chairman_candidates}
    sk_kagawad_vote_counts = {candidate[0]: 0 for candidate in sk_kagawad_candidates}

    # Fetch votes for SK Chairman and SK Kagawad
    cursor.execute("SELECT skchairman, skkagawad1, skkagawad2, skkagawad3, skkagawad4, skkagawad5, skkagawad6, skkagawad7 FROM users")
    votes = cursor.fetchall()

    # Tally votes for SK Chairman and SK Kagawad
    for vote in votes:
        if vote[0] is not None:
            sk_chairman_vote_counts[int(vote[0])] += 1
        for sk_kagawad_id in vote[1:]:
            if sk_kagawad_id is not None:
                sk_kagawad_vote_counts[int(sk_kagawad_id)] += 1

    conn.close()

    # Determine SK Chairman winner
    sk_chairman_winner_id = max(sk_chairman_vote_counts, key=sk_chairman_vote_counts.get)
    sk_chairman_winner = next((candidate for candidate in sk_chairman_candidates if candidate[0] == sk_chairman_winner_id), None)

    # Determine SK Kagawad winners (Top 7)
    sk_kagawad_winner_ids = sorted(sk_kagawad_vote_counts, key=sk_kagawad_vote_counts.get, reverse=True)[:7]
    sk_kagawad_winners = [candidate for candidate in sk_kagawad_candidates if candidate[0] in sk_kagawad_winner_ids]

    return render_template('user_display_results.html', sk_chairman_winner=sk_chairman_winner, sk_kagawad_winners=sk_kagawad_winners)


@app.route('/add_partylist', methods=['GET'])
def add_partylist():
    return render_template('admin_add_partylist.html')

@app.route('/submit_partylist', methods=['POST'])
def submit_partylist():
    if request.method == 'POST':
        partylist_name = request.form['partylist']

        # Connect to the SQLite database
        conn = sqlite3.connect('sk_voting.db')
        cursor = conn.cursor()

        # Insert the partylist into the database
        cursor.execute('INSERT INTO partylist (partylist_name) VALUES (?)', (partylist_name,))
        
        # Commit changes and close the connection
        conn.commit()
        conn.close()

        # Redirect to a success page or any other desired page
        return redirect(url_for('admin_dashboard'))

    return 'Invalid Request'



if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True,)
    


