import os
import pandas as pd
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify

# Import the append logic directly from your sync file
from src.sheets_sync import append

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/api/upload-csv', methods=['POST'])
def upload_csv():
    try:
        # Get uploaded files from the multipart form request
        monthly_file = request.files.get('monthly')
        seven_day_file = request.files.get('sevenDay')
        all_time_file = request.files.get('allTime')

        if not all([monthly_file, seven_day_file, all_time_file]):
            return jsonify({"error": "Missing one or more required CSV files."}), 400

        today = datetime.now()

        # ---------------------------------------------------------
        # 1. Process Monthly Report
        # Output: The sum of all downloads in the file.
        # ---------------------------------------------------------
        df_monthly = pd.read_csv(monthly_file)
        monthly_total = 0
        if 'Downloads' in df_monthly.columns:
            monthly_total = pd.to_numeric(
                df_monthly['Downloads'].astype(str).str.replace(',', '', regex=False), errors='coerce'
            ).sum()

        # ---------------------------------------------------------
        # 2. Process 7-Day Report
        # Output: The average of 7-day downloads from podcasts posted in the PREVIOUS month.
        # ---------------------------------------------------------
        df_7day = pd.read_csv(seven_day_file)
        seven_day_avg = 0
        if 'Release Date' in df_7day.columns and 'Downloads' in df_7day.columns:
            # Parse dates and numeric downloads
            df_7day['Release Date'] = pd.to_datetime(df_7day['Release Date'], errors='coerce')
            df_7day['Downloads'] = pd.to_numeric(
                df_7day['Downloads'].astype(str).str.replace(',', '', regex=False), errors='coerce'
            )

            # Calculate previous month boundaries
            first_of_this_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            last_month_end = first_of_this_month - timedelta(days=1)
            first_of_last_month = last_month_end.replace(day=1)

            # Filter rows for releases in the previous month and calculate the average
            last_month_episodes = df_7day[
                (df_7day['Release Date'] >= first_of_last_month) & 
                (df_7day['Release Date'] < first_of_this_month)
            ]

            if not last_month_episodes.empty:
                seven_day_avg = last_month_episodes['Downloads'].mean()

        # ---------------------------------------------------------
        # 3. Process All-Time Report
        # Output: Downloads from THIS YEAR (e.g., 2026).
        # ---------------------------------------------------------
        df_all_time = pd.read_csv(all_time_file)
        all_time_total = 0
        if 'Downloads' in df_all_time.columns:
            all_time_total = pd.to_numeric(
                df_all_time['Downloads'].astype(str).str.replace(',', '', regex=False), errors='coerce'
            ).sum()


        # ---------------------------------------------------------
        # Compile Metrics and Push to Sheets
        # ---------------------------------------------------------
        summary_metrics = {
            "downloads_7_days": int(seven_day_avg) if not pd.isna(seven_day_avg) else 0,
            "downloads_30_days": int(monthly_total) if not pd.isna(monthly_total) else 0,
            "downloads_all_time": int(all_time_total) if not pd.isna(all_time_total) else 0
        }

        # Sync to Google Sheets
        append(summary_metrics)

        return jsonify({
            "message": "Successfully processed files and synced to Google Sheets",
            "data": summary_metrics
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))