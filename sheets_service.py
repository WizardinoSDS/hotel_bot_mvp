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

                all_rows = sh.get_all_records()

                today = datetime.now().strftime("%Y-%m-%d")

                

                # Debug log to server console

                print(f"Checking {len(all_rows)} rows for date {today}")

                

                results = []

                for r in all_rows:

                    # Support both 'Time' and 'Timestamp' keys

                    row_date = r.get('Time') or r.get('Timestamp') or ""

                    if str(row_date).startswith(today):

                        results.append(r)

                return results

            except Exception as e:

                print(f"Error fetching reports: {e}")

                return []

    