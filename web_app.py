#!/usr/bin/env python3
"""
Web-based Student Data Entry System
Allows mobile data entry with PC file storage
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, send_file
from student_data_entry import StudentDataEntry
import os
import json
from datetime import datetime
from functools import wraps
from consolidate_data import consolidate_student_data
import tempfile
import shutil

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'student_data_entry_2025_admin_panel')

# User credentials and roles
USERS = {
    'admin': {'password': 'admin', 'role': 'admin', 'access': 'all'},
    'class1': {'password': 'class1', 'role': 'teacher', 'access': 'I'},
    'class2': {'password': 'class2', 'role': 'teacher', 'access': 'II'},
    'class3': {'password': 'class3', 'role': 'teacher', 'access': 'III'},
    'class4': {'password': 'class4', 'role': 'teacher', 'access': 'IV'},
    'class5': {'password': 'class5', 'role': 'teacher', 'access': 'V'},
    'class6': {'password': 'class6', 'role': 'teacher', 'access': 'VI'},
    'class7': {'password': 'class7', 'role': 'teacher', 'access': 'VII'},
    'class8': {'password': 'class8', 'role': 'teacher', 'access': 'VIII'},
    'class9': {'password': 'class9', 'role': 'teacher', 'access': 'IX'},
    'class10': {'password': 'class10', 'role': 'teacher', 'access': 'X'},
    'ece': {'password': 'ece', 'role': 'teacher', 'access': 'ECE'}
}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session or session.get('role') != 'admin':
            flash('Admin access required')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Initialize the data entry system
data_entry = StudentDataEntry()

@app.route('/')
def index():
    """Redirect to login if not authenticated, otherwise to dashboard"""
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in USERS and USERS[username]['password'] == password:
            session['user'] = username
            session['role'] = USERS[username]['role']
            session['access'] = USERS[username]['access']
            flash(f'Welcome, {username}!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    flash('You have been logged out')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard based on user role"""
    user_role = session.get('role')
    user_access = session.get('access')
    
    if user_role == 'admin':
        return redirect(url_for('admin_dashboard'))
    else:
        return redirect(url_for('class_dashboard', class_name=user_access))

