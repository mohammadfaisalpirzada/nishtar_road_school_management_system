#!/usr/bin/env python3
"""
Sample Configuration File
Copy this file to config.py and modify with your actual credentials
"""

import os
import hashlib
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Security configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')

# User credentials with hashed passwords
# In production, use proper password hashing (bcrypt, argon2, etc.)
USERS = {
    'admin': {
        'password': 'admin',  # In production, use hashed passwords
        'role': 'admin',
        'access': 'all'
    },
    'ece': {
        'password': 'ece',
        'role': 'teacher',
        'access': 'ECE'
    },
    'class1': {
        'password': 'class1',
        'role': 'teacher',
        'access': 'I'
    },
    'class2': {
        'password': 'class2',
        'role': 'teacher',
        'access': 'II'
    },
    'class3': {
        'password': 'class3',
        'role': 'teacher',
        'access': 'III'
    },
    'class4': {
        'password': 'class4',
        'role': 'teacher',
        'access': 'IV'
    },
    'class5': {
        'password': 'class5',
        'role': 'teacher',
        'access': 'V'
    },
    'class6': {
        'password': 'class6',
        'role': 'teacher',
        'access': 'VI'
    },
    'class7': {
        'password': 'class7',
        'role': 'teacher',
        'access': 'VII'
    },
    'class8': {
        'password': 'class8',
        'role': 'teacher',
        'access': 'VIII'
    },
    'class9': {
        'password': 'class9',
        'role': 'teacher',
        'access': 'IX'
    },
    'class10': {
        'password': 'class10',
        'role': 'teacher',
        'access': 'X'
    }
}

# Google Sheets configuration
GOOGLE_SHEETS_CONFIG = {
    'spreadsheet_id': os.environ.get('GOOGLE_SHEETS_ID'),
    'credentials_file': os.environ.get('GOOGLE_CREDENTIALS_FILE', 'credentials.json'),
    'credentials_json': os.environ.get('GOOGLE_CREDENTIALS_JSON')
}

# Application configuration
APP_CONFIG = {
    'debug': os.environ.get('FLASK_DEBUG', 'False').lower() == 'true',
    'host': os.environ.get('FLASK_HOST', '0.0.0.0'),
    'port': int(os.environ.get('FLASK_PORT', 5000)),
    'cache_duration': int(os.environ.get('CACHE_DURATION', 300)),  # 5 minutes
    'session_timeout': int(os.environ.get('SESSION_TIMEOUT', 3600))  # 1 hour
}

# Security functions
def hash_password(password):
    """Hash a password using SHA-256 (for demonstration - use bcrypt in production)"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    """Verify a password against its hash"""
    return hash_password(password) == hashed

def get_user(username):
    """Get user information securely"""
    if username in USERS:
        return USERS[username].copy()  # Return a copy to prevent modification
    return None

def authenticate_user(username, password):
    """Authenticate user credentials"""
    user = get_user(username)
    if user and user['password'] == password:  # In production, use verify_password()
        return user
    return None
