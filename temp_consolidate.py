def consolidate_student_data():
    """
    Consolidate all student data from Google Sheets into 408070227.xlsx
    """
    try:
        print("\nInitializing Google Sheets connection...")
        from google_sheets_data_entry import GoogleSheetsDataEntry
        data_entry = GoogleSheetsDataEntry()
        print("Connected to Google Sheets successfully")
        
        # Create new workbook for consolidated data
        target_file = '408070227.xlsx'
        target_wb = Workbook()
        target_ws = target_wb.active
        target_ws.title = "Consolidated_Data"
        
        print("\nSetting up consolidation file...")
        
        # Define headers
        headers = [
            'S.No',
            'Class_S.No',
            'GR#',
            'Student Name',
            'Father\'s Name',
            'Gender',
            'Religion',
            'Contact Number',
            'CNIC / B-Form',
            'Date of Birth',
            'Father/Mother\'s CNIC',
            'Guardian Name',
            'Guardian CNIC',
            'Guardian Relation',
            'Student Class',
            'Class Section',
            'SEMIS Code',
            'Date of Admission'
        ]
        
        # Write headers to target sheet
        for col, header in enumerate(headers, 1):
            target_ws.cell(row=1, column=col, value=header)
        
        # Initialize counters
        combined_sno = 1
        target_row = 2
        total_students = 0
        
        # Process each class in order
        class_order = ['ECE', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']
        
        print("\nStarting data consolidation...\n")
        
        for class_name in class_order:
            sheet_name = f"Class_{class_name}"
            print(f"Processing {sheet_name}...")
            
            try:
                # Get data from Google Sheets
                sheet_data = data_entry.get_sheet_data(sheet_name)
                
                if not sheet_data or len(sheet_data) <= 1:  # Only headers or empty
                    print(f"- No data found in {sheet_name}")
                    continue
                
                # Get headers from first row
                sheet_headers = sheet_data[0]
                header_indices = {header: idx for idx, header in enumerate(sheet_headers)}
                
                # Process each student row
                students_in_class = 0
                for row_data in sheet_data[1:]:  # Skip header row
                    if row_data and len(row_data) > 0 and row_data[0]:  # Check if row has data
                        # Pad row data if needed
                        while len(row_data) < len(sheet_headers):
                            row_data.append('')
                        
                        # Write data to consolidated sheet
                        target_ws.cell(row=target_row, column=1, value=combined_sno)  # Combined S.No
                        
                        # Map data to correct columns
                        field_mapping = {
                            'Class_S.No': 2,
                            'GR#': 3,
                            'Student Name': 4,
                            'Father\'s Name': 5,
                            'Gender': 6,
                            'Religion': 7,
                            'Contact Number': 8,
                            'CNIC / B-Form': 9,
                            'Date of Birth': 10,
                            'Father/Mother\'s CNIC': 11,
                            'Guardian Name': 12,
                            'Guardian CNIC': 13,
                            'Guardian Relation': 14,
                            'Student Class': 15,
                            'Class Section': 16,
                            'SEMIS Code': 17,
                            'Date of Admission': 18
                        }
                        
                        for field, target_col in field_mapping.items():
                            if field in header_indices:
                                source_col = header_indices[field]
                                value = row_data[source_col] if source_col < len(row_data) else ''
                                
                                # Format value based on field type
                                if field in ['CNIC / B-Form', 'Father/Mother\'s CNIC', 'Guardian CNIC']:
                                    formatted_value = format_cnic(value)
                                elif field == 'Contact Number':
                                    formatted_value = format_mobile_number(value)
                                elif field in ['Date of Birth', 'Date of Admission']:
                                    formatted_value = format_date(value)
                                else:
                                    formatted_value = clean_data_value(value)
                                
                                target_ws.cell(row=target_row, column=target_col, value=formatted_value)
                            else:
                                target_ws.cell(row=target_row, column=target_col, value='N/A')
                        
                        # Set Student Class if not present
                        if 'Student Class' not in header_indices:
                            target_ws.cell(row=target_row, column=15, value=class_name)
                        
                        combined_sno += 1
                        target_row += 1
                        students_in_class += 1
                
                print(f"- Processed {students_in_class} students from {sheet_name}")
                total_students += students_in_class
                
            except Exception as e:
                print(f"❌ Error processing {sheet_name}: {str(e)}")
                continue
        
        # Save the consolidated file
        print(f"\nSaving consolidated data to {target_file}...")
        target_wb.save(target_file)
        
        print(f"\n✅ Consolidation completed successfully!")
        print(f"📊 Total students consolidated: {total_students}")
        print(f"📁 Output file: {target_file}")
        
    except Exception as e:
        print(f"\n❌ Error during consolidation: {str(e)}")
        raise e
    
    finally:
        # Close workbook
        if 'target_wb' in locals():
            target_wb.close()
