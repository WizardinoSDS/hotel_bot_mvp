import gspread
from google.oauth2.service_account import Credentials
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class SheetsService:
    def __init__(self):
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        # Ensure credentials.json is in the same directory
        creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
        self.client = gspread.authorize(creds)
        self.sheet_id = os.getenv("GOOGLE_SHEET_ID")
        
        try:
            self.spreadsheet = self.client.open_by_key(self.sheet_id)
        except Exception as e:
            print(f"Error opening spreadsheet: {e}")
            self.spreadsheet = None

    def _get_or_create_worksheet(self, title, headers):
        try:
            return self.spreadsheet.worksheet(title)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = self.spreadsheet.add_worksheet(title=title, rows="100", cols=len(headers))
            worksheet.append_row(headers)
            return worksheet

    def log_cleaning(self, user_name, room_number, status):
        worksheet = self._get_or_create_worksheet("Cleaning", ["Timestamp", "Staff", "Room", "Status"])
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        worksheet.append_row([timestamp, user_name, room_number, status])

    def log_maintenance(self, user_name, description, status="Pending"):
        worksheet = self._get_or_create_worksheet("Maintenance", ["Timestamp", "Staff", "Issue", "Status"])
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        worksheet.append_row([timestamp, user_name, description, status])

    def log_task(self, user_name, task_name, status="Completed"):
        worksheet = self._get_or_create_worksheet("Daily Tasks", ["Timestamp", "Staff", "Task", "Status"])
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        worksheet.append_row([timestamp, user_name, task_name, status])

    def get_today_reports(self):
        # Placeholder for fetching data to show to Admin
        worksheet = self._get_or_create_worksheet("Cleaning", ["Timestamp", "Staff", "Room", "Status"])
        records = worksheet.get_all_records()
        today = datetime.now().strftime("%Y-%m-%d")
        return [r for r in records if r['Timestamp'].startswith(today)]
