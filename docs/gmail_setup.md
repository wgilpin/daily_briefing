# Gmail API Setup Guide

This guide walks you through setting up Google Cloud Project credentials to allow the Newsletter Aggregator to access your Gmail account.

## Overview

The Newsletter Aggregator uses OAuth 2.0 to securely access your Gmail account without storing your password. You'll need to:

1. Create a Google Cloud Project
2. Enable the Gmail API
3. Configure OAuth consent screen
4. Create OAuth 2.0 credentials
5. Download credentials file

## Prerequisites

- A Google account
- Access to [Google Cloud Console](https://console.cloud.google.com/)

## Step-by-Step Instructions

### Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click the project dropdown at the top of the page
3. Click **"New Project"**
4. Enter a project name (e.g., "Newsletter Aggregator")
5. Click **"Create"**
6. Wait for the project to be created, then select it from the dropdown

### Step 2: Enable Gmail API

1. In the Google Cloud Console, navigate to **"APIs & Services"** > **"Library"**
2. Search for **"Gmail API"**
3. Click on **"Gmail API"** from the results
4. Click **"Enable"**
5. Wait for the API to be enabled (this may take a minute)

### Step 3: Configure OAuth Consent Screen

1. Navigate to **"APIs & Services"** > **"OAuth consent screen"**
2. Select **"External"** user type (unless you have a Google Workspace account)
3. Click **"Create"**
4. Fill in the required information:
   - **App name**: Newsletter Aggregator (or your preferred name)
   - **User support email**: Your email address
   - **Developer contact information**: Your email address
5. Click **"Save and Continue"**
6. On the **"Scopes"** page:
   - Click **"Add or Remove Scopes"**
   - Search for and select: `https://www.googleapis.com/auth/gmail.readonly`
   - Click **"Update"**
   - Click **"Save and Continue"**
7. On the **"Test users"** page (if shown):
   - Add your Google account email as a test user
   - Click **"Save and Continue"**
8. Review and click **"Back to Dashboard"**

**Note**: For personal use, the app will remain in "Testing" mode. If you want to publish it for wider use, you'll need to go through Google's verification process.

### Step 4: Create OAuth Client ID

**create a Client ID.** This is the OAuth 2.0 credential that allows the app to authenticate with Gmail.

1. Navigate to **"APIs & Services"** > **"Credentials"**
2. Click **"+ CREATE CREDENTIALS"** button at the top of the page
3. From the dropdown menu, select **"OAuth client ID"**
4. You may be prompted to configure the OAuth consent screen first (if you haven't completed Step 3). If so, complete that first.
5. In the **"Create OAuth client ID"** form:
   - **Application type**: Select **"Desktop app"**
   - **Name**: Enter "Newsletter Aggregator" (or your preferred name)
6. Click **"Create"**
7. A popup dialog will appear showing:
   - **Your Client ID** (a long string ending in `.apps.googleusercontent.com`)
   - **Your Client Secret** (a shorter string)
   - **Important**: You can only view the Client Secret once in this dialog. You don't need to copy it manually - you'll download the full credentials file in the next step.
8. Click **"OK"** to close the dialog

### Step 5: Download Credentials File

1. In the **"Credentials"** page, find your newly created OAuth 2.0 Client ID
2. Click the **download icon** (⬇️) on the right side of the credentials entry
3. This downloads a file named `credentials.json`

### Step 6: Place Credentials in Project

1. Create the `config/` directory in your project root (if it doesn't exist):
   ```bash
   mkdir config
   ```

2. Move the downloaded `credentials.json` file to the `config/` directory:
   ```bash
   # On Windows (PowerShell)
   Move-Item -Path ~/Downloads/credentials.json -Destination config/credentials.json
   
   # On Windows (Git Bash)
   mv ~/Downloads/credentials.json config/credentials.json
   
   # On Linux/Mac
   mv ~/Downloads/credentials.json config/credentials.json
   ```

3. Verify the file is in the correct location:
   ```bash
   ls config/credentials.json
   ```

### Step 7: Verify Setup

The credentials file should look like this:

```json
{
  "installed": {
    "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
    "project_id": "your-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "YOUR_CLIENT_SECRET",
    "redirect_uris": ["http://localhost"]
  }
}
```

## First-Time Authentication

When you run the Newsletter Aggregator for the first time:

1. The application will detect that no tokens exist
2. It will open your default web browser
3. You'll be prompted to sign in with your Google account
4. You'll see a consent screen asking for permission to:
   - View your email messages and settings
5. Click **"Allow"** or **"Continue"**
6. The application will receive the authorization code and exchange it for tokens
7. Tokens will be saved to `data/tokens.json` for future use

## Security Notes

- **Never commit `credentials.json` to version control** - it's already in `.gitignore`
- **Never commit `data/tokens.json` to version control** - it's already in `.gitignore`
- The credentials file contains your OAuth client secret - keep it secure
- The tokens file contains your access and refresh tokens - keep it secure
- If you suspect your credentials or tokens have been compromised:
  1. Go to Google Cloud Console > Credentials
  2. Delete the compromised OAuth client ID
  3. Create a new one and download new credentials

## Troubleshooting

### "Credentials file not found" Error

- Verify `config/credentials.json` exists
- Check the file path is correct
- Ensure the file name is exactly `credentials.json` (not `credentials (1).json`)

### "Access blocked" Error

- Ensure you added your email as a test user in OAuth consent screen
- Check that the app is in "Testing" mode (for personal use)
- Verify the Gmail API is enabled in your project

### "Invalid client" Error

- Verify the credentials.json file is valid JSON
- Ensure you downloaded the correct credentials file
- Check that the OAuth client ID is still active in Google Cloud Console

### Token Refresh Issues

- Delete `data/tokens.json` and re-authenticate
- Check that your Google account is still active
- Verify the OAuth client hasn't been deleted in Google Cloud Console

## Additional Resources

- [Google Cloud Console](https://console.cloud.google.com/)
- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [OAuth 2.0 for Desktop Apps](https://developers.google.com/identity/protocols/oauth2/native-app)
- [Google API Python Client Documentation](https://github.com/googleapis/google-api-python-client)

## Quick Reference

**Required Scopes:**
- `https://www.googleapis.com/auth/gmail.readonly` - Read-only access to Gmail

**File Locations:**
- Credentials: `config/credentials.json`
- Tokens: `data/tokens.json`

**Important URLs:**
- Google Cloud Console: https://console.cloud.google.com/
- API Library: https://console.cloud.google.com/apis/library
- Credentials: https://console.cloud.google.com/apis/credentials
- OAuth Consent Screen: https://console.cloud.google.com/apis/credentials/consent
