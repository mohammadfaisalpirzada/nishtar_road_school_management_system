#!/usr/bin/env python3
"""
Student Data Entry Web Application
Now using Google Sheets for cloud storage
"""

import os
import time
import random
import threading
from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, send_file
from google_sheets_data_entry import GoogleSheetsDataEntry

# Load environment variables first
load_dotenv()

# Try to import local config.py; if missing, fall back to environment variables
try:
    from config import (
        USERS, SECRET_KEY, APP_CONFIG, authenticate_user, 
        GOOGLE_SHEETS_CONFIG
    )
    CONFIG_SOURCE = 'config.py'
except Exception as e:
    print(f"Warning: failed to import config.py: {e}. Falling back to environment-based config.")
    
    # Build minimal USERS dictionary with admin and class teachers
    admin_pw = os.environ.get('ADMIN_PASSWORD') or os.environ.get('ADMIN_PW')
    if not admin_pw:
        print("❌ CRITICAL: ADMIN_PASSWORD environment variable is required!")
        print("Please set ADMIN_PASSWORD in your .env file with a strong password.")
        exit(1)
    
    USERS = {
        'admin': {
            'password': admin_pw,
            'role': 'admin',
            'access': 'all'
        }
    }
    
    # Add class teachers - all passwords must be set in environment
    classes = ['ECE', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']
    missing_teacher_passwords = []
    
    for cls in classes:
        env_key = f'TEACHER_{cls}_PASSWORD'
        password = os.environ.get(env_key)
        if password:
            username = f'class{cls}' if cls != 'ECE' else 'ece'
            USERS[username] = {
                'password': password,
                'role': 'teacher',
                'access': cls
            }
        else:
            missing_teacher_passwords.append(cls)
    
    if missing_teacher_passwords:
        print(f"⚠️ WARNING: Missing teacher passwords for classes: {', '.join(missing_teacher_passwords)}")
        print("These teachers will not be able to log in. Set their passwords in .env file.")

    # Secret key from env (required for security)
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        print("❌ CRITICAL: SECRET_KEY environment variable is required!")
        print("Please set SECRET_KEY in your .env file with a strong random key.")
        exit(1)

    # Google Sheets configuration from environment
    GOOGLE_SHEETS_CONFIG = {
        'spreadsheet_id': os.environ.get('GOOGLE_SHEETS_ID'),
        'credentials_file': os.environ.get('GOOGLE_CREDENTIALS_FILE', 'credentials.json'),
        'credentials_json': os.environ.get('GOOGLE_CREDENTIALS_JSON')
    }

    # App configuration with defaults
    APP_CONFIG = {
        'debug': os.environ.get('FLASK_DEBUG', 'False').lower() == 'true',
        'host': os.environ.get('FLASK_HOST', '0.0.0.0'),
        'port': int(os.environ.get('PORT', os.environ.get('FLASK_PORT', 5000))),
        'cache_duration': int(os.environ.get('CACHE_DURATION', 300)),
        'session_timeout': int(os.environ.get('SESSION_TIMEOUT', 3600))
    }

    def authenticate_user(username, password):
        """Fallback authenticator using environment-based credentials."""
        user = USERS.get(username)
        if not user:
            return None
        if user.get('password') == password:
            return user.copy()
        return None

# Startup summary helper
def _mask(val):
    if not val:
        return '<empty>'
    s = str(val)
    if len(s) <= 6:
        return '******'
    return s[:3] + '...' + s[-3:]

def check_required_env():
    """Check for required environment variables and print warnings"""
    required_vars = {
        'SECRET_KEY': os.environ.get('SECRET_KEY'),
        'GOOGLE_SHEETS_ID': os.environ.get('GOOGLE_SHEETS_ID'),
        'ADMIN_PASSWORD': os.environ.get('ADMIN_PASSWORD')
    }
    
    missing = [k for k, v in required_vars.items() if not v]
    if missing:
        print("⚠️ Missing required environment variables:")
        for var in missing:
            print(f"  - {var}")
        print("Please set these variables in .env or in your deployment environment.")
    
    # Check for weak SECRET_KEY values
    weak_keys = ['change-me-in-production', 'your-secret-key-change-this-in-production', 'default-dev-key-change-in-production']
    if required_vars['SECRET_KEY'] in weak_keys:
        print("❌ CRITICAL: Using weak/default SECRET_KEY - this is a security risk!")
        print("Please set a strong, random SECRET_KEY in your .env file.")
        exit(1)

def print_startup_summary():
    """Print a summary of the app's configuration"""
    source = globals().get('CONFIG_SOURCE', 'env')
    enabled = os.environ.get('ENABLE_BACKGROUND_SYNC', 'False').lower() in ('1', 'true', 'yes')
    use_sheets = os.environ.get('USE_GOOGLE_SHEETS', 'False').lower() in ('1', 'true', 'yes')
    
    print('\n----- Startup Summary -----')
    print(f'CONFIG_SOURCE: {source}')
    print(f'DEBUG: {APP_CONFIG.get("debug", False)}')
    print(f'ENABLE_BACKGROUND_SYNC: {enabled}')
    print(f'USE_GOOGLE_SHEETS: {use_sheets}')
    print(f'SECRET_KEY: {_mask(SECRET_KEY)}')
    print(f'GOOGLE_SHEETS_ID: {_mask(os.environ.get("GOOGLE_SHEETS_ID", ""))}')
    print(f'ADMIN_PASSWORD set: {bool(os.environ.get("ADMIN_PASSWORD"))}')
    print('Session Security:')
    print(f'  COOKIE_SECURE: {app.config.get("SESSION_COOKIE_SECURE", False)}')
    print(f'  COOKIE_HTTPONLY: {app.config.get("SESSION_COOKIE_HTTPONLY", True)}')
    print('---------------------------\n')
    
    # Check required environment variables
    check_required_env()

from functools import wraps
from dotenv import load_dotenv
import importlib
import consolidate_data

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() in ('1', 'true', 'yes')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session or session.get('role') != 'admin':
            flash('Admin access required', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Initialize Google Sheets data entry with proper configuration and retry logic
data_entry = None
sheets_config = GOOGLE_SHEETS_CONFIG if 'GOOGLE_SHEETS_CONFIG' in globals() else {
    'spreadsheet_id': os.environ.get('GOOGLE_SHEETS_ID'),
    'credentials_file': os.environ.get('GOOGLE_CREDENTIALS_FILE', 'credentials.json'),
    'credentials_json': os.environ.get('GOOGLE_CREDENTIALS_JSON')
}

def init_google_sheets(max_retries=3):
    """Initialize Google Sheets connection with retries"""
    global data_entry
    
    if not sheets_config.get('spreadsheet_id'):
        print("⚠️ No GOOGLE_SHEETS_ID found in environment or config")
        return False
        
    print(f"Initializing Google Sheets connection to spreadsheet: {sheets_config['spreadsheet_id']}")
    
    for attempt in range(max_retries):
        try:
            data_entry = GoogleSheetsDataEntry(
                spreadsheet_id=sheets_config['spreadsheet_id'],
                credentials_file=sheets_config.get('credentials_file')
            )
            print("✅ Google Sheets connection initialized successfully")
            return True
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Connection attempt {attempt + 1}/{max_retries} failed:")
            print(f"   Error: {error_msg}")
            
            # Don't retry on SSL errors - they tend to persist
            if 'SSL' in error_msg or 'ssl' in error_msg.lower():
                print("   SSL error detected - skipping retries")
                break
                
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + random.random()
                print(f"   Retrying in {wait_time:.1f} seconds...")
                time.sleep(wait_time)
                continue
                
    print("❌ Failed to initialize Google Sheets after all retries")
    data_entry = None
    return False

# Try to initialize Google Sheets (non-blocking)
try:
    init_google_sheets()
except Exception as e:
    print(f"⚠️ Google Sheets initialization failed: {e}")
    print("📱 Server will start without Google Sheets connection")
    data_entry = None

# Cache system for better performance
class DataCache:
    def __init__(self):
        self.cache = {}
        self.cache_timestamps = {}
        self.cache_duration = 300  # 5 minutes cache
        self.lock = threading.Lock()
    
    def get(self, key):
        with self.lock:
            if key in self.cache:
                timestamp = self.cache_timestamps.get(key, 0)
                if time.time() - timestamp < self.cache_duration:
                    return self.cache[key]
                else:
                    # Cache expired, remove it
                    del self.cache[key]
                    if key in self.cache_timestamps:
                        del self.cache_timestamps[key]
            return None
    
    def set(self, key, value):
        with self.lock:
            self.cache[key] = value
            self.cache_timestamps[key] = time.time()
    
    def clear(self):
        with self.lock:
            self.cache.clear()
            self.cache_timestamps.clear()
    
    def get_all_data(self):
        return self.get('all_students')
    
    def set_all_data(self, data):
        self.set('all_students', data)
    
    def get_class_data(self, class_name):
        return self.get(f'class_{class_name}')
    
    def set_class_data(self, class_name, data):
        self.set(f'class_{class_name}', data)
    
    def get_class_wise_data(self):
        return self.get('class_wise_data')
    
    def set_class_wise_data(self, data):
        self.set('class_wise_data', data)

# Initialize cache
data_cache = DataCache()

# Background sync thread
def background_sync():
    """Background thread to sync data periodically"""
    while True:
        try:
            print("🔄 Background sync started...")
            # Sync all data
            all_students = data_entry.get_all_students()
            data_cache.set_all_data(all_students)
            
            # Sync class-wise data (use method if present, otherwise compute)
            try:
                if hasattr(data_entry, 'get_class_wise_data') and callable(getattr(data_entry, 'get_class_wise_data')):
                    class_wise_data = data_entry.get_class_wise_data()
                else:
                    # Compute class-wise data using available methods
                    classes = ['ECE', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']
                    class_wise_data = []
                    for cls in classes:
                        try:
                            student_count = data_entry.get_class_student_count(cls)
                            male_count = data_entry.get_class_gender_count(cls, 'Male')
                            female_count = data_entry.get_class_gender_count(cls, 'Female')
                        except Exception as inner_e:
                            print(f"Warning: error getting stats for {cls}: {inner_e}")
                            student_count = male_count = female_count = 0
                        class_wise_data.append({
                            'name': cls,
                            'total_students': student_count,
                            'male_students': male_count,
                            'female_students': female_count
                        })
                data_cache.set_class_wise_data(class_wise_data)
            except Exception as e:
                # Log and continue; don't let missing helper break the entire sync
                print(f"❌ Background sync error (class-wise): {e}")
            
            # Sync individual class data
            classes = ['ECE', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']
            for class_name in classes:
                class_data = data_entry.get_class_students(class_name)
                data_cache.set_class_data(class_name, class_data)
            
            print("✅ Background sync completed")
            time.sleep(300)  # Sync every 5 minutes
        except Exception as e:
            # Common network/SSL/HTTP errors can cause transient failures. Log full detail and back off.
            print(f"❌ Background sync error: {e}")
            time.sleep(60)  # Wait 1 minute on error

def start_background_sync_if_needed():
        """Start the background sync thread only when appropriate.

        - If running as the main module (development), start it.
        - If the environment variable ENABLE_BACKGROUND_SYNC is set to true, start it
            (useful if you intentionally want the sync running under your process manager).
        This avoids spinning up background threads in every Gunicorn worker by default.
        """
        enabled = os.environ.get('ENABLE_BACKGROUND_SYNC', 'False').lower() in ('1', 'true', 'yes')
        # Temporarily disable background sync to prevent SSL crashes
        print(f"Background sync disabled to prevent SSL connection issues (enabled={enabled}, __name__={__name__})")
        return
        
        if __name__ == '__main__' or enabled:
                print(f"Starting background sync (enabled={enabled}, __name__={__name__})")
                sync_thread = threading.Thread(target=background_sync, daemon=True)
                sync_thread.start()
        else:
                print("Background sync not started (set ENABLE_BACKGROUND_SYNC=true to enable under WSGI).")

# Attempt to start background sync only when appropriate
start_background_sync_if_needed()

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Support both form-encoded POST (regular submit) and JSON POST (AJAX)
        is_json = request.is_json
        if is_json:
            payload = request.get_json(silent=True) or {}
            username = payload.get('username', '')
            password = payload.get('password', '')
        else:
            username = request.form.get('username', '')
            password = request.form.get('password', '')

        print(f"Login attempt - Username: {username}")  # Debug log

        # Use secure authentication
        user = authenticate_user(username, password)

        if user:
            print(f"Login successful - User: {username}, Role: {user['role']}")  # Debug log
            session['username'] = username
            session['role'] = user['role']
            session['access'] = user['access']

            # Return JSON for AJAX requests, otherwise redirect as before
            if is_json:
                return jsonify({'success': True, 'redirect': url_for('dashboard')})
            else:
                flash(f'Welcome, {username}!', 'success')
                return redirect(url_for('dashboard'))
        else:
            print(f"Login failed - Invalid credentials for user: {username}")  # Debug log
            if is_json:
                return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
            else:
                flash('Invalid credentials. Please check your username and password.', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_role = session.get('role')
    user_access = session.get('access')
    
    # Check Google Sheets connection
    if not data_entry:
        flash("⚠️ Google Sheets connection is not available. Some features may be limited.", "warning")
        if user_role == 'admin':
            # Only admin can retry connection
            return redirect(url_for('admin_dashboard', retry_sheets='1'))
    
    if user_role == 'admin':
        return redirect(url_for('admin_dashboard'))
    else:
        # Teachers can only access their assigned class
        if not user_access or user_access == 'all':
            flash("Access level not properly configured", "error")
            return redirect(url_for('logout'))
        return redirect(url_for('class_dashboard', class_name=user_access))

@app.route('/form')
@app.route('/form/<class_name>')
@login_required
def form(class_name=None):
    user_access = session.get('access')
    user_role = session.get('role')
    
    # If class_name is provided, validate access
    if class_name and user_access != 'all' and user_access != class_name:
        flash('Access denied to this class', 'error')
        return redirect(url_for('dashboard'))
    
    # If teacher is accessing without class_name, redirect to their class
    if not class_name and user_role == 'teacher' and user_access != 'all':
        return redirect(url_for('form', class_name=user_access))
    
    return render_template('form.html', user_access=user_access, selected_class=class_name, user_role=user_role)

@app.route('/submit', methods=['POST'])
@login_required
def submit_data():
    try:
        # Get form data
        student_data = {
            'Class_S.No': request.form.get('class_sno'),
            'GR#': request.form.get('gr_number'),
            'Student Name': request.form.get('student_name'),
            "Father's Name": request.form.get('father_name'),
            'Gender': request.form.get('gender'),
            'Religion': request.form.get('religion'),
            'Contact Number': request.form.get('contact_number'),
            'CNIC / B-Form': request.form.get('cnic_bform'),
            'Date of Birth': request.form.get('date_of_birth'),
            "Father/Mother's CNIC": request.form.get('parent_cnic'),
            'Guardian Name': request.form.get('guardian_name'),
            'Guardian CNIC': request.form.get('guardian_cnic'),
            'Guardian Relation': request.form.get('guardian_relation'),
            'Student Class': request.form.get('student_class'),
            'Class Section': request.form.get('class_section'),
            'SEMIS Code': request.form.get('semis_code'),
            'Date of Admission': request.form.get('date_of_admission'),
            'Remarks': request.form.get('remarks')
        }
        
        # Check for duplicate GR number
        if data_entry.check_duplicate_gr(student_data['GR#']):
            return jsonify({
                'success': False,
                'message': f'GR Number {student_data["GR#"]} already exists!'
            })
        
        # Add student record
        success = data_entry.add_student_record(student_data)
        
        if success:
            # Clear and refresh caches so admin dashboard shows updated totals immediately
            try:
                data_cache.clear()

                # Try to repopulate the all-students cache (if available)
                try:
                    if hasattr(data_entry, 'get_all_students'):
                        all_students = data_entry.get_all_students()
                        data_cache.set_all_data(all_students)
                except Exception as _:
                    # Non-fatal: if repopulate fails, cache was cleared and will be rebuilt later
                    pass

                # Refresh the class-specific cache for the class we just added
                try:
                    cls = student_data.get('Student Class')
                    if cls:
                        if hasattr(data_entry, 'get_class_students'):
                            class_students = data_entry.get_class_students(cls)
                            data_cache.set_class_data(cls, class_students)
                except Exception:
                    pass

                # Refresh overall class-wise summary if helper exists, otherwise compute quickly
                try:
                    if hasattr(data_entry, 'get_class_wise_data'):
                        data_cache.set_class_wise_data(data_entry.get_class_wise_data())
                    else:
                        # Quick computation fallback
                        all_classes = ['ECE', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']
                        classes_data = []
                        total_students = total_male = total_female = 0
                        for class_name in all_classes:
                            try:
                                c_total = data_entry.get_class_student_count(class_name)
                                c_male = data_entry.get_class_gender_count(class_name, 'Male')
                                c_female = data_entry.get_class_gender_count(class_name, 'Female')
                                next_sno = data_entry.get_next_class_serial_number(class_name)
                                total_students += c_total
                                total_male += c_male
                                total_female += c_female
                                classes_data.append({
                                    'name': class_name,
                                    'total_students': c_total,
                                    'male_students': c_male,
                                    'female_students': c_female,
                                    'next_sno': next_sno
                                })
                            except Exception:
                                classes_data.append({
                                    'name': class_name,
                                    'total_students': 0,
                                    'male_students': 0,
                                    'female_students': 0,
                                    'next_sno': 1
                                })
                        data_cache.set_class_wise_data({'success': True, 'classes': classes_data, 'summary': {
                            'total_students': total_students,
                            'total_male': total_male,
                            'total_female': total_female
                        }})
                except Exception:
                    pass

            except Exception:
                # Non-fatal: ensure outer try has an except so syntax is valid
                pass

            return jsonify({
                'success': True,
                'message': 'Student data saved successfully!'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to save student data'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        })

@app.route('/check_gr/<gr_number>')
@login_required
def check_gr(gr_number):
    """Check if GR number already exists"""
    exists = data_entry.check_duplicate_gr(gr_number)
    return jsonify({'exists': exists})

@app.route('/get_next_class_sno/<student_class>')
@login_required
def get_next_class_sno(student_class):
    """Get the next serial number for a class"""
    try:
        next_sno = data_entry.get_next_class_serial_number(student_class)
        return jsonify({
            'success': True,
            'next_sno': next_sno
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

@app.route('/admin_dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard with full access"""
    try:
        # Prefer cached class-wise data to avoid inconsistent counts and quota spikes
        total_classes = 11  # ECE + I-X
        class_stats = {}
        total_students = 0
        sheets_connection_error = False

        # Prefer cached full student list (single stable source) to compute total
        all_students_cached = data_cache.get_all_data()
        cached = None
        
        if all_students_cached is not None:
            try:
                total_students = len(all_students_cached)
            except Exception:
                total_students = 0
        else:
            cached = data_cache.get_class_wise_data()
        
        if cached:
            # cached may be either the computed list or the API result structure
            if isinstance(cached, dict) and cached.get('classes'):
                classes_list = cached['classes']
                total_students = cached.get('summary', {}).get('total_students', sum(c.get('total_students', 0) for c in classes_list))
                for c in classes_list:
                    name = c.get('name')
                    class_stats[name] = c.get('total_students', 0)
            elif isinstance(cached, list):
                total_students = sum(c.get('total_students', 0) for c in cached)
                for c in cached:
                    name = c.get('name')
                    class_stats[name] = c.get('total_students', 0)
            else:
                # Unknown cache format - fall back to per-class queries
                cached = None

        if not cached:
            # Cache miss or invalid cache: query class counts (with error handling)
            total_students = 0
            all_classes = ['ECE', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']
            for class_name in all_classes:
                try:
                    if data_entry:
                        class_count = data_entry.get_class_student_count(class_name)
                        total_students += class_count
                        class_stats[class_name] = class_count
                    else:
                        class_stats[class_name] = 0
                        sheets_connection_error = True
                except Exception as e:
                    print(f"Error getting count for class {class_name}: {e}")
                    class_stats[class_name] = 0
                    sheets_connection_error = True

        # If we couldn't get any data, show a warning but don't crash
        if sheets_connection_error or (total_students == 0 and not cached):
            flash("⚠️ Google Sheets connection issues detected. Data may not be current.", "warning")

        return render_template('admin_dashboard.html', 
                             total_students=total_students,
                             total_classes=total_classes,
                             class_stats=class_stats)
    except Exception as e:
        print(f"Admin dashboard error: {e}")
        # Provide fallback data to prevent complete failure
        flash(f'⚠️ Dashboard loading issues: {str(e)}. Showing limited data.', 'warning')
        return render_template('admin_dashboard.html', 
                             total_students=0,
                             total_classes=11,
                             class_stats={})

@app.route('/class_dashboard/<class_name>')
@login_required
def class_dashboard(class_name):
    """Class-specific dashboard for teachers"""
    user_access = session.get('access')
    
    # Check if user has access to this class
    if user_access != 'all' and user_access != class_name:
        flash('Access denied to this class', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        # Get class-specific statistics
        class_students = data_entry.get_class_student_count(class_name)
        boys_students = data_entry.get_class_gender_count(class_name, 'Male')
        girls_students = data_entry.get_class_gender_count(class_name, 'Female')
        
        # Get next serial number
        next_sno = data_entry.get_next_class_serial_number(class_name)
        
        return render_template('class_dashboard.html', 
                             class_name=class_name,
                             class_students=class_students,
                             boys_students=boys_students,
                             girls_students=girls_students,
                             next_sno=next_sno,
                             user_role=session.get('role'))
    except Exception as e:
        flash(f'Error loading class dashboard: {str(e)}', 'error')
        return render_template('error.html', error=str(e))

@app.route('/data-edit')
@app.route('/data_edit')
@admin_required
def data_edit():
    """Data editing page for admin"""
    return render_template('data_edit.html')

@app.route('/admin_student_edit')
@login_required
def admin_student_edit():
    """Admin student edit page"""
    sheet_name = request.args.get('sheet')
    row_number = request.args.get('row')
    
    if not sheet_name or not row_number:
        flash('Invalid student reference', 'error')
        return redirect(url_for('admin_dashboard'))
    
    try:
        row_number = int(row_number)
        sheet_data = data_entry.get_sheet_data(sheet_name)
        
        if not sheet_data or len(sheet_data) < row_number:
            flash('Student not found', 'error')
            return redirect(url_for('admin_dashboard'))
        
        # Get headers and student data
        headers = sheet_data[0]
        student_row = sheet_data[row_number - 1]  # Convert to 0-indexed
        
        # Pad student row if needed
        while len(student_row) < len(headers):
            student_row.append('')
        
        # Create student dictionary
        student = {}
        for i, header in enumerate(headers):
            student[header] = student_row[i] if i < len(student_row) else ''
        
        return render_template('admin_student_edit.html', 
                             student=student, 
                             sheet_name=sheet_name, 
                             row_number=row_number,
                             headers=headers)
    except Exception as e:
        flash(f'Error loading student: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/teacher_student_edit')
@login_required
def teacher_student_edit():
    """Teacher student edit page"""
    sheet_name = request.args.get('sheet')
    row_number = request.args.get('row')
    
    if not sheet_name or not row_number:
        flash('Invalid student reference', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        row_number = int(row_number)
        sheet_data = data_entry.get_sheet_data(sheet_name)
        
        if not sheet_data or len(sheet_data) < row_number:
            flash('Student not found', 'error')
            return redirect(url_for('dashboard'))
        
        # Get headers and student data
        headers = sheet_data[0]
        student_row = sheet_data[row_number - 1]  # Convert to 0-indexed
        
        # Pad student row if needed
        while len(student_row) < len(headers):
            student_row.append('')
        
        # Create student dictionary
        student = {}
        for i, header in enumerate(headers):
            student[header] = student_row[i] if i < len(student_row) else ''
        
        return render_template('teacher_student_edit.html', 
                             student=student, 
                             sheet_name=sheet_name, 
                             row_number=row_number,
                             headers=headers)
    except Exception as e:
        flash(f'Error loading student: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/reports')
@login_required
def reports():
    """Reports page"""
    return render_template('reports.html')

@app.route('/class_report/<class_name>')
@login_required
def class_report(class_name):
    """Class report page"""
    return render_template('class_report.html', class_name=class_name)

@app.route('/settings')
@login_required
def settings():
    """Settings page (placeholder)"""
    return "<h1>Settings</h1><p>This feature will be implemented soon.</p><a href='/dashboard'>← Back to Dashboard</a>"

@app.route('/api/class_wise_data')
@login_required
def api_class_wise_data():
    """API endpoint to get class-wise data overview"""
    if data_entry is None:
        return jsonify({'success': False, 'message': 'Google Sheets not configured. Set USE_GOOGLE_SHEETS=true and provide credentials.'}), 503
    try:
        # Try to get from cache first
        cached_data = data_cache.get_class_wise_data()
        if cached_data is not None:
            return jsonify(cached_data)
        
        # Cache miss, fetch from Google Sheets
        all_classes = ['ECE', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']
        classes_data = []
        
        # Summary statistics
        total_students = 0
        total_male = 0
        total_female = 0
        
        for class_name in all_classes:
            try:
                # Get class statistics
                class_students = data_entry.get_class_student_count(class_name)
                male_students = data_entry.get_class_gender_count(class_name, 'Male')
                female_students = data_entry.get_class_gender_count(class_name, 'Female')
                next_sno = data_entry.get_next_class_serial_number(class_name)
                
                # Add to totals
                total_students += class_students
                total_male += male_students
                total_female += female_students
                
                classes_data.append({
                    'name': class_name,
                    'total_students': class_students,
                    'male_students': male_students,
                    'female_students': female_students,
                    'next_sno': next_sno
                })
            except Exception as e:
                # If there's an error with a specific class, continue with others
                classes_data.append({
                    'name': class_name,
                    'total_students': 0,
                    'male_students': 0,
                    'female_students': 0,
                    'next_sno': 1
                })
        
        result = {
            'success': True,
            'classes': classes_data,
            'summary': {
                'total_students': total_students,
                'total_male': total_male,
                'total_female': total_female
            }
        }
        
        # Cache the result
        data_cache.set_class_wise_data(result)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })


@app.route('/api/next_class_snos')
@login_required
def api_next_class_snos():
    """Return next serial number for each class in one request to reduce client fetches"""
    try:
        if data_entry is None:
            return jsonify({'success': False, 'message': 'Google Sheets not configured.'}), 503
        classes = ['ECE', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']
        result = {}
        for cls in classes:
            try:
                # try cache first
                cached = data_cache.get_class_data(cls)
                # We don't store next_sno in cache; compute via method
                next_sno = data_entry.get_next_class_serial_number(cls)
            except Exception as e:
                print(f"Error computing next SNo for {cls}: {e}")
                next_sno = 1
            result[cls] = next_sno
        return jsonify({'success': True, 'next_snos': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/consolidate_data', methods=['POST'])
@admin_required
def api_consolidate_data():
    """Trigger consolidation in background to avoid blocking the request"""
    try:
        def run_consolidation():
            try:
                print("🔁 Starting background consolidation...")
                # Re-import to pick up local changes if any
                importlib.reload(consolidate_data)
                consolidate_data.consolidate_student_data()
                print("✅ Background consolidation finished")
                # Clear cache after consolidation
                data_cache.clear()
            except Exception as e:
                print(f"❌ Consolidation failed in background: {e}")

        t = threading.Thread(target=run_consolidation, daemon=True)
        t.start()
        return jsonify({'success': True, 'message': 'Consolidation started in background'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/class_data/<class_name>')
@login_required
def api_class_data(class_name):
    """API endpoint to get class student data"""
    user_access = session.get('access')
    
    # Check if user has access to this class
    if user_access != 'all' and user_access != class_name:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    try:
        if data_entry is None:
            return jsonify({'success': False, 'message': 'Google Sheets not configured.'}), 503
        # Try to get from cache first
        cached_data = data_cache.get_class_data(class_name)
        if cached_data is not None:
            return jsonify({
                'success': True,
                'students': cached_data,
                'cached': True
            })
        
        # Cache miss, fetch from Google Sheets
        sheet_name = f"Class_{class_name}"
        
        if not data_entry.sheet_exists(sheet_name):
            return jsonify({'success': True, 'students': []})
        
        sheet_data = data_entry.get_sheet_data(sheet_name)
        students = []
        
        if not sheet_data or len(sheet_data) <= 1:  # Only headers or empty
            return jsonify({'success': True, 'students': []})
        
        # Get headers from first row
        headers = sheet_data[0] if sheet_data else []
        header_indices = {header: idx for idx, header in enumerate(headers)}
        
        # Extract student data
        for row_idx, row_data in enumerate(sheet_data[1:], start=2):
            if row_data and len(row_data) > 0 and row_data[0]:  # Check if S.No exists
                # Pad row_data with empty strings if needed
                while len(row_data) < len(headers):
                    row_data.append('')
                
                student = {
                    'sno': row_data[header_indices.get('S.No', 0)] if 'S.No' in header_indices else '',
                    'row_number': row_idx,
                    'class_sno': row_data[header_indices.get('Class_S.No', 0)] if 'Class_S.No' in header_indices else '',
                    'student_name': row_data[header_indices.get('Student Name', 2)] if 'Student Name' in header_indices else '',
                    'father_name': row_data[header_indices.get("Father's Name", 3)] if "Father's Name" in header_indices else '',
                    'class_section': row_data[header_indices.get('Class Section', 14)] if 'Class Section' in header_indices else '',
                    'gr_number': row_data[header_indices.get('GR#', 1)] if 'GR#' in header_indices else '',
                    'gender': row_data[header_indices.get('Gender', 4)] if 'Gender' in header_indices else '',
                    'religion': row_data[header_indices.get('Religion', 5)] if 'Religion' in header_indices else '',
                    'contact_number': row_data[header_indices.get('Contact Number', 6)] if 'Contact Number' in header_indices else '',
                    'cnic_bform': row_data[header_indices.get('CNIC / B-Form', 7)] if 'CNIC / B-Form' in header_indices else '',
                    'date_of_birth': row_data[header_indices.get('Date of Birth', 8)] if 'Date of Birth' in header_indices else '',
                    'guardian_name': row_data[header_indices.get('Guardian Name', 10)] if 'Guardian Name' in header_indices else '',
                    'guardian_relation': row_data[header_indices.get('Guardian Relation', 12)] if 'Guardian Relation' in header_indices else '',
                    'remarks': row_data[header_indices.get('Remarks', 17)] if 'Remarks' in header_indices else ''
                }
                students.append(student)
        
        return jsonify({'success': True, 'students': students})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/gender_data/<class_name>/<gender>')
@login_required
def api_gender_data(class_name, gender):
    """API endpoint to get gender-specific data for a class"""
    user_access = session.get('access')
    
    # Check if user has access to this class
    if user_access != 'all' and user_access != class_name:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    try:
        # Get all class data first
        sheet_name = f"Class_{class_name}"
        
        if not data_entry.sheet_exists(sheet_name):
            return jsonify({'success': True, 'students': []})
        
        sheet_data = data_entry.get_sheet_data(sheet_name)
        students = []
        
        if not sheet_data or len(sheet_data) <= 1:
            return jsonify({'success': True, 'students': []})
        
        # Get headers from first row
        headers = sheet_data[0] if sheet_data else []
        header_indices = {header: idx for idx, header in enumerate(headers)}
        
        # Extract student data filtered by gender
        for row_idx, row_data in enumerate(sheet_data[1:], start=2):
            if row_data and len(row_data) > 0 and row_data[0]:  # Check if S.No exists
                # Pad row_data with empty strings if needed
                while len(row_data) < len(headers):
                    row_data.append('')
                
                student_gender = row_data[header_indices.get('Gender', 4)] if 'Gender' in header_indices else ''
                
                # Filter by gender
                if student_gender.strip().lower() == gender.lower():
                    student = {
                        'sno': row_data[header_indices.get('S.No', 0)] if 'S.No' in header_indices else '',
                        'row_number': row_idx,
                        'class_sno': row_data[header_indices.get('Class_S.No', 0)] if 'Class_S.No' in header_indices else '',
                        'student_name': row_data[header_indices.get('Student Name', 2)] if 'Student Name' in header_indices else '',
                        'father_name': row_data[header_indices.get("Father's Name", 3)] if "Father's Name" in header_indices else '',
                        'class_section': row_data[header_indices.get('Class Section', 14)] if 'Class Section' in header_indices else '',
                        'gr_number': row_data[header_indices.get('GR#', 1)] if 'GR#' in header_indices else '',
                        'gender': student_gender,
                        'remarks': row_data[header_indices.get('Remarks', 17)] if 'Remarks' in header_indices else ''
                    }
                    students.append(student)
        
        return jsonify({'success': True, 'students': students})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    
    # Check if user has access to this class
    if user_access != 'all' and user_access != class_name:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    try:
        # Get all class data first
        sheet_name = f"Class_{class_name}"
        
        if not data_entry.sheet_exists(sheet_name):
            return jsonify({'success': True, 'students': []})
        
        sheet_data = data_entry.get_sheet_data(sheet_name)
        students = []
        
        if not sheet_data or len(sheet_data) <= 1:
            return jsonify({'success': True, 'students': []})
        
        # Get headers from first row
        headers = sheet_data[0] if sheet_data else []
        header_indices = {header: idx for idx, header in enumerate(headers)}
        
        # Extract student data filtered by gender
        for row_idx, row_data in enumerate(sheet_data[1:], start=2):
            if row_data and len(row_data) > 0 and row_data[0]:  # Check if S.No exists
                # Pad row_data with empty strings if needed
                while len(row_data) < len(headers):
                    row_data.append('')
                
                student_gender = row_data[header_indices.get('Gender', 4)] if 'Gender' in header_indices else ''
                
                # Filter by gender
                if student_gender.strip().lower() == gender.lower():
                    student = {
                        'sno': row_data[header_indices.get('S.No', 0)] if 'S.No' in header_indices else '',
                        'row_number': row_idx,
                        'class_sno': row_data[header_indices.get('Class_S.No', 0)] if 'Class_S.No' in header_indices else '',
                        'student_name': row_data[header_indices.get('Student Name', 2)] if 'Student Name' in header_indices else '',
                        'father_name': row_data[header_indices.get("Father's Name", 3)] if "Father's Name" in header_indices else '',
                        'class_section': row_data[header_indices.get('Class Section', 14)] if 'Class Section' in header_indices else '',
                        'gr_number': row_data[header_indices.get('GR#', 1)] if 'GR#' in header_indices else '',
                        'gender': student_gender,
                        'remarks': row_data[header_indices.get('Remarks', 17)] if 'Remarks' in header_indices else ''
                    }
                    students.append(student)
        
        return jsonify({'success': True, 'students': students})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/all_students')
@admin_required
def api_all_students():
    """API endpoint to get all students data for admin"""
    try:
        # Try to get from cache first
        cached_data = data_cache.get_all_data()
        if cached_data is not None:
            return jsonify({
                'success': True,
                'students': cached_data,
                'total_count': len(cached_data),
                'cached': True
            })
        
        # Cache miss, fetch from Google Sheets
        all_students = []
        sno_counter = 1
        
        # Define all class sheets
        class_sheets = ['Class_ECE', 'Class_I', 'Class_II', 'Class_III', 'Class_IV', 
                       'Class_V', 'Class_VI', 'Class_VII', 'Class_VIII', 'Class_IX', 'Class_X']
        
        for sheet_name in class_sheets:
            if data_entry.sheet_exists(sheet_name):
                sheet_data = data_entry.get_sheet_data(sheet_name)
                if not sheet_data or len(sheet_data) <= 1:
                    continue
                    
                headers = sheet_data[0] if sheet_data else []
                header_indices = {header: idx for idx, header in enumerate(headers)}
                
                # Extract student data
                for row_idx, row_data in enumerate(sheet_data[1:], start=2):
                    if row_data and len(row_data) > 0 and row_data[0]:  # Check if S.No exists
                        # Pad row_data with empty strings if needed
                        while len(row_data) < len(headers):
                            row_data.append('')
                        
                        student = {
                            'sno': sno_counter,
                            'sheet_name': sheet_name,
                            'row_number': row_idx,
                            'class_sno': row_data[header_indices.get('Class_S.No', 0)] if len(row_data) > header_indices.get('Class_S.No', 0) else '',
                            'student_name': row_data[header_indices.get('Student Name', 2)] if len(row_data) > header_indices.get('Student Name', 2) else '',
                            'father_name': row_data[header_indices.get("Father's Name", 3)] if len(row_data) > header_indices.get("Father's Name", 3) else '',
                            'gr_number': row_data[header_indices.get('GR#', 1)] if len(row_data) > header_indices.get('GR#', 1) else '',
                            'student_class': sheet_name.replace('Class_', ''),
                            'class_section': row_data[header_indices.get('Class Section', 14)] if len(row_data) > header_indices.get('Class Section', 14) else '',
                            'contact_number': row_data[header_indices.get('Contact Number', 6)] if len(row_data) > header_indices.get('Contact Number', 6) else '',
                            'gender': row_data[header_indices.get('Gender', 4)] if len(row_data) > header_indices.get('Gender', 4) else '',
                            'religion': row_data[header_indices.get('Religion', 5)] if len(row_data) > header_indices.get('Religion', 5) else '',
                            'cnic_bform': row_data[header_indices.get('CNIC / B-Form', 7)] if len(row_data) > header_indices.get('CNIC / B-Form', 7) else '',
                            'date_of_birth': row_data[header_indices.get('Date of Birth', 8)] if len(row_data) > header_indices.get('Date of Birth', 8) else '',
                            'guardian_name': row_data[header_indices.get('Guardian Name', 10)] if len(row_data) > header_indices.get('Guardian Name', 10) else '',
                            'guardian_relation': row_data[header_indices.get('Guardian Relation', 12)] if len(row_data) > header_indices.get('Guardian Relation', 12) else '',
                            'remarks': row_data[header_indices.get('Remarks', 17)] if len(row_data) > header_indices.get('Remarks', 17) else ''
                        }
                        all_students.append(student)
                        sno_counter += 1
        
        # Cache the result
        data_cache.set_all_data(all_students)
        
        return jsonify({
            'success': True,
            'students': all_students,
            'total_count': len(all_students),
            'cached': False
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error loading students: {str(e)}'
        })

@app.route('/api/student_details/<sheet_name>/<int:row_number>')
@login_required
def api_student_details(sheet_name, row_number):
    """API endpoint to get student details"""
    try:
        # Validate access
        user_access = session.get('access')
        if user_access != 'all' and user_access != sheet_name.replace('Class_', ''):
            return jsonify({'success': False, 'message': 'Access denied'})
        
        if data_entry is None:
            return jsonify({'success': False, 'message': 'Google Sheets not configured.'}), 503
            
        sheet_data = data_entry.get_sheet_data(sheet_name)
        if not sheet_data or len(sheet_data) < row_number:
            return jsonify({'success': False, 'message': 'Student not found'})
        
        # Get headers and student data
        headers = sheet_data[0]
        student_row = sheet_data[row_number - 1]  # Convert to 0-indexed
        
        # Pad student row if needed
        while len(student_row) < len(headers):
            student_row.append('')
        
        # Create student dictionary
        student = {}
        for i, header in enumerate(headers):
            student[header] = student_row[i] if i < len(student_row) else ''
        
        return jsonify({'success': True, 'student': student})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/teacher_student_details/<sheet_name>/<int:row_number>')
@login_required
def api_teacher_student_details(sheet_name, row_number):
    """API endpoint to get student details for teachers"""
    try:
        # Validate access
        user_access = session.get('access')
        if user_access != 'all' and user_access != sheet_name.replace('Class_', ''):
            return jsonify({'success': False, 'message': 'Access denied'})
        
        if data_entry is None:
            return jsonify({'success': False, 'message': 'Google Sheets not configured.'}), 503
            
        sheet_data = data_entry.get_sheet_data(sheet_name)
        if not sheet_data or len(sheet_data) < row_number:
            return jsonify({'success': False, 'message': 'Student not found'})
        
        # Get headers and student data
        headers = sheet_data[0]
        student_row = sheet_data[row_number - 1]  # Convert to 0-indexed
        
        # Pad student row if needed
        while len(student_row) < len(headers):
            student_row.append('')
        
        # Create student dictionary
        student = {}
        for i, header in enumerate(headers):
            student[header] = student_row[i] if i < len(student_row) else ''
        
        return jsonify({'success': True, 'student': student})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/edit_student/<sheet_name>/<int:row_number>', methods=['POST'])
@login_required
def api_edit_student(sheet_name, row_number):
    """API endpoint to edit a student"""
    try:
        # Get form data
        student_data = request.get_json()
        
        # Validate access
        user_access = session.get('access')
        if user_access != 'all' and user_access != sheet_name.replace('Class_', ''):
            return jsonify({'success': False, 'message': 'Access denied'})
        
        # Update student record
        result = data_entry.update_student_record(sheet_name, row_number, student_data)
        
        if result:
            # Clear cache after update
            data_cache.clear()
            return jsonify({
                'success': True,
                'message': 'Student updated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to update student'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error updating student: {str(e)}'
        })

@app.route('/api/delete_student/<sheet_name>/<int:row_number>', methods=['DELETE'])
@admin_required
def api_delete_student(sheet_name, row_number):
    """API endpoint to delete a student"""
    try:
        result = data_entry.delete_student_record(sheet_name, row_number)
        if result:
            # Clear cache after successful deletion
            data_cache.clear()
            return jsonify({
                'success': True,
                'message': 'Student deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to delete student'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error deleting student: {str(e)}'
        })

@app.route('/api/refresh_cache', methods=['POST'])
@admin_required
def api_refresh_cache():
    """API endpoint to manually refresh cache"""
    try:
        data_cache.clear()
        return jsonify({
            'success': True,
            'message': 'Cache refreshed successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error refreshing cache: {str(e)}'
        })

@app.route('/student_details')
@login_required
def student_details():
    """Student details page"""
    sheet_name = request.args.get('sheet')
    row_number = request.args.get('row')
    
    if not sheet_name or not row_number:
        flash('Invalid student reference', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        row_number = int(row_number)
        sheet_data = data_entry.get_sheet_data(sheet_name)
        
        if not sheet_data or len(sheet_data) < row_number:
            flash('Student not found', 'error')
            return redirect(url_for('dashboard'))
        
        # Get headers and student data
        headers = sheet_data[0]
        student_row = sheet_data[row_number - 1]  # Convert to 0-indexed
        
        # Pad student row if needed
        while len(student_row) < len(headers):
            student_row.append('')
        
        # Create student dictionary
        student_data = dict(zip(headers, student_row))
        
        return render_template('student_details.html', 
                             student=student_data, 
                             sheet_name=sheet_name, 
                             row_number=row_number)
    except Exception as e:
        flash(f'Error loading student details: {str(e)}', 'error')
        return redirect(url_for('dashboard'))


@app.route('/health')
def health():
    """Lightweight healthcheck endpoint for load balancers and platform healthchecks.

    This endpoint deliberately avoids any Google Sheets calls so it responds quickly
    during deployments and prevents healthcheck-related quota usage.
    """
    return jsonify({'success': True, 'status': 'ok'}), 200

@app.route('/print_student/<sheet_name>/<int:row_number>')
@login_required
def print_student(sheet_name, row_number):
    """Print student details in A4 format"""
    try:
        sheet_data = data_entry.get_sheet_data(sheet_name)
        
        if not sheet_data or len(sheet_data) < row_number:
            return jsonify({'success': False, 'message': 'Student not found'})
        
        # Get headers and student data
        headers = sheet_data[0]
        student_row = sheet_data[row_number - 1]  # Convert to 0-indexed
        
        # Pad student row if needed
        while len(student_row) < len(headers):
            student_row.append('')
        
        # Create student dictionary
        student_data = dict(zip(headers, student_row))
        
        return render_template('print_student.html', 
                             student=student_data, 
                             sheet_name=sheet_name, 
                             row_number=row_number)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/teacher_student_details')
@login_required
def teacher_student_details():
    """Teacher student details page"""
    sheet_name = request.args.get('sheet')
    row_number = request.args.get('row')
    
    if not sheet_name or not row_number:
        flash('Invalid student reference', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        row_number = int(row_number)
        sheet_data = data_entry.get_sheet_data(sheet_name)
        
        if not sheet_data or len(sheet_data) < row_number:
            flash('Student not found', 'error')
            return redirect(url_for('dashboard'))
        
        # Get headers and student data
        headers = sheet_data[0]
        student_row = sheet_data[row_number - 1]  # Convert to 0-indexed
        
        # Pad student row if needed
        while len(student_row) < len(headers):
            student_row.append('')
        
        # Create student dictionary
        student_data = dict(zip(headers, student_row))
        
        return render_template('teacher_student_details.html', 
                             student=student_data, 
                             sheet_name=sheet_name, 
                             row_number=row_number)
    except Exception as e:
        flash(f'Error loading student details: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print("Starting Student Data Entry Web Server...")
    print(f"Access from mobile: http://YOUR_PC_IP:{port}")
    print(f"Access locally: http://localhost:{port}")
    print("Login credentials are loaded from .env file:")
    print(f"Admin: admin/{admin_pw if admin_pw else 'NOT_SET'}")
    print("Class teachers: Use usernames like 'classI', 'classII', etc. with passwords from .env")
    print("ECE teacher: ece/[password from .env]")
    app.run(host='0.0.0.0', port=port, debug=debug)