import gspread
import google.auth
from datetime import datetime, timedelta


# Authenticate with Google Sheets using Cloud Run's built-in Service Account
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def get_sheets_client():
    credentials, project = google.auth.default(scopes=SCOPES)
    return gspread.authorize(credentials)

def append(metrics):
    gc = get_sheets_client()
    
    # Replace with your actual Google Sheet ID (from the sheet URL)
    SHEET_ID = "10_pz7I2u27s-eTKsatJDAbuZ6QnEpJTF9ZPAq2vk_EA"
    WORKSHEET_NAME = "Podbean"
    sheet = gc.open_by_key(SHEET_ID).worksheet(WORKSHEET_NAME)  # or specify worksheet name

    # 3. Append data to the Google Sheet
    date = datetime.now()
    first_of_this_month = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month = (first_of_this_month - timedelta(days=1)).strftime("%B %Y")

    
    sheet.append_row([
        last_month,
        metrics["downloads_7_days"],
        metrics["downloads_30_days"],
        metrics["downloads_all_time"],
    ])