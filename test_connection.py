import os
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials

# Load environment variables
load_dotenv()

# Google Sheets setup
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
CREDS_FILE = os.getenv('GOOGLE_CREDS_FILE')
SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
SHEET_TAB = os.getenv('SHEET_TAB_NAME', 'Sheet1')

def test_read_sheet():
    """Test if we can read the Google Sheet"""
    try:
        # Authenticate
        creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)
        
        # Open the sheet
        sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_TAB)
        
        # Get all data
        data = sheet.get_all_records()
        
        # Print results
        print(f"\n✅ Successfully connected to Google Sheets!")
        print(f"📊 Found {len(data)} customers:\n")
        
        for i, row in enumerate(data, 1):
            name = row.get('name', 'N/A')
            email = row.get('email', 'N/A')
            start_date = row.get('start_date', 'N/A')
            print(f"  {i}. {name} ({email}) - Started: {start_date}")
        
        print("\n🎉 Test passed! Everything is working.\n")
        
    except FileNotFoundError:
        print(f"❌ Error: Could not find credentials file: {CREDS_FILE}")
        print("   Make sure credentials.json is in the project folder.")
    except gspread.exceptions.APIError as e:
        print(f"❌ Google API Error: {e}")
        print("   Check if you shared the sheet with the service account email.")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_read_sheet()