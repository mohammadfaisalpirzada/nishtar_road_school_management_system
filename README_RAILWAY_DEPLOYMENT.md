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
- **Class Teachers**: username: `class1`, password: `class1` (and so on for class2, class3, etc.)
- **ECE Teacher**: username: `ece`, password: `ece`

## Important Notes

1. **File Storage**: The current implementation stores data in Excel files. On Railway, the filesystem is ephemeral, meaning files may be lost on redeploys. Consider migrating to a database for production use.

2. **Security**: Change default passwords before deploying to production.

3. **HTTPS**: Railway provides HTTPS by default for all deployments.

4. **Custom Domain**: You can configure a custom domain in Railway dashboard.

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