@app.route('/form')
@login_required
def form():
    """Student data entry form - accessible to all authenticated users"""
    try:
        return render_template('form.html')
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/submit', methods=['POST'])
@login_required
def submit_data():
    """Handle form submission"""
    try:
        # Get form data
        form_data = request.form.to_dict()
        
        # Validate required fields
        required_fields = ['student_name', 'father_name', 'gr_number', 'student_class']
        for field in required_fields:
            if not form_data.get(field):
                return jsonify({
                    'success': False, 
                    'message': f'{field.replace("_", " ").title()} is required'
                })
        
        # Get student class for Class_S.No generation
        student_class = form_data.get('student_class', '')
        class_sno = data_entry.get_next_class_serial_number(student_class)
        
        # Generate Class_S.No with correct format
        if student_class == "ECE":
            class_s_no = f"ECE_{class_sno:02d}"
        else:
            # For numbered classes (I, II, III, etc.), use format like 101, 201, 301
            class_mapping = {
                "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5,
                "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10
            }
            if student_class in class_mapping:
                class_prefix = class_mapping[student_class]
                class_s_no = f"{class_prefix}{class_sno:02d}"
            else:
                # Fallback for any other class format
                class_s_no = f"{student_class}_{class_sno:02d}"
        
        # Prepare student data with all required fields
        student_data = {
            'Class_S.No': class_s_no,
            'GR#': form_data.get('gr_number', ''),
            'Student Name': form_data.get('student_name', ''),
            'Father\'s Name': form_data.get('father_name', ''),
            'Gender': form_data.get('gender', 'N/A'),
            'Religion': form_data.get('religion', ''),
            'Contact Number': form_data.get('contact_number', 'N/A'),
            'CNIC / B-Form': form_data.get('cnic_bform', 'N/A'),
            'Date of Birth': form_data.get('date_of_birth', 'N/A'),
            'Father/Mother\'s CNIC': form_data.get('father_cnic', 'N/A'),
            'Guardian Name': '',  # Will be set based on guardian type
            'Guardian CNIC': '',  # Will be set based on guardian type
            'Guardian Relation': '',  # Will be set based on guardian type
            'Student Class': form_data.get('student_class', ''),
            'Class Section': '',  # Will be set based on gender
            'SEMIS Code': '408070227',  # Auto-set
            'Date of Admission': form_data.get('date_of_admission', 'N/A'),
            'Remarks': 'N/A'  # Admin-only field, set after admission
        }
        
        # Handle guardian selection
        guardian_type = form_data.get('guardian_type', 'N')
        if guardian_type == 'F':  # Father
            student_data['Guardian Name'] = student_data['Father\'s Name']
            student_data['Guardian CNIC'] = student_data['Father/Mother\'s CNIC']
            student_data['Guardian Relation'] = 'Father'
        elif guardian_type == 'N':  # Nil
            student_data['Guardian Name'] = '-'
            student_data['Guardian CNIC'] = '-'
            student_data['Guardian Relation'] = '-'
        else:  # Others
            student_data['Guardian Name'] = form_data.get('guardian_name', 'N/A')
            student_data['Guardian CNIC'] = form_data.get('guardian_cnic', 'N/A')
            student_data['Guardian Relation'] = form_data.get('guardian_relation', 'N/A')
        
        # Set Class Section based on gender
        gender = student_data.get('Gender', '').lower()
        if gender in ['male', 'm']:
            student_data['Class Section'] = 'Boys'
        else:  # female or any other value defaults to Girls
            student_data['Class Section'] = 'Girls'
        
        # Class_S.No is no longer used - keeping empty for Excel structure compatibility
        
        # Validate GR# for duplicates
        if data_entry.check_duplicate_gr(student_data['GR#']):
            return jsonify({
                'success': False,
                'message': f'GR# {student_data["GR#"]} already exists. Please use a different number.'
            })
        
        # Format CNIC numbers
        cnic_fields = ['CNIC / B-Form', 'Father/Mother\'s CNIC', 'Guardian CNIC']
        for field in cnic_fields:
            if student_data.get(field) and student_data[field] != '-':
                student_data[field] = data_entry.format_cnic(student_data[field])
        
        # Save to Excel
        if data_entry.add_student_record(student_data):
            return jsonify({
                'success': True,
                'message': f'Student record saved successfully! Class S.No: {student_data["Class_S.No"]}, GR#: {student_data["GR#"]}',
                'student_data': student_data
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to save student record to Excel file. Please check file permissions and try again.'
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
    try:
        exists = data_entry.check_duplicate_gr(gr_number)
        return jsonify({'exists': exists})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/get_next_class_sno/<student_class>')
@login_required
def get_next_class_sno(student_class):
    """Get next class serial number for AJAX updates"""
    try:
        next_class_sno = data_entry.get_next_class_serial_number(student_class)
        
        # Format based on class type
        if student_class == "ECE":
            formatted_sno = f"ECE_{next_class_sno:02d}"
        else:
            # For numbered classes (I, II, III, etc.), use format like 101, 201, 301
            class_mapping = {
                "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5,
                "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10
            }
            if student_class in class_mapping:
                class_prefix = class_mapping[student_class]
                formatted_sno = f"{class_prefix}{next_class_sno:03d}"
            else:
                # Fallback for any other class format
                formatted_sno = f"{student_class}_{next_class_sno:02d}"
        
        return jsonify({'success': True, 'next_class_sno': formatted_sno})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/stats')
@login_required
def api_stats():
    """API endpoint for dashboard statistics"""
    try:
        total_students = data_entry.get_total_students()
        total_classes = 11  # ECE + I-X
        
        return jsonify({
            'success': True,
            'total_students': total_students,
            'total_classes': total_classes
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/class_wise_data')
@login_required
def api_class_wise_data():
    """API endpoint for class-wise data overview"""
    try:
        # Define all classes
        all_classes = ['ECE', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']
        classes_data = []
        
        # Summary statistics
        total_students = 0
        total_male = 0
        total_female = 0
        
        for class_name in all_classes:
            # Get class statistics
            class_students = data_entry.get_class_student_count(class_name)
            boys_section = data_entry.get_class_section_count(class_name, 'Boys')
            girls_section = data_entry.get_class_section_count(class_name, 'Girls')
            next_sno = data_entry.get_next_class_serial_number(class_name)
            
            # Get gender statistics for this class
            male_students = data_entry.get_class_gender_count(class_name, 'Male')
            female_students = data_entry.get_class_gender_count(class_name, 'Female')
            
            # Add to totals
            total_students += class_students
            total_male += male_students
            total_female += female_students
            
            classes_data.append({
                'name': class_name,
                'total_students': class_students,
                'male_students': male_students,
                'female_students': female_students,
                'boys_section': boys_section,
                'girls_section': girls_section,
                'next_sno': next_sno
            })
        
        return jsonify({
            'success': True,
            'classes': classes_data,
            'summary': {
                'total_students': total_students,
                'total_male': total_male,
                'total_female': total_female
            }
        })
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
        # Use the correct sheet naming convention
        sheet_name = f"Class_{class_name}"
        
        if sheet_name not in data_entry.workbook.sheetnames:
            return jsonify({'success': True, 'students': []})
        
        sheet = data_entry.workbook[sheet_name]
        students = []
        
        # Get header row to find column indices
        headers = {}
        for col in range(1, sheet.max_column + 1):
            header_value = sheet.cell(row=1, column=col).value
            if header_value:
                headers[header_value] = col
        
        # Extract student data
        for row in range(2, sheet.max_row + 1):
            if sheet.cell(row=row, column=1).value:  # Check if S.No exists
                student = {
                    'sno': sheet.cell(row=row, column=headers.get('S.No', 1)).value,
                    'row_number': row,
                    'class_sno': sheet.cell(row=row, column=headers.get('Class_S.No', 2)).value,
                    'student_name': sheet.cell(row=row, column=headers.get('Student Name', 3)).value,
                    'father_name': sheet.cell(row=row, column=headers.get("Father's Name", 4)).value,
                    'class_section': sheet.cell(row=row, column=headers.get('Class Section', 15)).value,
                    'gr_number': sheet.cell(row=row, column=headers.get('GR#', 16)).value,
                    'gender': sheet.cell(row=row, column=headers.get('Gender', 5)).value
                }
                students.append(student)
        
        return jsonify({'success': True, 'students': students})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/section_data/<class_name>/<section>')
@login_required
def api_section_data(class_name, section):
    """API endpoint to get section-specific student data"""
    user_access = session.get('access')
    
    # Check if user has access to this class
    if user_access != 'all' and user_access != class_name:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    try:
        # Use the correct sheet naming convention
        sheet_name = f"Class_{class_name}"
        
        if sheet_name not in data_entry.workbook.sheetnames:
            return jsonify({'success': True, 'students': []})
        
        sheet = data_entry.workbook[sheet_name]
        students = []
        
        # Get header row to find column indices
        headers = {}
        for col in range(1, sheet.max_column + 1):
            header_value = sheet.cell(row=1, column=col).value
            if header_value:
                headers[header_value] = col
        
        section_col = headers.get('Class Section', 15)
        
        # Extract student data for specific section
        for row in range(2, sheet.max_row + 1):
            if (sheet.cell(row=row, column=1).value and  # Check if S.No exists
                sheet.cell(row=row, column=section_col).value == section):
                student = {
                    'sno': sheet.cell(row=row, column=headers.get('S.No', 1)).value,
                    'class_sno': sheet.cell(row=row, column=headers.get('Class_S.No', 2)).value,
                    'student_name': sheet.cell(row=row, column=headers.get('Student Name', 3)).value,
                    'father_name': sheet.cell(row=row, column=headers.get('Father Name', 4)).value,
                    'class_section': sheet.cell(row=row, column=section_col).value,
                    'gr_number': sheet.cell(row=row, column=headers.get('GR#', 16)).value,
                    'gender': sheet.cell(row=row, column=headers.get('Gender', 5)).value
                }
                students.append(student)
        
        return jsonify({'success': True, 'students': students})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/gender_data/<class_name>/<gender>')
@login_required
def api_gender_data(class_name, gender):
    """API endpoint to get gender-specific student data"""
    user_access = session.get('access')
    
    # Check if user has access to this class
    if user_access != 'all' and user_access != class_name:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    try:
        # Use the correct sheet naming convention
        sheet_name = f"Class_{class_name}"
        
        if sheet_name not in data_entry.workbook.sheetnames:
            return jsonify({'success': True, 'students': []})
        
        sheet = data_entry.workbook[sheet_name]
        students = []
        
        # Get header row to find column indices
        headers = {}
        for col in range(1, sheet.max_column + 1):
            header_value = sheet.cell(row=1, column=col).value
            if header_value:
                headers[header_value] = col
        
        gender_col = headers.get('Gender', 5)
        
        # Extract student data for specific gender
        for row in range(2, sheet.max_row + 1):
            if sheet.cell(row=row, column=1).value:  # Check if S.No exists
                student_gender = sheet.cell(row=row, column=gender_col).value
                if student_gender and student_gender.lower() == gender.lower():
                    student = {
                        'sno': sheet.cell(row=row, column=headers.get('S.No', 1)).value,
                        'class_sno': sheet.cell(row=row, column=headers.get('Class_S.No', 2)).value,
                        'student_name': sheet.cell(row=row, column=headers.get('Student Name', 3)).value,
                        'father_name': sheet.cell(row=row, column=headers.get('Father Name', 4)).value,
                        'class_section': sheet.cell(row=row, column=headers.get('Class Section', 15)).value,
                        'gr_number': sheet.cell(row=row, column=headers.get('GR#', 16)).value,
                        'gender': student_gender
                    }
                    students.append(student)
        
        return jsonify({'success': True, 'students': students})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin_dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard with full access"""
    try:
        total_students = data_entry.get_total_students()
        total_classes = 11  # ECE + I-X
        
        return render_template('admin_dashboard.html', 
                             total_students=total_students,
                             total_classes=total_classes)
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/class_dashboard/<class_name>')
@login_required
def class_dashboard(class_name):
    """Class-specific dashboard for teachers"""
    user_access = session.get('access')
    
    # Check if user has access to this class
    if user_access != 'all' and user_access != class_name:
        flash('Access denied to this class')
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
        return render_template('error.html', error=str(e))

# Placeholder routes for dashboard buttons
@app.route('/data-view')
@login_required
def data_view():
    """Data viewing page (placeholder)"""
    return "<h1>Data View</h1><p>This feature will be implemented soon.</p><a href='/dashboard'>← Back to Dashboard</a>"

@app.route('/data-edit')
@admin_required
def data_edit():
    """Data editing page for admin"""
    return render_template('data_edit.html')

@app.route('/admin_student_edit')
@login_required
def admin_student_edit():
    """Admin student edit page"""
    if session.get('role') != 'admin':
        return redirect(url_for('dashboard'))
    return render_template('admin_student_edit.html')

@app.route('/class-wise')
@login_required
def class_wise():
    """Class-wise data page"""
    return render_template('class_wise.html')

@app.route('/reports')
@login_required
def reports():
    """Reports page with data visualization"""
    return render_template('reports.html')

@app.route('/class_report/<class_name>')
@login_required
def class_report(class_name):
    """Class-specific report page"""
    user_access = session.get('access')
    
    # Check if user has access to this class
    if user_access != 'all' and user_access != class_name:
        flash('Access denied to this class')
        return redirect(url_for('dashboard'))
    
    return render_template('class_report.html', class_name=class_name)

@app.route('/api/class_report_data/<class_name>')
@login_required
def api_class_report_data(class_name):
    """API endpoint to get class report data for charts"""
    user_access = session.get('access')
    
    # Check if user has access to this class
    if user_access != 'all' and user_access != class_name:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    try:
        from datetime import datetime
        import calendar
        
        # Use the correct sheet naming convention
        sheet_name = f"Class_{class_name}"
        
        if sheet_name not in data_entry.workbook.sheetnames:
            return jsonify({'success': True, 'gender_data': {}, 'age_data': {}, 'section_data': {}, 'total_students': 0})
        
        sheet = data_entry.workbook[sheet_name]
        
        # Get header row to find column indices
        headers = {}
        for col in range(1, sheet.max_column + 1):
            header_value = sheet.cell(row=1, column=col).value
            if header_value:
                headers[header_value] = col
        
        # Initialize counters
        gender_count = {'Male': 0, 'Female': 0}
        age_groups = {'3-5': 0, '6-8': 0, '9-11': 0, '12-14': 0, '15+': 0}
        section_count = {'Boys': 0, 'Girls': 0}
        total_students = 0
        
        # Process each student row
        for row in range(2, sheet.max_row + 1):
            if sheet.cell(row=row, column=1).value:  # Check if S.No exists
                total_students += 1
                
                # Gender data
                gender = sheet.cell(row=row, column=headers.get('Gender', 5)).value
                if gender and gender.strip():
                    gender = gender.strip().title()
                    if gender in gender_count:
                        gender_count[gender] += 1
                
                # Section data
                section = sheet.cell(row=row, column=headers.get('Class Section', 15)).value
                if section and section.strip():
                    section = section.strip().upper()
                    if section in section_count:
                        section_count[section] += 1
                
                # Age data (calculate from date of birth)
                dob_cell = sheet.cell(row=row, column=headers.get('Date of Birth', 10)).value
                if dob_cell:
                    try:
                        if isinstance(dob_cell, str):
                            # Try different date formats
                            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']:
                                try:
                                    dob = datetime.strptime(dob_cell, fmt)
                                    break
                                except ValueError:
                                    continue
                            else:
                                continue
                        else:
                            dob = dob_cell
                        
                        # Calculate age
                        today = datetime.now()
                        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                        
                        # Categorize age
                        if age <= 5:
                            age_groups['3-5'] += 1
                        elif age <= 8:
                            age_groups['6-8'] += 1
                        elif age <= 11:
                            age_groups['9-11'] += 1
                        elif age <= 14:
                            age_groups['12-14'] += 1
                        else:
                            age_groups['15+'] += 1
                    except (ValueError, TypeError):
                        continue
        
        return jsonify({
            'success': True,
            'gender_data': gender_count,
            'age_data': age_groups,
            'section_data': section_count,
            'total_students': total_students
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/all_students')
@admin_required
def api_all_students():
    """API endpoint to get all students data for admin"""
    try:
        all_students = []
        sno_counter = 1
        
        # Define all class sheets
        class_sheets = ['Class_ECE', 'Class_I', 'Class_II', 'Class_III', 'Class_IV', 
                       'Class_V', 'Class_VI', 'Class_VII', 'Class_VIII', 'Class_IX', 'Class_X']
        
        for sheet_name in class_sheets:
            if sheet_name in data_entry.workbook.sheetnames:
                sheet = data_entry.workbook[sheet_name]
                
                # Get header row to find column indices
                headers = {}
                for col in range(1, sheet.max_column + 1):
                    header_value = sheet.cell(row=1, column=col).value
                    if header_value:
                        headers[header_value] = col
                
                # Extract student data with all available fields
                for row in range(2, sheet.max_row + 1):
                    if sheet.cell(row=row, column=1).value:  # Check if S.No exists
                        student = {
                            'sno': sno_counter,
                            'sheet_name': sheet_name,
                            'row_number': row,
                            'class_sno': sheet.cell(row=row, column=headers.get('Class_S.No', 2)).value,
                            'gr_number': sheet.cell(row=row, column=headers.get('GR#', 3)).value,
                            'student_name': sheet.cell(row=row, column=headers.get('Student Name', 4)).value,
                            'father_name': sheet.cell(row=row, column=headers.get("Father's Name", 5)).value,
                            'gender': sheet.cell(row=row, column=headers.get('Gender', 6)).value,
                            'religion': sheet.cell(row=row, column=headers.get('Religion', 7)).value,
                            'contact_number': sheet.cell(row=row, column=headers.get('Contact Number', 8)).value,
                            'cnic_bform': sheet.cell(row=row, column=headers.get('CNIC / B-Form', 9)).value,
                            'date_of_birth': sheet.cell(row=row, column=headers.get('Date of Birth', 10)).value,
                            'father_mother_cnic': sheet.cell(row=row, column=headers.get("Father/Mother's CNIC", 11)).value,
                            'guardian_name': sheet.cell(row=row, column=headers.get('Guardian Name', 12)).value,
                            'guardian_cnic': sheet.cell(row=row, column=headers.get('Guardian CNIC', 13)).value,
                            'guardian_relation': sheet.cell(row=row, column=headers.get('Guardian Relation', 14)).value,
                            'student_class': sheet.cell(row=row, column=headers.get('Student Class', 15)).value or sheet_name.replace('Class_', ''),
                            'class_section': sheet.cell(row=row, column=headers.get('Class Section', 16)).value
                        }
                        all_students.append(student)
                        sno_counter += 1
        
        return jsonify({'success': True, 'students': all_students})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/student_details/<sheet_name>/<int:row_number>')
@admin_required
def api_student_details(sheet_name, row_number):
    """API endpoint to get complete student details (Admin only)"""
    try:
        if sheet_name not in data_entry.workbook.sheetnames:
            return jsonify({'success': False, 'message': 'Sheet not found'})
        
        sheet = data_entry.workbook[sheet_name]
        
        # Get header row to find column indices
        headers = {}
        for col in range(1, sheet.max_column + 1):
            header_value = sheet.cell(row=1, column=col).value
            if header_value:
                headers[header_value] = col
        
        # Get complete student data
        student_details = {}
        for header, col in headers.items():
            cell_value = sheet.cell(row=row_number, column=col).value
            student_details[header] = cell_value if cell_value is not None else 'N/A'
        
        return jsonify({'success': True, 'student': student_details})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/teacher_student_details/<sheet_name>/<int:row_number>')
@login_required
def api_teacher_student_details(sheet_name, row_number):
    """API endpoint to get complete student details for teachers"""
    user_access = session.get('access')
    
    # Extract class name from sheet name (e.g., "Class_I" -> "I")
    class_name = sheet_name.replace('Class_', '')
    
    # Check if user has access to this class
    if user_access != 'all' and user_access != class_name:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    try:
        if sheet_name not in data_entry.workbook.sheetnames:
            return jsonify({'success': False, 'message': 'Sheet not found'})
        
        sheet = data_entry.workbook[sheet_name]
        
        # Get header row to find column indices
        headers = {}
        for col in range(1, sheet.max_column + 1):
            header_value = sheet.cell(row=1, column=col).value
            if header_value:
                headers[header_value] = col
        
        # Get complete student data
        student_details = {}
        for header, col in headers.items():
            cell_value = sheet.cell(row=row_number, column=col).value
            student_details[header] = cell_value if cell_value is not None else 'N/A'
        
        return jsonify({'success': True, 'student': student_details})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/edit_student/<sheet_name>/<int:row_number>', methods=['POST'])
@login_required
def api_edit_student(sheet_name, row_number):
    """API endpoint to edit student details for teachers"""
    user_access = session.get('access')
    
    # Extract class name from sheet name (e.g., "Class_I" -> "I")
    class_name = sheet_name.replace('Class_', '')
    
    # Check if user has access to this class
    if user_access != 'all' and user_access != class_name:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    try:
        if sheet_name not in data_entry.workbook.sheetnames:
            return jsonify({'success': False, 'message': 'Sheet not found'})
        
        sheet = data_entry.workbook[sheet_name]
        form_data = request.get_json()
        
        # Get header row to find column indices
        headers = {}
        for col in range(1, sheet.max_column + 1):
            header_value = sheet.cell(row=1, column=col).value
            if header_value:
                headers[header_value] = col
        
        # Update student data (excluding GR# which should not be editable)
        editable_fields = [
            'Student Name', 'Father\'s Name', 'Gender', 'Religion', 
            'Contact Number', 'CNIC / B-Form', 'Date of Birth', 
            'Father/Mother\'s CNIC', 'Guardian Name', 'Guardian CNIC', 
            'Guardian Relation', 'Student Class', 'Class Section', 
            'Date of Admission'
        ]
        
        for field in editable_fields:
            if field in form_data and field in headers:
                col = headers[field]
                new_value = form_data[field]
                
                # Format CNIC numbers
                if 'CNIC' in field and new_value and new_value != '-':
                    new_value = data_entry.format_cnic(new_value)
                
                sheet.cell(row=row_number, column=col, value=new_value)
        
        # Save the workbook
        data_entry.workbook.save(data_entry.excel_file)
        
        return jsonify({'success': True, 'message': 'Student details updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/delete_student/<sheet_name>/<int:row_number>', methods=['DELETE'])
@admin_required
def api_delete_student(sheet_name, row_number):
    """API endpoint to delete a student from Excel file"""
    try:
        if sheet_name not in data_entry.workbook.sheetnames:
            return jsonify({'success': False, 'message': 'Sheet not found'})
        
        sheet = data_entry.workbook[sheet_name]
        
        # Check if row exists and has data
        if row_number < 2 or row_number > sheet.max_row:
            return jsonify({'success': False, 'message': 'Invalid row number'})
        
        if not sheet.cell(row=row_number, column=1).value:
            return jsonify({'success': False, 'message': 'Student not found'})
        
        # Get student name for confirmation
        student_name = sheet.cell(row=row_number, column=3).value  # Assuming column 3 is Student Name
        
        # Delete the row
        sheet.delete_rows(row_number)
        
        # Update S.No for remaining students
        sno_col = 1  # Assuming column 1 is S.No
        current_sno = 1
        for row in range(2, sheet.max_row + 1):
            if sheet.cell(row=row, column=sno_col).value is not None:
                sheet.cell(row=row, column=sno_col).value = current_sno
                current_sno += 1
        
        # Save the workbook
        data_entry.workbook.save(data_entry.excel_file)
        
        return jsonify({
            'success': True, 
            'message': f'Student "{student_name}" has been deleted successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/navigate_student/<sheet_name>/<int:row_number>/<direction>')
@admin_required
def api_navigate_student(sheet_name, row_number, direction):
    """API endpoint to navigate to next/previous student"""
    try:
        if sheet_name not in data_entry.workbook.sheetnames:
            return jsonify({'success': False, 'message': 'Sheet not found'})
        
        sheet = data_entry.workbook[sheet_name]
        
        if direction == 'next':
            next_row = row_number + 1
            while next_row <= sheet.max_row:
                if sheet.cell(row=next_row, column=1).value is not None:
                    return jsonify({'success': True, 'row_number': next_row})
                next_row += 1
            return jsonify({'success': False, 'message': 'No next student found'})
        
        elif direction == 'previous':
            prev_row = row_number - 1
            while prev_row >= 2:  # Start from row 2 (skip header)
                if sheet.cell(row=prev_row, column=1).value is not None:
                    return jsonify({'success': True, 'row_number': prev_row})
                prev_row -= 1
            return jsonify({'success': False, 'message': 'No previous student found'})
        
        else:
            return jsonify({'success': False, 'message': 'Invalid direction'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/get_student_name/<sheet_name>/<int:row_number>')
@admin_required
def api_get_student_name(sheet_name, row_number):
    """API endpoint to get student name for delete confirmation"""
    try:
        if sheet_name not in data_entry.workbook.sheetnames:
            return jsonify({'success': False, 'message': 'Sheet not found'})
        
        sheet = data_entry.workbook[sheet_name]
        
        if row_number < 2 or row_number > sheet.max_row:
            return jsonify({'success': False, 'message': 'Invalid row number'})
        
        # Find Student Name column
        headers = {}
        for col in range(1, sheet.max_column + 1):
            header_value = sheet.cell(row=1, column=col).value
            if header_value:
                headers[header_value] = col
        
        if 'Student Name' not in headers:
            return jsonify({'success': False, 'message': 'Student Name column not found'})
        
        student_name = sheet.cell(row=row_number, column=headers['Student Name']).value
        
        return jsonify({'success': True, 'student_name': student_name or 'Unknown'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/student_details')
@admin_required
def student_details():
    """Student details page (Admin only)"""
    return render_template('student_details.html')

@app.route('/teacher_student_details')
@login_required
def teacher_student_details():
    """Teacher student details page"""
    return render_template('teacher_student_details.html')

@app.route('/teacher_student_edit')
@login_required
def teacher_student_edit():
    """Teacher student edit page"""
    return render_template('teacher_student_edit.html')

@app.route('/api/consolidate_data', methods=['POST'])
@admin_required
def api_consolidate_data():
    """Consolidate all student data and return as downloadable file"""
    try:
        # Run the consolidation process
        consolidate_student_data()
        
        # Check if the consolidated file was created
        consolidated_file = '408070227.xlsx'
        if os.path.exists(consolidated_file):
            # Return the file for download
            return send_file(
                consolidated_file,
                as_attachment=True,
                download_name='408070227.xlsx',
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        else:
            return jsonify({'error': 'Consolidated file not found'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Consolidation failed: {str(e)}'}), 500

@app.route('/settings')
@admin_required
def settings():
    """Settings page (placeholder)"""
    return "<h1>Settings</h1><p>This feature will be implemented soon.</p><a href='/dashboard'>← Back to Dashboard</a>"

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print("Starting Student Data Entry Web Server...")
    print(f"Access from mobile: http://YOUR_PC_IP:{port}")
    print(f"Access locally: http://localhost:{port}")
    print("\nDefault login credentials:")
    print("Admin: admin/admin")
    print("Class teachers: class1/class1, class2/class2, etc.")
    print("ECE teacher: ece/ece")
    app.run(host='0.0.0.0', port=port, debug=debug)