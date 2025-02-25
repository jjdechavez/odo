import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, UTC
import jwt
import os

class Database:
    def __init__(self):
        self.db_path = 'odo.db'
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('admin', 'user')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    token TEXT UNIQUE NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            conn.commit()

            # Check if admin user exists
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM users WHERE role = ?', ('admin',))
            admin_count = cursor.fetchone()[0]

            # Create admin user if none exists and environment variables are set
            if admin_count == 0:
                admin_email = os.getenv('ADMIN_EMAIL')
                admin_password = os.getenv('ADMIN_PASSWORD')
                
                if admin_email and admin_password:
                    self.create_user(admin_email, admin_password, role='admin')

    def create_user(self, username, password, role='user'):
        try:
            with sqlite3.connect(self.db_path) as conn:
                password_hash = generate_password_hash(password)
                conn.execute(
                    'INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)',
                    (username, password_hash, role)
                )
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False

    def verify_user(self, username, password):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT id, password_hash, role FROM users WHERE username = ?',
                (username,)
            )
            user = cursor.fetchone()
            
            if user and check_password_hash(user[1], password):
                return {'id': user[0], 'role': user[2]}
        return None

    def create_session(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            expires_at = datetime.now(UTC) + timedelta(days=1)
            token = jwt.encode(
                {
                    'user_id': user_id,
                    'exp': expires_at
                },
                os.getenv('JWT_SECRET', 'your-secret-key'),
                algorithm='HS256'
            )
            
            conn.execute(
                'INSERT INTO sessions (user_id, token, expires_at) VALUES (?, ?, ?)',
                (user_id, token, expires_at)
            )
            conn.commit()
            return token

    def verify_session(self, token):
        try:
            payload = jwt.decode(
                token,
                os.getenv('JWT_SECRET', 'your-secret-key'),
                algorithms=['HS256']
            )
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''
                    SELECT u.id, u.role FROM users u
                    JOIN sessions s ON u.id = s.user_id
                    WHERE s.token = ? AND s.expires_at > ?
                    ''',
                    (token, datetime.now(UTC))
                )
                result = cursor.fetchone()
                if result:
                    return {'user_id': result[0], 'role': result[1]}
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        return None