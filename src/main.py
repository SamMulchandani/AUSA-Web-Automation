import os
import io
import pandas as pd
from src.sheets_sync import append
import json
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)


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

        json_data = df.to_dict(orient='records')
        # print(json.dumps(json_data,indent=2))
        
        from datetime import datetime, timedelta

# 1. Establish the 1st of the current month as the anchor point
        today = datetime.now()
        first_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # 2. Define time windows looking backward from the 1st of the month
        seven_days_prior = first_of_month - timedelta(days=7)
        thirty_days_prior = first_of_month - timedelta(days=30)

        # 3. Initialize counters
        downloads_all_time = 0
        downloads_past_30_days = 0
        downloads_past_7_days = 0

        # 4. Loop through the parsed JSON rows
        for row in json_data:
            # Get the date string from the 'Release Date' column
            date_str = str(row.get('Release Date', '')).strip()

            if not date_str:
                continue

            try:
                # Parse 'YYYY-MM-DD' (e.g., '2026-08-26')
                release_date = datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                # Skip rows with missing or invalid date strings
                continue

            # Safely coerce Downloads to a number; treat missing/blank as 0
            raw_downloads = row.get("Downloads", 0)
            if isinstance(raw_downloads, str):
                raw_downloads = raw_downloads.replace(",", "").strip()
            try:
                downloads = int(float(raw_downloads)) if raw_downloads not in ("", None) else 0
            except (ValueError, TypeError):
                downloads = 0

            # Increment All-Time total
            downloads_all_time += downloads

            # Count if date falls within the 30-day window before the 1st
            if thirty_days_prior <= release_date < first_of_month:
                downloads_past_30_days += downloads

            # Count if date falls within the 7-day window before the 1st
            if seven_days_prior <= release_date < first_of_month:
                downloads_past_7_days += downloads

        # Summary metrics dictionary ready for your Google Sheet pipeline
        summary_metrics = {
            "downloads_all_time": downloads_all_time,
            "downloads_past_30_days": downloads_past_30_days,
            "downloads_past_7_days": downloads_past_7_days
        }

        # sync to google sheets
        append(summary_metrics)

        return jsonify({
            "message": "Successfully converted CSV to JSON object",
            "row_count": len(json_data),
            "data": json_data
        }), 200


    except Exception as e:
        return jsonify({"error": str(e)}), 500


        

    # except Exception as e:
    #     return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))