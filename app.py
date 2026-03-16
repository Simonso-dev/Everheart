from flask import Flask, render_template, jsonify, request
from datetime import datetime
from util import split_dataset_per_day, read_ecg_csv, parse_iso, binarySearch, lttb, read_ecg_csv_fast, to_json_friendly, to_column_json
import csv, time

app = Flask(__name__)

@app.route("/uPlot")
def index():
    return render_template("index.html")

@app.route("/d3")
def d3_page():
    return render_template("d3.html")

@app.route("/chart-js")
def chart_js_page():
    return render_template("chart-js.html")

@app.route("/")
def plotly_page():
    return render_template("plotly.html")

'''
@app.route("/ecg-mean")
def get_ecg_mean():
    csv_path = "240507_mean.csv"
    with open(csv_path, 'r') as csv_file:
        ecg_mean_csv = csv.reader(csv_file)
        
        headers = next(ecg_mean_csv)
        
        ecg_mean = []
        for row in ecg_mean_csv:
            ecg_mean.append({headers[i]: row[i] for i in range(len(headers))})
    
    return jsonify(ecg_mean)

@app.route("/ecg-predictions")
def get_ecg_pred():
    csv_path = "240507_pred_mean2.csv"
    ecg_data = read_ecg_csv(csv_path)
    return jsonify(ecg_data)

@app.route("/ecg-predictions-split")
def get_ecg_pred_split():
    csv_path = "240507_pred_mean2.csv"
    return split_dataset_per_day(csv_path)


raw_ecg_csv = read_ecg_csv("240507_pred_50hz.csv")
medium_ecg_csv = read_ecg_csv("240507_pred_20hz.csv")
downsampled_ecg_mean = read_ecg_csv("240507_pred_1hz.csv")
'''

raw_ecg_csv = read_ecg_csv_fast("240507_pred_50hz.csv")
medium_ecg_csv = read_ecg_csv_fast("240507_pred_20hz.csv")
downsampled_ecg_mean = read_ecg_csv_fast("240507_pred_1hz.csv")

@app.route("/ecg-predictions-resample", methods=["GET"])
def get_ecg_pred_resample():
    
    start = request.args.get("start")
    end = request.args.get("end")

    if not start and not end :
        return jsonify(to_column_json(downsampled_ecg_mean))
    
    print("Received start:", start)
    print("Received end:", end)
    print("--------------------------------------")
    
    start_date = datetime.strptime(start, "%Y-%m-%d %H:%M:%S.%f")
    print(f"Start date: {start_date}")
    end_date = datetime.strptime(end, "%Y-%m-%d %H:%M:%S.%f")
    print(f"End date: {end_date}")
    print("--------------------------------------")
    
    span = (end_date - start_date).total_seconds()
    print(f"Span: {span}")

    # If the span is greater than 6 hours use the 1hz downsample,
    # then if the span is between 1 and 6 hours use 10hz downsample.
    # For every span less than an hour use the raw file.
    if span > 6 * 3600:
        ecg_pred = downsampled_ecg_mean
    elif span > 3600:
        ecg_pred = medium_ecg_csv
    else:
        print("Swapped to raw")
        ecg_pred = raw_ecg_csv
    
    start_time = time.time()
    start_index = binarySearch(ecg_pred, start_date)
    print(f"Start index: {start_index}")
    end_time = time.time()
    print(f"Binary search took: {end_time - start_time:.6f} seconds")
    end_index = binarySearch(ecg_pred, end_date)
    print(f"End index: {end_index}")

    if start_index is not None and end_index is not None:
        ecg_data = ecg_pred[start_index:end_index + 1]
    else:
        ecg_data = ecg_pred

    # start_time = time.time()
    '''
    ecg_data = []
    for row in ecg_pred[start_index:]:
        date = datetime.strptime(row["Time"], "%Y-%m-%d %H:%M:%S.%f")
        if date >= start_date and date <= end_date:
            # print(row)
            ecg_data.append(row)
    '''
    
    # end_time = time.time()
    # print(f"Linear search took: {end_time - start_time:.6f} seconds")
    
    print(f"Data lenght: {len(ecg_data)}")

    # ecg_data = lttb(ecg_data, 10000)

    # print(f"Data lenght after lttb: {len(ecg_data)}")
    

    return jsonify(to_column_json(ecg_data))