# Student Data Entry System

A comprehensive student data management system with both web and command-line interfaces for adding student data to Excel files or Google Sheets with class-wise organization.

## Features

- **Web Interface**: Modern, mobile-friendly web dashboard with navigation
- **CLI Interface**: User-friendly command-line interface for data entry
- **Class-wise Organization**: Automatic organization of students into class-specific sheets
- **Data Validation**: Built-in validation for phone numbers, CNIC format, dates, and gender
- **Unified Serial Numbers**: Sequential S.No across all classes for simplified tracking
- **Dual Storage Options**: 
  - **Excel Integration**: Works directly with Excel files using openpyxl
  - **Google Sheets Integration**: Cloud-based storage with real-time collaboration
- **Error Handling**: Comprehensive error handling and user feedback
- **Dashboard Statistics**: Real-time statistics and quick navigation
- **Cloud Deployment Ready**: Optimized for Railway deployment with persistent data storage

## Student Data Fields

The system collects the following information for each student:

1. **S.No** (Auto-generated sequential number)
2. **GR#** (General Register Number)
3. **Student Name**
4. **Father's Name**
5. **Gender** (Male/Female)
6. **Religion**
7. **Contact Number**
8. **CNIC / B-Form**
9. **Date of Birth** (DD/MM/YYYY format)
10. **Father/Mother's CNIC**
11. **Guardian Name** (Optional)
12. **Guardian CNIC** (Optional)
13. **Guardian Relation** (Optional)
14. **Student Class** (ECE, I-X)
15. **Class Section** (Auto-set to Girls for female students, Boys for male students)
16. **SEMIS Code** (Auto-set to 408070227)
17. **Date of Admission** (DD/MM/YYYY format)

## Installation

1. **Install Python** (if not already installed)
   - Download from [python.org](https://python.org)
   - Make sure Python is added to your system PATH

2. **Install Required Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   
   Or install manually:
   ```bash
   pip install openpyxl flask gunicorn
   # For Google Sheets integration:
   pip install google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2
   ```

## Storage Options

### Option 1: Excel Storage (Default)
- Data stored in local Excel files
- Works offline
- Suitable for single-user scenarios
- Files may be lost on cloud deployments

### Option 2: Google Sheets Storage (Recommended for Cloud)
- Data stored in Google Sheets
- Cloud-based and persistent
- Real-time collaboration
- Survives application restarts
- **Setup Required**: See [Google Sheets Setup Guide](GOOGLE_SHEETS_SETUP.md)

## Usage

### Web Interface (Recommended)

1. **Start the Web Server**
   ```bash
   python web_app.py
   ```

2. **Access the Dashboard**
   - **Local**: http://localhost:5000
   - **Mobile**: http://YOUR_PC_IP:5000

3. **Navigate the Dashboard**
   - View real-time statistics
   - Click "Data Entry" to add new students
   - Use other navigation buttons for different features

4. **Add Student Data**
   - Fill out the mobile-friendly form
   - System automatically validates and saves to appropriate class sheet
   - Receive instant confirmation

### Command Line Interface

1. **Run the CLI Program**
   ```bash
   python student_data_entry.py
   ```

2. **Follow the Prompts**
   - The program will guide you through each field
   - Enter the required information when prompted
   - Some fields are optional and can be left empty
   - The program provides format hints for specific fields

### Data Validation (Both Interfaces)
   - **Dates**: Use DD/MM/YYYY or DD-MM-YYYY format
   - **Gender**: Enter Male/Female or M/F
   - **Phone Numbers**: Use numbers, spaces, dashes, parentheses, and + sign
   - **CNIC**: Use numbers and dashes (e.g., 12345-6789012-3)

## Example Usage

```
============================================================
           STUDENT DATA ENTRY SYSTEM
============================================================

S.No: 1 (Auto-generated)

Class S.no: 15

GR#: GR2025001

Student Name: Ahmed Ali

Father's Name: Muhammad Ali

Gender (Male/Female or M/F): Male

Religion: Islam

Contact Number (e.g., +92-300-1234567): +92-300-1234567

CNIC / B-Form (e.g., 12345-6789012-3): 12345-6789012-3

Date of Birth (DD/MM/YYYY or DD-MM-YYYY): 15/03/2010

... (continue for all fields)
```

## File Structure

```
students_data_feeding_program/
├── student_data_entry.py      # CLI program and core functionality
├── web_app.py                 # Web server and dashboard
├── requirements.txt           # Python dependencies
├── students_data_2025.xlsx   # Excel file with class-wise sheets
├── static/
│   └── logo.png              # School logo for web interface
├── templates/
│   ├── index.html            # Main dashboard page
│   ├── form.html             # Student data entry form
│   └── error.html            # Error page template
├── CLASS_WISE_SHEETS.md      # Documentation for class organization
├── MOBILE_SETUP.md           # Mobile access setup guide
└── README.md                 # This file
```

## Features in Detail

### Class-wise Organization
- Automatically creates separate Excel sheets for each class (Class_ECE, Class_I, etc.)
- Students are organized by their class for better management
- Maintains unified serial numbering across all classes

### Unified Serial Numbers
- Sequential S.No across all classes (1, 2, 3, 4...)
- No separate class-wise numbering for simplified tracking
- Automatic duplicate prevention across all sheets

### Data Validation
- **Required Fields**: Student Name, Father's Name, GR#, Student Class
- **Optional Fields**: Guardian Name, Guardian CNIC, Guardian Relation
- **Format Validation**: Ensures proper format for dates, phone numbers, and CNIC
- **Gender Normalization**: Converts M/F to Male/Female automatically
- **GR# Duplicate Check**: Prevents duplicate GR numbers across all classes

### Excel File Handling
- Creates Excel file and class sheets automatically
- Adds headers automatically on first run
- Preserves existing data when adding new records
- Handles file errors gracefully

### Web Dashboard
- Modern, responsive design for desktop and mobile
- Real-time statistics display
- Easy navigation between different features
- Mobile-optimized data entry form

## Troubleshooting

### Common Issues

1. **"No module named 'openpyxl'"**
   - Install openpyxl: `pip install openpyxl`

2. **Permission Error when saving Excel file**
   - Close the Excel file if it's open in another program
   - Check file permissions

3. **Date format errors**
   - Use DD/MM/YYYY format (e.g., 15/03/2010)
   - Or DD-MM-YYYY format (e.g., 15-03-2010)

4. **CNIC format errors**
   - Use format: 12345-6789012-3
   - Include dashes between number groups

### Getting Help

- Check error messages for specific guidance
- Ensure all required fields are filled
- Verify date and CNIC formats
- Make sure Excel file is not open in another program

## License

This program is free to use for educational purposes.