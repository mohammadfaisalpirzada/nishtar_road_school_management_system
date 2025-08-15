# Google Sheets Setup Guide

This guide explains how to set up Google Sheets integration for the Nishtar Road School Management System.

## Why Google Sheets?

- **Cloud Storage**: Data is stored in the cloud, not locally
- **Persistent**: Data survives application restarts and redeployments
- **Accessible**: Can be viewed and edited directly in Google Sheets
- **Collaborative**: Multiple users can access the same data
- **Backup**: Google automatically backs up your data

## Prerequisites

1. A Google account
2. Access to Google Cloud Console
3. Basic understanding of Google Sheets

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "New Project" or select an existing project
3. Give your project a name (e.g., "School Management System")
4. Note down your Project ID

## Step 2: Enable Google Sheets API

1. In Google Cloud Console, go to "APIs & Services" > "Library"
2. Search for "Google Sheets API"
3. Click on it and press "Enable"

## Step 3: Create Service Account Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "Service Account"
3. Fill in the service account details:
   - Name: `school-management-service`
   - Description: `Service account for school management system`
4. Click "Create and Continue"
5. Skip the optional steps and click "Done"

## Step 4: Generate and Download Credentials

1. In the "Credentials" page, find your service account
2. Click on the service account email
3. Go to the "Keys" tab
4. Click "Add Key" > "Create New Key"
5. Choose "JSON" format
6. Download the JSON file
7. Rename it to `credentials.json`

## Step 5: Create Google Spreadsheet

1. Go to [Google Sheets](https://sheets.google.com/)
2. Create a new spreadsheet
3. Give it a name (e.g., "School Student Data 2025")
4. Copy the Spreadsheet ID from the URL:
   ```
   https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit
   ```
5. Share the spreadsheet with your service account:
   - Click "Share" button
   - Add the service account email (from credentials.json)
   - Give it "Editor" permissions

## Step 6: Configure Local Development

1. Place `credentials.json` in your project root directory
2. Create a `.env` file (copy from `.env.example`):
   ```env
   SECRET_KEY=your-secret-key-here
   FLASK_ENV=development
   GOOGLE_SHEETS_ID=1nS0r6tutsUMuR8ViB9LpKIKeD9We9b8r
   GOOGLE_CREDENTIALS_FILE=credentials.json
   ```
   
   **Note**: The `GOOGLE_SHEETS_ID` is extracted from your Google Sheets URL:
   `https://docs.google.com/spreadsheets/d/1nS0r6tutsUMuR8ViB9LpKIKeD9We9b8r/edit...`

## Step 7: Configure Railway Deployment

1. In Railway dashboard, go to your project
2. Click on "Variables" tab
3. Add these environment variables:
   ```
   SECRET_KEY=your-secret-key-here
   FLASK_ENV=production
   GOOGLE_SHEETS_ID=1nS0r6tutsUMuR8ViB9LpKIKeD9We9b8r
   GOOGLE_CREDENTIALS_JSON=paste-entire-credentials-json-content-here
   ```

**Important**: For `GOOGLE_CREDENTIALS_JSON`, paste the entire content of your `credentials.json` file as a single line string.

## Step 8: Test the Setup

1. Run your application locally:
   ```bash
   python web_app.py
   ```
2. Check the console output for:
   ```
   Using Google Sheets for data storage
   ```
3. Try adding a student record
4. Check your Google Spreadsheet to see if data appears

## Troubleshooting

### Common Issues:

1. **"Google Sheets credentials not found"**
   - Check if `credentials.json` exists
   - Verify `GOOGLE_CREDENTIALS_JSON` environment variable

2. **"Permission denied"**
   - Make sure you shared the spreadsheet with service account email
   - Check if service account has "Editor" permissions

3. **"Spreadsheet not found"**
   - Verify the `GOOGLE_SHEETS_ID` is correct
   - Make sure the spreadsheet exists and is accessible

4. **"API not enabled"**
   - Enable Google Sheets API in Google Cloud Console
   - Wait a few minutes for the API to become active

### Fallback to Excel

If Google Sheets setup fails, the application will automatically fall back to Excel storage:
```
Failed to initialize Google Sheets: [error message]
Falling back to Excel storage
```

## Security Notes

1. **Never commit `credentials.json` to version control**
2. **Keep your service account credentials secure**
3. **Use environment variables for production deployment**
4. **Regularly rotate your service account keys**
5. **Limit spreadsheet sharing to necessary accounts only**

## Data Structure

The system will create the following sheets in your Google Spreadsheet:
- `408070227`: Main sheet with all student data
- `I`, `II`, `III`, etc.: Class-specific sheets
- `ECE`: Early Childhood Education sheet

Each sheet will have these columns:
- Class_S.No, GR#, Student Name, Father's Name, Gender, Religion
- Contact Number, CNIC / B-Form, Date of Birth, Father/Mother's CNIC
- Guardian Name, Guardian CNIC, Guardian Relation, Student Class
- Class Section, SEMIS Code, Date of Admission, Remarks

## Benefits of Google Sheets Integration

✅ **Persistent Data**: Survives application restarts and redeployments
✅ **Cloud Backup**: Google automatically backs up your data
✅ **Real-time Access**: View and edit data directly in Google Sheets
✅ **Collaboration**: Multiple users can work with the same data
✅ **Export Options**: Easy to export to Excel, PDF, CSV formats
✅ **Version History**: Google Sheets tracks all changes
✅ **Mobile Access**: Access data from any device with internet

Your school management system is now ready to use Google Sheets for reliable, cloud-based data storage!