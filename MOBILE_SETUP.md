# 📱 Mobile Student Data Entry Setup

## Overview
This system allows you to enter student data from your mobile device while saving the data to your PC's Excel file.

## Setup Instructions

### 1. Start the Web Server on Your PC
```bash
python web_app.py
```

### 2. Find Your PC's IP Address
The server will display your PC's IP address when it starts. Look for:
```
* Running on http://192.168.10.5:5000
```

### 3. Access from Mobile
On your mobile device, open a web browser and go to:
```
http://YOUR_PC_IP:5000
```
Example: `http://192.168.10.5:5000`

### 4. Access Locally on PC
On the same PC, you can access:
```
http://localhost:5000
```

## Features

### ✅ Mobile-Optimized Interface
- Responsive design for all screen sizes
- Touch-friendly form controls
- Auto-focus and validation

### ✅ All Original Features Included
- **Auto S.No Generation**: Automatically assigns next serial number
- **Class S.No Formatting**: Generates formatted class serial numbers (e.g., "ECE-01")
- **GR# Validation**: Prevents duplicate GR numbers, numeric-only input
- **CNIC Auto-Formatting**: Formats CNIC numbers as XXXXX-XXXXXXX-X
- **Guardian Selection**:
  - **F (Father)**: Copies father's data to guardian fields
  - **O (Others)**: Manual guardian entry
  - **N (Nil)**: Sets all guardian fields to "-"
- **Auto-Set Fields**: SEMIS Code (408070227) and Class Section (Boys for male, Girls for female)

### ✅ Real-Time Features
- **Duplicate GR Check**: Validates GR numbers as you type
- **Auto-Save**: Data saves directly to PC Excel file
- **Success Feedback**: Confirms successful data entry
- **Error Handling**: Clear error messages for validation issues

## Network Requirements

### Same WiFi Network
Both your PC and mobile device must be connected to the same WiFi network.

### Firewall Settings
If you can't access from mobile:
1. Check Windows Firewall settings
2. Allow Python through firewall
3. Ensure port 5000 is not blocked

## Usage Instructions

### 1. Fill Required Fields
- Student Name *
- Father's Name *
- GR Number * (numbers only, auto-checked for duplicates)
- Student Class * (auto-generates Class S.No)

### 2. Optional Fields
- Gender, Date of Birth, Date of Admission
- CNIC/B-Form, Father's CNIC, Contact Number

### 3. Guardian Selection
- **Father**: Automatically copies father's information
- **Others**: Enter custom guardian details
- **Nil**: No guardian information

### 4. Submit
- Tap "💾 Save Student Record"
- Wait for success confirmation
- Form automatically resets for next entry

## Data Storage

- All data saves to `students_data_2025.xlsx` on your PC
- Uses the '408070227' worksheet
- Maintains all existing data and formatting
- Compatible with original desktop application

## Troubleshooting

### Can't Access from Mobile
1. Verify both devices on same WiFi
2. Check PC's IP address in server output
3. Try disabling Windows Firewall temporarily
4. Ensure no VPN is blocking local network access

### Server Won't Start
1. Install Flask: `pip install Flask==2.3.3`
2. Check if port 5000 is already in use
3. Verify Excel file permissions

### Data Not Saving
1. Check Excel file is not open in another program
2. Verify file permissions
3. Check server terminal for error messages

## Security Notes

- Server runs on local network only
- No internet connection required
- Data stays on your PC
- Development server - not for production use

## Stopping the Server

Press `Ctrl+C` in the terminal to stop the web server.