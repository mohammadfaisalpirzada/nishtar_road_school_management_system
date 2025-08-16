# Railway Deployment Guide

This guide explains how to deploy the Nishtar Road School Management System to Railway.

## Prerequisites

1. A Railway account (sign up at https://railway.app)
2. Git repository with your code
3. GitHub/GitLab account (recommended for automatic deployments)

## Deployment Steps

### Method 1: Deploy from GitHub (Recommended)

1. **Push your code to GitHub:**
   ```bash
   git add .
   git commit -m "Prepare for Railway deployment"
   git push origin main
   ```

2. **Create a new Railway project:**
   - Go to https://railway.app
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

3. **Configure environment variables:**
   - In Railway dashboard, go to your project
   - Click on "Variables" tab
   - Add the following variables:
     - `SECRET_KEY`: A secure random string for Flask sessions
     - `FLASK_ENV`: Set to `production`
     - `USE_GOOGLE_SHEETS`: Set to `true` (recommended for persistent data)
     - `GOOGLE_SHEETS_ID`: Your Google Spreadsheet ID (see Google Sheets Setup)
     - `GOOGLE_CREDENTIALS_JSON`: Your service account credentials as JSON string

4. **Deploy:**
   - Railway will automatically detect the Python app
   - It will use the `Procfile` and `requirements.txt` for deployment
   - The app will be available at the provided Railway URL

### Method 2: Deploy using Railway CLI

1. **Install Railway CLI:**
   ```bash
   npm install -g @railway/cli
   ```

2. **Login to Railway:**
   ```bash
   railway login
   ```

3. **Initialize and deploy:**
   ```bash
   railway init
   railway up
   ```

## Configuration Files

The following files have been configured for Railway deployment:

- **`Procfile`**: Specifies how to run the application using Gunicorn
- **`requirements.txt`**: Lists all Python dependencies including Gunicorn
- **`railway.json`**: Railway-specific configuration
- **`runtime.txt`**: Specifies Python version
- **`.env.example`**: Template for environment variables

## Environment Variables

Set these variables in Railway dashboard:

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | Flask secret key for sessions | Yes |
| `FLASK_ENV` | Set to 'production' for production | Yes |
| `PORT` | Port number (automatically set by Railway) | No |

## Default Login Credentials

- **Admin**: username: `admin`, password: `admin`
- **Class Teachers**: username: `classI`, password: `[from TEACHER_I_PASSWORD env var]` (and so on for classII, classIII, etc.)
- **ECE Teacher**: username: `ece`, password: `ece`

## Important Notes

1. **Data Storage Options**:
   - **Excel Storage (Default)**: Files are ephemeral on Railway and will be lost on redeploys
   - **Google Sheets Storage (Recommended)**: Persistent cloud storage that survives redeploys
   - Set `USE_GOOGLE_SHEETS=true` for production deployments

2. **Google Sheets Setup**: 
   - Follow the [Google Sheets Setup Guide](GOOGLE_SHEETS_SETUP.md) before deployment
   - Ensure `GOOGLE_SHEETS_ID` and `GOOGLE_CREDENTIALS_JSON` are properly configured
   - Test the integration locally before deploying

3. **Security**: 
   - **CRITICAL**: Change ALL passwords in .env file before deploying to production
   - Set strong, unique passwords for ADMIN_PASSWORD and all TEACHER_*_PASSWORD variables
   - Generate a secure SECRET_KEY using: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
   - Keep Google service account credentials secure
   - Never commit `credentials.json` to your repository

4. **HTTPS**: Railway provides HTTPS by default for all deployments.

5. **Custom Domain**: You can configure a custom domain in Railway dashboard.

## Troubleshooting

### Common Issues:

1. **Build Failures**: Check the build logs in Railway dashboard
2. **App Not Starting**: Verify the `Procfile` and ensure all dependencies are in `requirements.txt`
3. **File Permissions**: Ensure the app has write permissions for Excel files

### Logs:

View application logs in Railway dashboard under the "Deployments" tab.

## Support

For Railway-specific issues, check:
- Railway Documentation: https://docs.railway.app
- Railway Discord: https://discord.gg/railway