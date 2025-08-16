import os
import json
from typing import Dict, Optional

class Config:
    """Application configuration."""
    
    # Application Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-dev-key-change-in-production')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

    # Server Configuration
    PORT = int(os.getenv('PORT', 5000))
    DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'true').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = os.getenv('SESSION_COOKIE_HTTPONLY', 'true').lower() == 'true'

    # Google Sheets Configuration
    SHEETS_ID = os.getenv('GOOGLE_SHEETS_ID')
    
    @staticmethod
    def get_credentials() -> Optional[Dict]:
        """Get Google credentials from environment or file."""
        creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
        if creds_json:
            try:
                return json.loads(creds_json)
            except json.JSONDecodeError:
                return None
        return None

    # Cache Configuration
    CACHE_DURATION = int(os.getenv('CACHE_DURATION', 300))  # 5 minutes
    SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', 3600))  # 1 hour

    # Background Sync Configuration
    ENABLE_BACKGROUND_SYNC = os.getenv('ENABLE_BACKGROUND_SYNC', 'false').lower() == 'true'
    SYNC_INTERVAL = int(os.getenv('SYNC_INTERVAL', 300))  # 5 minutes

    # Teacher Passwords
    TEACHER_PASSWORDS = {
        'ECE': os.getenv('TEACHER_ECE_PASSWORD', 'ece123'),
        'I': os.getenv('TEACHER_I_PASSWORD', 'class1'),
        'II': os.getenv('TEACHER_II_PASSWORD', 'class2'),
        'III': os.getenv('TEACHER_III_PASSWORD', 'class3'),
        'IV': os.getenv('TEACHER_IV_PASSWORD', 'class4'),
        'V': os.getenv('TEACHER_V_PASSWORD', 'class5'),
        'VI': os.getenv('TEACHER_VI_PASSWORD', 'class6'),
        'VII': os.getenv('TEACHER_VII_PASSWORD', 'class7'),
        'VIII': os.getenv('TEACHER_VIII_PASSWORD', 'class8'),
        'IX': os.getenv('TEACHER_IX_PASSWORD', 'class9'),
        'X': os.getenv('TEACHER_X_PASSWORD', 'class10'),
    }

    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration."""
        if not cls.SECRET_KEY or cls.SECRET_KEY == 'default-dev-key-change-in-production':
            return False
            
        if not cls.SHEETS_ID:
            return False
            
        if not cls.get_credentials():
            return False
            
        return True
