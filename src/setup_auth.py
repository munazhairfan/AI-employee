"""
Gmail OAuth Setup Script

This script helps you authenticate with Gmail API and create token.json.
Run this ONCE to set up authentication, then use gmail_watcher.py.
"""

import os
import sys
from pathlib import Path


def check_prerequisites():
    """Check if required packages are installed."""
    missing = []
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        missing.append('google-auth-oauthlib')
    
    try:
        from google.auth.transport.requests import Request
    except ImportError:
        missing.append('google-auth')
    
    try:
        from googleapiclient.discovery import build
    except ImportError:
        missing.append('google-api-python-client')
    
    if missing:
        print("Missing required packages.")
        print(f"Install with: pip install {' '.join(missing)}")
        return False
    return True


def check_credentials_file():
    """Check if credentials.json exists."""
    cred_path = Path('credentials.json')
    if not cred_path.exists():
        print("\n[ERROR] credentials.json not found!")
        print("\nYou need to download it from Google Cloud Console:")
        print("1. Go to: https://console.cloud.google.com/")
        print("2. Create a new project (or select existing)")
        print("3. Enable 'Gmail API' for the project")
        print("4. Go to 'Credentials' > 'Create Credentials' > 'OAuth client ID'")
        print("5. Application type: 'Desktop app'")
        print("6. Download the JSON file and save it as 'credentials.json' in this folder")
        return False
    print("[OK] credentials.json found")
    return True


def run_oauth_flow():
    """Run OAuth flow to get Gmail access token."""
    from google_auth_oauthlib.flow import InstalledAppFlow
    
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    
    print("\n" + "=" * 60)
    print("Starting Gmail OAuth Setup")
    print("=" * 60)
    
    print("\nThis will open a browser window for you to sign in to Google.")
    print("You'll grant permission to read your Gmail messages.")
    print("\nPress Enter to continue...")
    input()
    
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json',
            SCOPES
        )
        
        # Run local server flow
        creds = flow.run_local_server(port=0, open_browser=True)
        
        # Save token
        token_path = Path('token.json')
        with open(token_path, 'w') as f:
            f.write(creds.to_json())
        
        print("\n" + "=" * 60)
        print("[SUCCESS] Authentication complete!")
        print("=" * 60)
        print(f"\nToken saved to: {token_path.absolute()}")
        print("\nYou can now run: python gmail_watcher.py")
        print("\nNote: token.json contains your access credentials. Keep it secure!")
        
        # Test the connection
        print("\nTesting Gmail connection...")
        from googleapiclient.discovery import build
        service = build('gmail', 'v1', credentials=creds)
        
        # Get profile
        profile = service.users().getProfile(userId='me').execute()
        print(f"[OK] Connected to: {profile.get('emailAddress', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Authentication failed: {e}")
        print("\nTroubleshooting:")
        print("- Make sure credentials.json is valid")
        print("- Check that Gmail API is enabled in Google Cloud Console")
        print("- Try deleting token.json and running again")
        return False


def main():
    print("=" * 60)
    print("GMAIL WATCHER - AUTHENTICATION SETUP")
    print("=" * 60)
    
    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)
    
    # Check credentials file
    if not check_credentials_file():
        sys.exit(1)
    
    # Run OAuth flow
    success = run_oauth_flow()
    
    if success:
        print("\n" + "=" * 60)
        print("SETUP COMPLETE")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Run: python gmail_watcher.py")
        print("   (Watches for new important emails every 60 seconds)")
        print("\n2. Check AI_Employee_Vault/Needs_Action/ for email files")
        print("\n3. The orchestrator will process them automatically")
    else:
        print("\nSetup failed. Please fix the errors and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
