#!/usr/bin/env python3
"""
Google Sheets Student Data Entry System
Replaces Excel with Google Sheets for cloud storage and persistence
"""

import os
import json
from datetime import datetime
import re
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import time
import random

class GoogleSheetsDataEntry:
    def __init__(self, spreadsheet_id=None, credentials_file=None):
        # Load environment variables from .env file if available
        from dotenv import load_dotenv
        load_dotenv()
        
        self.spreadsheet_id = spreadsheet_id or os.environ.get('GOOGLE_SHEETS_ID')
        self.credentials_file = credentials_file or os.environ.get('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
        
        # Validate required parameters
        if not self.spreadsheet_id:
            raise ValueError("Google Sheets ID is required. Set GOOGLE_SHEETS_ID environment variable or pass spreadsheet_id parameter.")
        
        self.headers = [
            "Class_S.No", 
            "GR#",
            "Student Name",
            "Father's Name",
            "Gender",
            "Religion",
            "Contact Number",
            "CNIC / B-Form",
            "Date of Birth",
            "Father/Mother's CNIC",
            "Guardian Name",
            "Guardian CNIC",
            "Guardian Relation",
            "Student Class",
            "Class Section",
            "SEMIS Code",
            "Date of Admission",
            "Remarks"
        ]
        
        self.service = None
        self.setup_google_sheets()
    
    def setup_google_sheets(self):
        """Setup Google Sheets API connection"""
        try:
            # Load credentials from environment variable or file
            if os.environ.get('GOOGLE_CREDENTIALS_JSON'):
                # For Railway deployment - credentials as environment variable
                credentials_info = json.loads(os.environ.get('GOOGLE_CREDENTIALS_JSON'))
                credentials = Credentials.from_service_account_info(
                    credentials_info,
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
            elif os.path.exists(self.credentials_file):
                # For local development - credentials file
                credentials = Credentials.from_service_account_file(
                    self.credentials_file,
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
            else:
                raise FileNotFoundError("Google Sheets credentials not found")
            
            self.service = build('sheets', 'v4', credentials=credentials)

            # Create or setup the main worksheet
            self.setup_main_worksheet()
            
        except Exception as e:
            print(f"Error setting up Google Sheets: {e}")
            raise

    def _execute_request(self, request, max_retries=5, initial_backoff=0.5):
        """Execute a google-api-python-client request with retries on transient errors.

        request: a prepared request object (e.g., service.spreadsheets().get(...))
        Returns the parsed JSON response from .execute().
        """
        backoff = initial_backoff
        for attempt in range(max_retries):
            try:
                return request.execute()
            except HttpError as e:
                status = None
                try:
                    status = int(e.resp.status)
                except Exception:
                    pass

                # Retry on 5xx or 429 (rate limit)
                if status and (500 <= status < 600 or status == 429):
                    sleep_time = backoff + random.random() * backoff
                    time.sleep(sleep_time)
                    backoff *= 2
                    continue
                # Non-retryable error: re-raise
                raise
            except Exception:
                # For unknown errors, do a short backoff and retry a couple times
                time.sleep(backoff)
                backoff *= 2
        # Final attempt without catching to surface error
        return request.execute()
    
    def setup_main_worksheet(self):
        """Setup main worksheet with headers if it doesn't exist"""
        try:
            # Check if the spreadsheet exists and has the main sheet
            sheet_metadata = self._execute_request(
                self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id)
            )
            
            # Check if '408070227' sheet exists
            sheet_names = [sheet['properties']['title'] for sheet in sheet_metadata['sheets']]
            
            if '408070227' not in sheet_names:
                # Create the main sheet
                self.create_worksheet('408070227')
            
            # Add headers if they don't exist
            self.add_headers_to_sheet('408070227')
            
        except HttpError as e:
            print(f"Error setting up main worksheet: {e}")
            raise
    
    def create_worksheet(self, sheet_name):
        """Create a new worksheet"""
        try:
            request_body = {
                'requests': [{
                    'addSheet': {
                        'properties': {
                            'title': sheet_name
                        }
                    }
                }]
            }

            self._execute_request(
                self.service.spreadsheets().batchUpdate(spreadsheetId=self.spreadsheet_id, body=request_body)
            )

        except HttpError as e:
            print(f"Error creating worksheet {sheet_name}: {e}")
            raise
    
    def add_headers_to_sheet(self, sheet_name):
        """Add headers to a sheet if they don't exist"""
        try:
            # Check if headers already exist
            result = self._execute_request(
                self.service.spreadsheets().values().get(spreadsheetId=self.spreadsheet_id, range=f'{sheet_name}!A1:R1')
            )
            
            values = result.get('values', [])
            
            if not values or values[0] != self.headers:
                # Add headers
                self._execute_request(
                    self.service.spreadsheets().values().update(
                        spreadsheetId=self.spreadsheet_id,
                        range=f'{sheet_name}!A1:R1',
                        valueInputOption='RAW',
                        body={'values': [self.headers]}
                    )
                )
                
        except HttpError as e:
            print(f"Error adding headers to {sheet_name}: {e}")
            raise
    
    def get_or_create_class_sheet(self, student_class):
        """Get or create a class-specific sheet"""
        try:
            # Convert class name to proper sheet name format
            sheet_name = f'Class_{student_class}' if not student_class.startswith('Class_') else student_class
            
            sheet_metadata = self._execute_request(
                self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id)
            )
            
            sheet_names = [sheet['properties']['title'] for sheet in sheet_metadata['sheets']]
            
            if sheet_name not in sheet_names:
                self.create_worksheet(sheet_name)
                self.add_headers_to_sheet(sheet_name)
            
            return sheet_name
            
        except HttpError as e:
            print(f"Error getting/creating class sheet {sheet_name}: {e}")
            raise
    
    def check_duplicate_gr(self, gr_number):
        """Check if GR number already exists"""
        try:
            # Search in main sheet
            result = self._execute_request(
                self.service.spreadsheets().values().get(spreadsheetId=self.spreadsheet_id, range='408070227!B:B')
            )
            
            values = result.get('values', [])
            gr_numbers = [row[0] if row else '' for row in values[1:]]  # Skip header
            
            return gr_number in gr_numbers
            
        except HttpError as e:
            print(f"Error checking duplicate GR: {e}")
            return False
    
    def get_next_class_serial_number(self, student_class):
        """Get the next serial number for a class"""
        try:
            # Get or create class sheet
            sheet_name = self.get_or_create_class_sheet(student_class)
            
            # Get all data from class sheet - use Class_S.No column (column B)
            result = self._execute_request(
                self.service.spreadsheets().values().get(spreadsheetId=self.spreadsheet_id, range=f'{sheet_name}!A:A')
            )
            
            values = result.get('values', [])
            
            if len(values) <= 1:  # Only headers or empty
                return 1
            
            # Find the highest serial number
            serial_numbers = []
            for row in values[1:]:  # Skip header
                if row and row[0]:
                    try:
                        serial_numbers.append(int(row[0]))
                    except ValueError:
                        continue
            
            return max(serial_numbers) + 1 if serial_numbers else 1
            
        except HttpError as e:
            print(f"Error getting next serial number: {e}")
            return 1
    
    def add_student_record(self, student_data):
        """Add a student record to both main sheet and class sheet"""
        try:
            student_class = student_data.get('Student Class', '')

            # If Class_S.No is missing/empty, auto-generate using existing class sheet entries (class-wise)
            class_sno = student_data.get('Class_S.No')
            if (not class_sno or str(class_sno).strip() == '') and student_class:
                try:
                    # Ensure class sheet exists and get its name
                    class_sheet_name = self.get_or_create_class_sheet(student_class)

                    # Read the first column (Class_S.No) for the class sheet to compute highest existing suffix
                    sheet_values = self.get_sheet_data(class_sheet_name, range_spec='A:A')
                    max_num = 0
                    prefix = str(student_class).strip()

                    for row in sheet_values[1:]:  # skip header
                        val = row[0] if row and len(row) > 0 else ''
                        if not val:
                            continue
                        # Match formats like PREFIX_01, PREFIX-01, PREFIX01 or just trailing digits
                        m = re.match(rf'^(?:{re.escape(prefix)}[_-]?)?(\d+)$', str(val).strip())
                        if m:
                            try:
                                num = int(m.group(1))
                                if num > max_num:
                                    max_num = num
                            except Exception:
                                continue

                    next_num = max_num + 1
                    # Format as PREFIX_XX with zero padding to 2 digits
                    student_data['Class_S.No'] = f"{prefix}_{str(next_num).zfill(2)}"
                except Exception:
                    # Non-fatal: leave Class_S.No blank if computation fails
                    pass

            # Prepare row data from headers (ensure Class_S.No used)
            row_data = [student_data.get(header, '') for header in self.headers]

            # Add to main sheet (408070227)
            self.append_row_to_sheet('408070227', row_data)

            # Add to class-specific sheet
            if student_class:
                class_sheet = self.get_or_create_class_sheet(student_class)
                self.append_row_to_sheet(class_sheet, row_data)

            return True
            
        except Exception as e:
            print(f"Error adding student record: {e}")
            return False
    
    def append_row_to_sheet(self, sheet_name, row_data):
        """Append a row to a specific sheet"""
        try:
            self._execute_request(
                self.service.spreadsheets().values().append(
                    spreadsheetId=self.spreadsheet_id,
                    range=f'{sheet_name}!A:R',
                    valueInputOption='RAW',
                    insertDataOption='INSERT_ROWS',
                    body={'values': [row_data]}
                )
            )

        except HttpError as e:
            print(f"Error appending row to {sheet_name}: {e}")
            raise
    
    def get_all_students(self):
        """Get all students from main sheet"""
        try:
            result = self._execute_request(
                self.service.spreadsheets().values().get(spreadsheetId=self.spreadsheet_id, range='408070227!A:R')
            )
            
            values = result.get('values', [])
            
            if not values:
                return []
            
            # Convert to list of dictionaries
            students = []
            headers = values[0]
            
            for row in values[1:]:
                # Pad row with empty strings if needed
                while len(row) < len(headers):
                    row.append('')
                
                student = dict(zip(headers, row))
                students.append(student)
            
            return students
            
        except HttpError as e:
            print(f"Error getting all students: {e}")
            return []
    
    def get_class_students(self, class_name):
        """Get all students from a specific class sheet"""
        try:
            # Convert class name to proper sheet name format
            sheet_name = f'Class_{class_name}' if not class_name.startswith('Class_') else class_name
            result = self._execute_request(
                self.service.spreadsheets().values().get(spreadsheetId=self.spreadsheet_id, range=f'{sheet_name}!A:R')
            )
            
            values = result.get('values', [])
            
            if not values:
                return []
            
            # Convert to list of dictionaries
            students = []
            headers = values[0]
            
            for row in values[1:]:
                # Pad row with empty strings if needed
                while len(row) < len(headers):
                    row.append('')
                
                student = dict(zip(headers, row))
                students.append(student)
            
            return students
            
        except HttpError as e:
            print(f"Error getting class students: {e}")
            return []
    
    def update_student_record(self, sheet_name, row_number, student_data):
        """Update a student record in a specific sheet"""
        try:
            # Prepare row data
            row_data = [student_data.get(header, '') for header in self.headers]
            
            # Update the specific row
            self._execute_request(
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=f'{sheet_name}!A{row_number}:R{row_number}',
                    valueInputOption='RAW',
                    body={'values': [row_data]}
                )
            )
            
            return True
            
        except HttpError as e:
            print(f"Error updating student record: {e}")
            return False
    
    def delete_student_record(self, sheet_name, row_number):
        """Delete a student record from a specific sheet"""
        try:
            # Get sheet ID
            sheet_metadata = self._execute_request(
                self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id)
            )
            
            sheet_id = None
            for sheet in sheet_metadata['sheets']:
                if sheet['properties']['title'] == sheet_name:
                    sheet_id = sheet['properties']['sheetId']
                    break
            
            if sheet_id is None:
                return False
            
            # Delete the row
            request_body = {
                'requests': [{
                    'deleteDimension': {
                        'range': {
                            'sheetId': sheet_id,
                            'dimension': 'ROWS',
                            'startIndex': row_number - 1,  # 0-indexed
                            'endIndex': row_number
                        }
                    }
                }]
            }
            
            self._execute_request(
                self.service.spreadsheets().batchUpdate(spreadsheetId=self.spreadsheet_id, body=request_body)
            )
            
            return True
            
        except HttpError as e:
            print(f"Error deleting student record: {e}")
            return False
    
    def get_total_students(self):
        """Get total number of students"""
        students = self.get_all_students()
        return len(students)
    
    def get_class_student_count(self, class_name):
        """Get count of students in a specific class"""
        try:
            sheet_name = f'Class_{class_name}' if not class_name.startswith('Class_') else class_name
            
            if not self.sheet_exists(sheet_name):
                return 0
            
            sheet_data = self.get_sheet_data(sheet_name)
            if not sheet_data or len(sheet_data) <= 1:
                return 0
            
            # Count non-empty rows (excluding header)
            count = 0
            for row_data in sheet_data[1:]:
                if row_data and len(row_data) > 0 and row_data[0]:  # Check if S.No exists
                    count += 1
                    
            return count
        except Exception as e:
            print(f"Error getting student count for {class_name}: {e}")
            return 0
    
    def get_class_gender_count(self, class_name, gender):
        """Get count of students by gender in a specific class"""
        try:
            sheet_name = f'Class_{class_name}' if not class_name.startswith('Class_') else class_name
            
            if not self.sheet_exists(sheet_name):
                return 0
            
            sheet_data = self.get_sheet_data(sheet_name)
            if not sheet_data or len(sheet_data) <= 1:
                return 0
            
            headers = sheet_data[0]
            header_indices = {header: idx for idx, header in enumerate(headers)}
            gender_index = header_indices.get('Gender', 4)
            
            gender_count = 0
            for row_data in sheet_data[1:]:
                if row_data and len(row_data) > gender_index and row_data[gender_index]:
                    if row_data[gender_index].strip().lower() == gender.lower():
                        gender_count += 1
                        
            return gender_count
        except Exception as e:
            print(f"Error getting gender count for {class_name}: {e}")
            return 0
    
    def get_class_section_count(self, class_name, section):
        """Get count of students by section in a specific class"""
        students = self.get_class_students(class_name)
        section_count = 0
        
        for student in students:
            if len(student) > 14 and student[14].strip().lower() == section.lower():
                section_count += 1
                
        return section_count
    
    def sheet_exists(self, sheet_name):
        """Check if a sheet exists in the spreadsheet"""
        try:
            sheet_metadata = self._execute_request(
                self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id)
            )
            
            sheet_names = [sheet['properties']['title'] for sheet in sheet_metadata['sheets']]
            return sheet_name in sheet_names
            
        except HttpError as e:
            print(f"Error checking if sheet exists: {e}")
            return False
    
    def get_sheet_data(self, sheet_name, range_spec='A:R'):
        """Get data from a specific sheet"""
        try:
            result = self._execute_request(
                self.service.spreadsheets().values().get(spreadsheetId=self.spreadsheet_id, range=f'{sheet_name}!{range_spec}')
            )

            return result.get('values', [])

        except HttpError as e:
            print(f"Error getting sheet data: {e}")
            return []
    
    def validate_input(self, field_name, value):
        """Validate input fields"""
        if field_name == "Contact Number":
            if not re.match(r'^[0-9+\-\s()]+$', value):
                return False, "Contact number should contain only numbers, +, -, spaces, and parentheses"
        
        elif field_name == "CNIC / B-Form":
            # Remove spaces and dashes for validation
            clean_value = re.sub(r'[\s\-]', '', value)
            if not re.match(r'^[0-9]{13}$', clean_value):
                return False, "CNIC/B-Form should be 13 digits"
        
        elif field_name == "Father/Mother's CNIC":
            clean_value = re.sub(r'[\s\-]', '', value)
            if not re.match(r'^[0-9]{13}$', clean_value):
                return False, "Parent's CNIC should be 13 digits"
        
        elif field_name == "Guardian CNIC":
            if value:  # Optional field
                clean_value = re.sub(r'[\s\-]', '', value)
                if not re.match(r'^[0-9]{13}$', clean_value):
                    return False, "Guardian CNIC should be 13 digits"
        
        return True, ""
    
    def format_cnic(self, cnic_number):
        """Format CNIC number with dashes"""
        # Remove any existing formatting
        clean_cnic = re.sub(r'[^0-9]', '', cnic_number)
        
        # Add formatting if it's 13 digits
        if len(clean_cnic) == 13:
            return f"{clean_cnic[:5]}-{clean_cnic[5:12]}-{clean_cnic[12]}"
        
        return cnic_number
    
    def get_class_wise_data(self):
        """Get data overview for all classes"""
        try:
            # Get class sheets
            sheet_metadata = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            class_sheets = [sheet['properties']['title'] for sheet in sheet_metadata['sheets']
                          if sheet['properties']['title'].startswith('Class_')]
            
            class_data = []
            for sheet_name in class_sheets:
                # Get student count
                student_count = self.get_class_student_count(sheet_name.replace('Class_', ''))
                
                # Get gender counts
                male_count = self.get_class_gender_count(sheet_name.replace('Class_', ''), 'Male')
                female_count = self.get_class_gender_count(sheet_name.replace('Class_', ''), 'Female')
                
                class_data.append({
                    'name': sheet_name.replace('Class_', ''),
                    'total_students': student_count,
                    'male_students': male_count,
                    'female_students': female_count
                })
            
            return class_data
            
        except Exception as e:
            print(f"Error getting class-wise data: {e}")
            return []

    def update_student_record(self, sheet_name, row_number, student_data):
        """Update a student record in the specified sheet"""
        try:
            # Get current sheet data
            sheet_data = self.get_sheet_data(sheet_name)
            if not sheet_data or len(sheet_data) < row_number:
                print(f"Row {row_number} not found in sheet {sheet_name}")
                return False
            
            # Get headers
            headers = sheet_data[0]
            header_indices = {header: idx for idx, header in enumerate(headers)}
            
            # Prepare the updated row
            updated_row = [''] * len(headers)
            
            # Map student data to the correct columns
            for field, value in student_data.items():
                if field in header_indices:
                    col_index = header_indices[field]
                    # Format CNIC fields
                    if 'CNIC' in field and value:
                        value = self.format_cnic(value)
                    updated_row[col_index] = str(value) if value else ''
            
            # Update the row in Google Sheets
            range_name = f'{sheet_name}!A{row_number}:R{row_number}'
            
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body={'values': [updated_row]}
            ).execute()
            
            print(f"Successfully updated student record in {sheet_name} at row {row_number}")
            return True
            
        except Exception as e:
            print(f"Error updating student record: {e}")
            return False

def main():
    """Main function for testing"""
    print("Google Sheets Student Data Entry System")
    print("This module provides Google Sheets integration for the student management system.")
    print("Please configure your Google Sheets credentials and spreadsheet ID.")

if __name__ == "__main__":
    main()