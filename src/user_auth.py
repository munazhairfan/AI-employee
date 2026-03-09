"""
User Authentication & Credential Management
- User signup/login
- OAuth token storage (Gmail, Odoo, etc.)
- Secure encryption for credentials
"""

import sqlite3
import hashlib
import secrets
import json
from datetime import datetime
from pathlib import Path
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import os

load_dotenv()

# Database path
DB_PATH = Path('data/users.db')
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Encryption key (generate once and store in .env)
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', '')
if not ENCRYPTION_KEY:
    # Generate new key if not exists
    ENCRYPTION_KEY = Fernet.generate_key().decode()
    print(f"[WARNING] Generated new encryption key: {ENCRYPTION_KEY}")
    print(f"[WARNING] Add this to your .env file:")
    print(f"ENCRYPTION_KEY={ENCRYPTION_KEY}")
    # Save to .env for next time
    with open('.env', 'a') as f:
        f.write(f'\nENCRYPTION_KEY={ENCRYPTION_KEY}\n')

cipher = Fernet(ENCRYPTION_KEY.encode())


def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    # User credentials table (encrypted)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            platform TEXT NOT NULL,  -- 'gmail', 'odoo', 'whatsapp', etc.
            access_token TEXT,  -- Encrypted
            refresh_token TEXT,  -- Encrypted
            token_expiry TIMESTAMP,
            email_address TEXT,  -- For Gmail
            odoo_url TEXT,  -- For Odoo
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, platform)
        )
    ''')
    
    # User sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("[OK] Database initialized")


def hash_password(password):
    """Hash password with salt"""
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{pwd_hash}"


def verify_password(password, password_hash):
    """Verify password against hash"""
    try:
        salt, stored_hash = password_hash.split(':')
        new_hash = hashlib.sha256((salt + password).encode()).hexdigest()
        return new_hash == stored_hash
    except:
        return False


def encrypt_token(token):
    """Encrypt sensitive token"""
    if not token:
        return None
    return cipher.encrypt(token.encode()).decode()


def decrypt_token(encrypted_token):
    """Decrypt sensitive token"""
    if not encrypted_token:
        return None
    return cipher.decrypt(encrypted_token.encode()).decode()


# ============ User Management ============

def create_user(email, password, name=''):
    """Create new user"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        password_hash = hash_password(password)
        
        cursor.execute('''
            INSERT INTO users (email, password_hash, name)
            VALUES (?, ?, ?)
        ''', (email, password_hash, name))
        
        conn.commit()
        user_id = cursor.lastrowid
        
        return {'success': True, 'user_id': user_id, 'message': 'User created'}
    
    except sqlite3.IntegrityError:
        return {'success': False, 'error': 'Email already registered'}
    
    finally:
        conn.close()


def login_user(email, password):
    """Login user and create session"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Get user
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        
        if not user:
            return {'success': False, 'error': 'User not found'}
        
        # Verify password
        if not verify_password(password, user['password_hash']):
            return {'success': False, 'error': 'Invalid password'}
        
        # Create session
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.now().replace(hour=23, minute=59, second=59)
        
        cursor.execute('''
            INSERT INTO user_sessions (user_id, session_token, expires_at)
            VALUES (?, ?, ?)
        ''', (user['id'], session_token, expires_at))
        
        # Update last login
        cursor.execute('UPDATE users SET last_login = ? WHERE id = ?', 
                      (datetime.now(), user['id']))
        
        conn.commit()
        
        return {
            'success': True,
            'user_id': user['id'],
            'email': user['email'],
            'name': user['name'],
            'session_token': session_token
        }
    
    finally:
        conn.close()


def verify_session(session_token):
    """Verify if session is valid"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT u.*, s.expires_at 
            FROM users u
            JOIN user_sessions s ON u.id = s.user_id
            WHERE s.session_token = ? AND s.expires_at > ?
        ''', (session_token, datetime.now()))
        
        user = cursor.fetchone()
        
        if user:
            return {
                'valid': True,
                'user_id': user['id'],
                'email': user['email'],
                'name': user['name']
            }
        else:
            return {'valid': False}
    
    finally:
        conn.close()


# ============ Credential Management ============

def save_user_credentials(user_id, platform, credentials):
    """Save user credentials (encrypted)"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Encrypt sensitive data
        access_token = encrypt_token(credentials.get('access_token', ''))
        refresh_token = encrypt_token(credentials.get('refresh_token', ''))
        
        # Upsert credentials
        cursor.execute('''
            INSERT INTO user_credentials 
                (user_id, platform, access_token, refresh_token, 
                 token_expiry, email_address, odoo_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, platform) DO UPDATE SET
                access_token = excluded.access_token,
                refresh_token = excluded.refresh_token,
                token_expiry = excluded.token_expiry,
                email_address = excluded.email_address,
                odoo_url = excluded.odoo_url,
                updated_at = CURRENT_TIMESTAMP
        ''', (
            user_id,
            platform,
            access_token,
            refresh_token,
            credentials.get('token_expiry'),
            credentials.get('email_address'),
            credentials.get('odoo_url')
        ))
        
        conn.commit()
        return {'success': True, 'message': f'{platform} credentials saved'}
    
    finally:
        conn.close()


def get_user_credentials(user_id, platform):
    """Get user credentials (decrypted)"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT * FROM user_credentials 
            WHERE user_id = ? AND platform = ?
        ''', (user_id, platform))
        
        cred = cursor.fetchone()
        
        if not cred:
            return None
        
        # Decrypt tokens
        return {
            'platform': cred['platform'],
            'access_token': decrypt_token(cred['access_token']),
            'refresh_token': decrypt_token(cred['refresh_token']),
            'token_expiry': cred['token_expiry'],
            'email_address': cred['email_address'],
            'odoo_url': cred['odoo_url']
        }
    
    finally:
        conn.close()


# Initialize database on import
init_db()


# ============ Test Function ============

if __name__ == "__main__":
    print("Testing User Authentication System...")
    print("=" * 60)
    
    # Test user creation
    print("\n[TEST 1] Create user...")
    result = create_user('test@example.com', 'password123', 'Test User')
    print(f"Result: {result}")
    
    # Test login
    print("\n[TEST 2] Login user...")
    result = login_user('test@example.com', 'password123')
    print(f"Result: {result}")
    
    if result['success']:
        # Test saving credentials
        print("\n[TEST 3] Save Gmail credentials...")
        creds = {
            'access_token': 'gmail_access_token_123',
            'refresh_token': 'gmail_refresh_token_456',
            'email_address': 'test@gmail.com'
        }
        result = save_user_credentials(result['user_id'], 'gmail', creds)
        print(f"Result: {result}")
        
        # Test retrieving credentials
        print("\n[TEST 4] Retrieve Gmail credentials...")
        creds = get_user_credentials(result['user_id'], 'gmail')
        print(f"Result: {creds}")
