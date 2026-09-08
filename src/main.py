import os
import io
import pandas as pd
import gspread
import google.auth
from flask import Flask, render_template, request, jsonify

app = Flask(__name__, template_folder='.')

# Authenticate with Google Sheets using Cloud Run's built-in Service Account
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def get_sheets_client():
    credentials, project = google.auth.default(scopes=SCOPES)
    return gspread.authorize(credentials)

@app.route('/', methods=['GET'])
def index():
    # Serves the index.html template from the same directory
    return render_template('index.html')

@app.route('/api/upload-csv', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    
    try:
        # 1. Parse CSV into DataFrame
        df = pd.read_csv(file)
        
        # Replace NaN values with empty strings for JSON compatibility
        df = df.fillna('')

        # 2. Connect to Google Sheets
        gc = get_sheets_client()
        
        # Replace with your actual Google Sheet ID (from the sheet URL)
        SHEET_ID = "YOUR_GOOGLE_SHEET_ID_HERE"
        sheet = gc.open_by_key(SHEET_ID).sheet1  # or specify worksheet name

        # 3. Append data to the Google Sheet
        values = df.values.tolist()
        sheet.append_rows(values, value_input_option='USER_ENTERED')

        return jsonify({"message": "Successfully appended data to Google Sheet"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))