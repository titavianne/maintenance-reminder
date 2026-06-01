"""
处理从 Google 表格读取数据的操作
"""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
from config.settings import GOOGLE_CREDENTIALS_JSON, GOOGLE_SHEET_NAME, COLUMNS, REMINDER_DAYS_BEFORE


class SheetReader:
    """Reads maintenance data from Google Sheets."""
    
    def __init__(self):
        """Initialize Google Sheets connection."""
        # Define Google API scopes needed
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # Authenticate using service account credentials
        creds = Credentials.from_service_account_file(
            GOOGLE_CREDENTIALS_JSON,
            scopes=scopes
        )
        
        # Connect to Google Sheets
        self.client = gspread.authorize(creds)
        self.sheet = self.client.open(GOOGLE_SHEET_NAME).sheet1
        
    def get_all_records(self):
        """
        Get all records from the sheet as a list of dictionaries.
        
        Returns:
            list: All rows from the sheet
        """
        return self.sheet.get_all_records()
    
    def get_maintenance_due_today(self):
        """
        Find assets with maintenance due TODAY.
        
        Returns:
            list: Assets requiring maintenance today
        """
        today = datetime.now().date()
        return self._filter_by_date(today)
    
    def get_maintenance_due_in_7_days(self):
        """
        Find assets with maintenance due in 7 days (H-7 reminder).
        
        Returns:
            list: Assets requiring maintenance in 7 days
        """
        target_date = datetime.now().date() + timedelta(days=REMINDER_DAYS_BEFORE)
        return self._filter_by_date(target_date)
    
    def _filter_by_date(self, target_date):
        """
        Internal method to filter records by a specific date.
        
        Args:
            target_date: Date to filter by
            
        Returns:
            list: Filtered asset records
        """
        all_records = self.get_all_records()
        matching_assets = []
        
        for record in all_records:
            # Skip if status is already completed
            if record.get(COLUMNS['status'], '').lower() == 'completed':
                continue
            
            # Parse the maintenance date
            maintenance_date_str = record.get(COLUMNS['maintenance_date'], '')
            
            if maintenance_date_str:
                try:
                    # Convert string to date object (format: YYYY-MM-DD)
                    maintenance_date = datetime.strptime(
                        maintenance_date_str, 
                        '%Y-%m-%d'
                    ).date()
                    
                    # Check if dates match
                    if maintenance_date == target_date:
                        matching_assets.append(record)
                        
                except ValueError:
                    # Invalid date format - log and skip
                    print(f"⚠️ Invalid date format for {record.get(COLUMNS['asset_name'])}: {maintenance_date_str}")
                    continue
        
        return matching_assets
    
    def update_status(self, asset_id, new_status):
        """
        Update the status of an asset (optional feature).
        
        Args:
            asset_id: The asset ID to update
            new_status: New status value
        """
        # Find the row with matching asset ID
        cell = self.sheet.find(asset_id)
        
        if cell:
            # Update the status column (assuming it's column F)
            status_col = self.sheet.find(COLUMNS['status']).col
            self.sheet.update_cell(cell.row, status_col, new_status)
            print(f"✅ Updated {asset_id} status to {new_status}")