from flask import Flask, render_template, jsonify, request
from datetime import datetime
from util import binarySearch, lttb3, count_arythmia_episodes, read_multiple_files
import time

app = Flask(__name__)

'''

    Initialize global variables

'''
parquet_paths = ("data/parquet/240507_1hz.parquet", "data/parquet/240507_20hz.parquet", "data/parquet/240507_100hz.parquet")

start_time = time.time()
parquet_files = read_multiple_files(parquet_paths)
ecg_1hz = parquet_files.get()
ecg_20hz = parquet_files.get()
ecg_100hz = parquet_files.get()
end_time = time.time()
print(f"Loading all datasets took: {end_time - start_time:.6f} seconds")

'''

    Routes

'''
@app.route("/")
def index():
    return render_template("plotly.html")

@app.route("/ecg-stats", methods=["GET"])
def get_ecg_stats():
    ecg_stats = count_arythmia_episodes(ecg_100hz)
    return ecg_stats

@app.route("/ecg-predictions-resample", methods=["GET"])
def get_ecg_pred_resample():
    
    start = request.args.get("start")
    end = request.args.get("end")

    if not start or not end:
        sampeld_start = lttb3(ecg_1hz, 5000)
        return sampeld_start.to_json(orient="records")
    
    print("-"*30)
    print("Received start:", start)
    print("Received end:", end)
    print("-"*30)
    
    start_date = datetime.strptime(start, "%Y-%m-%d %H:%M:%S.%f")
    print(f"Start date: {start_date}")
    end_date = datetime.strptime(end, "%Y-%m-%d %H:%M:%S.%f")
    print(f"End date: {end_date}")
    print("-"*30)
    
    span = (end_date - start_date).total_seconds()
    print(f"Span: {span}")

    # If the span is greater than 6 hours use the 1hz downsample,
    # then if the span is between 1 and 6 hours use 10hz downsample.
    # For every span less than an hour use the raw file.
    if span > 6 * 3600:
        print("Swapped to 1hz")
        ecg_pred = ecg_1hz
    elif span > 300:
        print("Swapped to 20hz")
        ecg_pred = ecg_20hz
    else:
        print("Swapped to 100hz")
        ecg_pred = ecg_100hz
    
    start_time = time.time()
    start_index = binarySearch(ecg_pred, start_date)
    print(f"Start index: {start_index}")
    end_time = time.time()
    print(f"Binary search took: {end_time - start_time:.6f} seconds")
    end_index = binarySearch(ecg_pred, end_date)
    print(f"End index: {end_index}")

    if start_index is not None and end_index is not None:
        ecg_data = ecg_pred.iloc[start_index:end_index + 1]
    else:
        ecg_data = ecg_pred.copy()

    print(f"Data lenght: {len(ecg_data)}")
    print("-"*30)

    if len(ecg_data) > 5000:
        sampeld = lttb3(ecg_data, 5000)
        return sampeld.to_json(orient="records")
    
    return ecg_data.to_json(orient="records")