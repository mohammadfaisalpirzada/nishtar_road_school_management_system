#!/usr/bin/env python3
"""
Setup Google Sheets for the School Management System
Creates all required sheets and sets up headers
"""

from google_sheets_data_entry import GoogleSheetsDataEntry

def setup_sheets():
    """Create and setup all required sheets"""
    print("Setting up Google Sheets...")
    data_entry = GoogleSheetsDataEntry()
    
    # List of all class sheets to create
    classes = ['ECE', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']
    
    # Ensure main sheet exists
    data_entry.setup_main_worksheet()
    print("✅ Main worksheet (408070227) ready")
    
    # Create class sheets
    for class_name in classes:
        sheet_name = f'Class_{class_name}'
        try:
            if not data_entry.sheet_exists(sheet_name):
                data_entry.create_worksheet(sheet_name)
                print(f"Created sheet for class {class_name}")
            data_entry.add_headers_to_sheet(sheet_name)
            print(f"✅ Sheet for class {class_name} ready")
        except Exception as e:
            print(f"❌ Error setting up {sheet_name}: {e}")
    
    print("\nSetup complete! You can now use the web application.")

if __name__ == "__main__":
    setup_sheets()
