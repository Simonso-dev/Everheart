import csv
from datetime import datetime
import numpy as np
import pandas as pd

csv_path = "240507_pred_mean2.csv"

def read_large_ecg_pred(file_path, chunk_size):
    for chunk in pd.read_csv(file_path, chunksize=chunk_size, skiprows=7, parse_dates=True, skipinitialspace=True):
        yield chunk

def read_ecg_csv(csv_path: str):
    with open(csv_path, 'r') as csv_file:
        ecg_csv = csv.reader(csv_file)
        
        headers = next(ecg_csv)
        
        ecg_data = []
        for row in ecg_csv:
            ecg_data.append({headers[i]: row[i] for i in range(len(headers))})
    
    return ecg_data

def read_ecg_csv_fast(csv_path):
    return np.genfromtxt(csv_path, delimiter=",", names=True, dtype=None)

def split_dataset_per_day(csv_path: str):
    with open(csv_path, 'r') as csv_file:
        ecg_csv = csv.reader(csv_file)

        headers = next(ecg_csv)

        previous_date = datetime.min
        ecg_data = {}
        for row in ecg_csv:
            date = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S.%f")
            current_date = date
            if current_date.day != previous_date.day:
                formated_date = current_date.strftime("%Y-%m-%d")
                ecg_data.setdefault(formated_date, [])
                previous_date = current_date

            ecg_data[formated_date].append(dict(zip(headers, row)))

        return ecg_data

def parse_iso(timestamp): 
    '''
        Reformats a datetime ISO string to a python datetime string with the format "%Y-%m-%d %H:%M:%S.%f".
    '''
    date = datetime.fromisoformat(timestamp)
    return date.strftime("%Y-%m-%d %H:%M:%S.%f")

def to_json_friendly(recarray):
    return [
        {name: row[name].item() for name in recarray.dtype.names}
        for row in recarray
    ]

def to_column_json(recarray):
    return {
        name: recarray[name].tolist()
        for name in recarray.dtype.names
    }

def lttb(data, threshold: int):
    '''
        Largest Triangle Three Buckets (LTTB)
        
        The LTTB algorithm as described by Sveinn Steinarsson.
        Algorithm 4.2 Largest-Triangle-Three-Buckets
        Require: data . The original data
        Require: threshold . Number of data points to be returned
        1: Split the data into equal number of buckets as the threshold but have the first
           bucket only containing the first data point and the last bucket containing only
           the last data point
        2: Select the point in the first bucket
        3: for each bucket except the first and last do
        4: Rank every point in the bucket by calculating the area of a triangle it forms
           with the selected point in the last bucket and the average point in the next bucket
        5: Select the point with the highest rank within the bucket
        6: end for
        7: Select the point in the last bucket . There is only one
    '''
    data_length = len(data)
    if threshold >= data_length or threshold == 0:
        return data
    
    sampled = []
    bucket_size = (data_length - 2) / (threshold - 2)

    a = 0

    sampled.append(data[0])

    for i in range(1, threshold - 1):
        # The current bucket
        start = int((i - 1) * bucket_size) + 1
        end = int(i * bucket_size) + 1

        if end >= data_length:
            end = data_length - 1
        
        # Calculate the next bucket average.
        next_start = int(i * bucket_size) + 1
        next_end = int((i + 1) * bucket_size) + 1
        
        if next_end > data_length:
            next_end = data_length

        count = next_end - next_start
        avg_x = 0.0
        avg_y = 0.0
        for j in range(next_start, next_end):
            x, y = datetime.strptime(data[j]["Time"], "%Y-%m-%d %H:%M:%S.%f").timestamp(), float(data[j]["240507_complete:ECG"])
            avg_x += x
            avg_y += y
        
        avg_x /= count
        avg_y /= count

        # Point A
        ax, ay = datetime.strptime(data[a]["Time"], "%Y-%m-%d %H:%M:%S.%f").timestamp(), float(data[a]["240507_complete:ECG"])

        # Find the max area point in the current bucket.
        max_area = -1
        max_point = None
        max_index = None

        for j in range(start, end):
            bx, by = datetime.strptime(data[j]["Time"], "%Y-%m-%d %H:%M:%S.%f").timestamp(), float(data[j]["240507_complete:ECG"])

            area = abs(
                (ax - avg_x) * (by - ay) -
                (ax - bx) * (avg_y - ay)
            )

            if area > max_area:
                max_area = area
                max_point = data[j]
                max_index = j
        
        sampled.append(max_point)
        a = max_index
    
    sampled.append(data[-1])
    return sampled

def binarySearch(sorted_list, key):
    first = 0
    last = (len(sorted_list) - 1)

    while first <= last:
        mid = (first + last) // 2

        mid_date = datetime.strptime(sorted_list[mid][0], "%Y-%m-%d %H:%M:%S.%f")
        
        if mid_date < key:
            first = mid + 1
        else:
            last = mid - 1

    # print("Key not found, returning None")
    return first

if __name__ == "__main__":
    # Generate example data
    N = 5000  # number of points

    # X values: evenly spaced timestamps
    x = np.linspace(0, 100, N)

    # Y values: noisy signal with multiple frequencies
    y = (
        np.sin(x * 0.2) * 10 +
        np.sin(x * 1.5) * 2 +
        np.random.normal(scale=1.0, size=N)
    )

    # Combine into a 2D array if needed
    data = np.column_stack((x, y))

    ecg_data = read_ecg_csv(csv_path)
    # print(ecg_data)
    ecg_sample = lttb(ecg_data, 10)
    print(ecg_sample)