import gspread
from google.oauth2.service_account import Credentials
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class SheetsService:
    def __init__(self):
        # Setup sheets connection
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        try:
            creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
            self.client = gspread.authorize(creds)
            self.sheet_id = os.getenv("GOOGLE_SHEET_ID")
            self.doc = self.client.open_by_key(self.sheet_id)
        except Exception as e:
            print(f"Auth failed: {e}")
            self.doc = None

    def _get_sheet(self, name, cols):
        try:
            return self.doc.worksheet(name)
        except:
            # Create if missing
            sh = self.doc.add_worksheet(title=name, rows="500", cols=str(len(cols)))
            sh.append_row(cols)
            return sh

    def log_cleaning(self, worker, room, status):
        sh = self._get_sheet("Cleaning", ["Time", "Staff", "Room", "Status"])
        sh.append_row([datetime.now().strftime("%Y-%m-%d %H:%M"), worker, room, status])

    def log_maintenance(self, worker, issue):
        sh = self._get_sheet("Maintenance", ["Time", "Staff", "Issue", "Status"])
        sh.append_row([datetime.now().strftime("%Y-%m-%d %H:%M"), worker, issue, "Pending"])

    def log_task(self, worker, task):
        sh = self._get_sheet("DailyTasks", ["Time", "Staff", "Task"])
        sh.append_row([datetime.now().strftime("%Y-%m-%d %H:%M"), worker, task])

            def get_today_reports(self):

                try:

                    sh = self.doc.worksheet("Cleaning")

                    all_rows = sh.get_all_values() # Get everything as raw list of lists

                    if not all_rows: return []

                    

                    headers = all_rows[0]

                    rows = all_rows[1:]

                    today = datetime.now().strftime("%Y-%m-%d")

                    

                    results = []

                    for row in rows:

                        # Check if 'today' exists in ANY cell of this row (usually the first one)

                        if any(today in str(cell) for cell in row):

                            # Convert back to dict for the bot logic

                            results.append(dict(zip(headers, row)))

                    

                    print(f"Found {len(results)} matches for {today}")

                    return results

                except Exception as e:

                    print(f"Error: {e}")

                    return []

        

    