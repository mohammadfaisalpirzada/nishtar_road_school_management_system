#!/usr/bin/env python3
"""
Google Credentials Helper
Utility to load Google Sheets credentials from environment variables
"""

import os
import json
from google.oauth2.service_account import Credentials

def load_google_credentials():
    """
    Load Google Sheets credentials from environment variable or file
    Returns: Google service account credentials object
    """
    
    # Try to load from environment variable first (for Railway deployment)
    GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if GOOGLE_CREDENTIALS_JSON:
        try:
            creds_info = json.loads(GOOGLE_CREDENTIALS_JSON)
            credentials = Credentials.from_service_account_info(
                creds_info,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            print("✅ Google credentials loaded from environment variable")
            return credentials
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing GOOGLE_CREDENTIALS_JSON: {e}")
            return None
        except Exception as e:
            print(f"❌ Error loading credentials from environment: {e}")
            return None
    
    # Fallback to credentials file (for local development)
    credentials_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
    if os.path.exists(credentials_file):
        try:
            credentials = Credentials.from_service_account_file(
                credentials_file,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            print(f"✅ Google credentials loaded from file: {credentials_file}")
            return credentials
        except Exception as e:
            print(f"❌ Error loading credentials from file: {e}")
            return None
    
    print("❌ No Google credentials found. Set GOOGLE_CREDENTIALS_JSON environment variable or place credentials.json file.")
    return None

def get_spreadsheet_id():
    """
    Get Google Sheets spreadsheet ID from environment variable
    Returns: Spreadsheet ID string
    """
    spreadsheet_id = os.getenv("GOOGLE_SHEETS_ID")
    if not spreadsheet_id:
        print("❌ GOOGLE_SHEETS_ID environment variable not set")
        return None
    
    print(f"✅ Using Google Sheets ID: {spreadsheet_id}")
    return spreadsheet_id

if __name__ == "__main__":
    # Test the credentials loading
    print("Testing Google Credentials Helper...")
    
    credentials = load_google_credentials()
    if credentials:
        print("✅ Credentials loaded successfully")
    else:
        print("❌ Failed to load credentials")
    
    spreadsheet_id = get_spreadsheet_id()
    if spreadsheet_id:
        print("✅ Spreadsheet ID found")
    else:
        print("❌ Spreadsheet ID not found")