from flask import Flask, render_template, request, jsonify, session, redirect
import sqlite3

app = Flask(__name__)
app.secret_key = "supersecretkey"

# -----------------------------
# DATABASE
# -----------------------------
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            skill TEXT
        )
    ''')

    conn.commit()
    conn.close()


init_db()

# -----------------------------
# ROUTES (PAGES)
# -----------------------------

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/login-page')
def login_page():
    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login-page')
    return render_template('dashboard.html')


@app.route('/profiles')
def profiles():
    return render_template('profiles.html')


@app.route('/profile')
def profile():
    return render_template('profile.html')


# -----------------------------
# AUTH
# -----------------------------

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (email, password) VALUES (?, ?)",
            (data['email'], data['password'])
        )
        conn.commit()
    except:
        return jsonify({"status": "user exists"})

    conn.close()
    return jsonify({"status": "success"})


@app.route('/login-api', methods=['POST'])
def login():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
        (data['email'], data['password'])
    )

    user = cursor.fetchone()
    conn.close()

    if user:
        session['user'] = user['email']
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "fail"})


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login-page')


@app.route('/current-user')
def current_user():
    return jsonify({"user": session.get('user')})


# -----------------------------
# SKILLS
# -----------------------------

@app.route('/add-skill', methods=['POST'])
def add_skill():
    if 'user' not in session:
        return jsonify({"status": "login required"})

    skill = request.json.get('skill', '').strip()
    user = session['user']

    if not skill:
        return jsonify({"status": "empty"})

    conn = get_db()
    cursor = conn.cursor()

    # prevent duplicate
    cursor.execute(
        "SELECT * FROM skills WHERE user_email=? AND skill=?",
        (user, skill)
    )

    if cursor.fetchone():
        conn.close()
        return jsonify({"status": "duplicate"})

    cursor.execute(
        "INSERT INTO skills (user_email, skill) VALUES (?, ?)",
        (user, skill)
    )

    conn.commit()
    conn.close()

    return jsonify({"status": "success"})


@app.route('/delete-skill', methods=['POST'])
def delete_skill():
    if 'user' not in session:
        return jsonify({"status": "login required"})

    skill = request.json.get('skill')
    user = session['user']

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM skills WHERE user_email=? AND skill=?",
        (user, skill)
    )

    conn.commit()
    conn.close()

    return jsonify({"status": "deleted"})


@app.route('/users')
def get_users():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT email FROM users")
    users = cursor.fetchall()

    result = []

    for u in users:
        email = u['email']

        cursor.execute(
            "SELECT skill FROM skills WHERE user_email=?",
            (email,)
        )

        skills = [s['skill'] for s in cursor.fetchall()]

        result.append({
            "email": email,
            "skills": skills
        })

    conn.close()
    return jsonify(result)


# -----------------------------
# RUN (IMPORTANT FOR DEPLOYMENT)
# -----------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)