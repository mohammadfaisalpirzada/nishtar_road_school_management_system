import os
import json
from typing import Dict, Optional

class Config:
    """Application configuration."""
    
    # Application Security - MUST be set in environment variables
    SECRET_KEY = os.getenv('SECRET_KEY')  # Required: Set a strong secret key
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')  # Required: Set a strong admin password

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

    # Teacher Passwords - MUST be set in environment variables
    TEACHER_PASSWORDS = {
        'ECE': os.getenv('TEACHER_ECE_PASSWORD'),  # Required: Set strong password
        'I': os.getenv('TEACHER_I_PASSWORD'),     # Required: Set strong password
        'II': os.getenv('TEACHER_II_PASSWORD'),   # Required: Set strong password
        'III': os.getenv('TEACHER_III_PASSWORD'), # Required: Set strong password
        'IV': os.getenv('TEACHER_IV_PASSWORD'),   # Required: Set strong password
        'V': os.getenv('TEACHER_V_PASSWORD'),     # Required: Set strong password
        'VI': os.getenv('TEACHER_VI_PASSWORD'),   # Required: Set strong password
        'VII': os.getenv('TEACHER_VII_PASSWORD'), # Required: Set strong password
        'VIII': os.getenv('TEACHER_VIII_PASSWORD'),# Required: Set strong password
        'IX': os.getenv('TEACHER_IX_PASSWORD'),   # Required: Set strong password
        'X': os.getenv('TEACHER_X_PASSWORD'),     # Required: Set strong password
    }

    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration."""
        if not cls.SECRET_KEY:
            print("❌ SECRET_KEY environment variable is required")
            return False
            
        if not cls.ADMIN_PASSWORD:
            print("❌ ADMIN_PASSWORD environment variable is required")
            return False
            
        if not cls.SHEETS_ID:
            print("❌ GOOGLE_SHEETS_ID environment variable is required")
            return False
            
        if not cls.get_credentials():
            print("❌ Google credentials not found in environment")
            return False
            
        # Check that teacher passwords are set
        missing_passwords = [k for k, v in cls.TEACHER_PASSWORDS.items() if not v]
        if missing_passwords:
            print(f"❌ Missing teacher passwords for: {', '.join(missing_passwords)}")
            return False
            
        return True
