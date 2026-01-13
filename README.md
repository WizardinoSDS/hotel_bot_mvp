# HotelFlow Telegram Bot (Phase 1 MVP)

A Python-based Telegram bot designed to streamline internal hotel workflows, connecting reception, housekeeping, and management with real-time Google Sheets logging.

## Core Features
- **Role-Based Access Control:** Distinct workflows for Staff and Admins.
- **Housekeeping Module:** Staff can report room cleaning status via `/clean`.
- **Maintenance Tracking:** File maintenance issues instantly via `/issue`.
- **Admin Dashboard:** In-Telegram panel to view daily reports and manage operations.
- **Google Sheets Integration:** All data is logged to a central spreadsheet for reporting.
- **Real-time Notifications:** Admins receive instant alerts when staff submit reports.

## Tech Stack
- **Language:** Python 3.9+
- **API:** `python-telegram-bot` (Async/Await)
- **Data Store:** Google Sheets API (`gspread`)
- **Environment Management:** `python-dotenv`

## Setup Instructions

### 1. Google Cloud Configuration
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project.
3. Enable **Google Sheets API** and **Google Drive API**.
4. Create a **Service Account**, generate a JSON key, and rename it to `credentials.json`.
5. Place `credentials.json` in the project root.
6. Create a new Google Sheet and share it with the `client_email` found in your `credentials.json` (Editor access).

### 2. Telegram Bot Setup
1. Message [@BotFather](https://t.me/botfather) on Telegram to create a new bot.
2. Save the API Token.

### 3. Local Installation
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file from the template:
   ```env
   TELEGRAM_BOT_TOKEN=your_token_here
   GOOGLE_SHEET_ID=your_spreadsheet_id_from_url
   ADMIN_CHAT_ID=your_personal_telegram_id
   ```

### 4. Running the Bot
```bash
python main.py
```

## Deployment Notes
For a production environment (Phase 2), it is recommended to:
- Use a VPS (e.g., DigitalOcean, AWS) or a specialized Python host like PythonAnywhere.
- Run the bot as a systemd service to ensure it restarts automatically.
- Use a robust database (PostgreSQL) for user role management if the staff count exceeds 50+.

## Project Structure
- `main.py`: Bot logic, command handlers, and role management.
- `sheets_service.py`: Google Sheets API wrapper.
- `credentials.json`: (Not included) Service account keys.
- `.env`: (Not included) Sensitive configuration.
