# Railway Deployment Guide

This guide explains how to deploy the School Management System on Railway.

## Required Environment Variables

Set these in Railway's Variables tab:

```
# Required Settings
SECRET_KEY=your-secure-random-key
ADMIN_PASSWORD=choose-strong-password
GOOGLE_SHEETS_ID=your-spreadsheet-id
GOOGLE_CREDENTIALS_JSON={"type": "service_account", ...}  # Paste entire service account JSON

# Optional Settings
SESSION_COOKIE_SECURE=true
ENABLE_BACKGROUND_SYNC=false  # Set true only for background worker
USE_GOOGLE_SHEETS=true
FLASK_DEBUG=false

# Teacher Passwords (if using environment-based auth)
TEACHER_ECE_PASSWORD=strong-password
TEACHER_I_PASSWORD=strong-password
TEACHER_II_PASSWORD=strong-password
# ... etc for other classes
```

## Deployment Steps

1. Create a new Railway project
2. Connect your GitHub repository
3. Add the environment variables listed above
4. Deploy and verify the health check passes
5. Visit your Railway domain and log in with admin credentials

## Troubleshooting

If the deployment fails:

1. Check Railway logs for errors
2. Verify all required environment variables are set
3. Ensure Google Sheets API is enabled and credentials are correct
4. Try setting USE_GOOGLE_SHEETS=false temporarily to verify the app starts

## Security Notes

1. Use strong passwords for all accounts
2. Change the default admin password
3. Keep your Google service account credentials secure
4. Enable SESSION_COOKIE_SECURE in production

## Background Sync (Optional)

To run background sync in production:

1. Create a second Railway service
2. Use the same environment variables
3. Set ENABLE_BACKGROUND_SYNC=true for this service only
4. Update the Procfile to use minimal resources
