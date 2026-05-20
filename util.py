import csv, time
from datetime import datetime
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import threading, queue
import lttb
from memory_profiler import profile


def read_large_ecg_pred(file_path: str, chunk_size: int):
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

def read_ecg_csv_fast(csv_path: str):
    return np.genfromtxt(csv_path, delimiter=",", names=True, dtype=None)

def read_csv_df(csv_path: str):
    return pd.read_csv(csv_path, skipinitialspace=True)

def write_df_parquet(df: pd.DataFrame, file_path: str):
    pd.DataFrame.to_parquet(path=file_path, self=df, index=False)

def read_parquet(parquet_path: str):
    return pd.read_parquet(parquet_path)


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

def count_arythmia_episodes(df: pd.DataFrame):
    """
        Counts arythmia episodes per type and returns a dictionary: { "Type": count, ... }
    """
    df = df.copy()
    
    changes = df["Prediction"].ne(df["Prediction"].shift())
    df["Episode_ID"] = changes.cumsum()

    summary = df.groupby("Prediction").size()
    ecg_stats = summary.to_dict()
    
    return ecg_stats

def lttb3(data: pd.DataFrame, threshold: int):
    data = data.copy()

    if len(data) <= threshold:
        return data

    data["Time"] = pd.to_datetime(data["Time"]).map(pd.Timestamp.timestamp)
    pred = data["Prediction"]
    data = data.drop("Prediction", axis=1)

    sampeld = lttb.downsample(data.to_numpy(), threshold)

    sampeld_df = pd.DataFrame(sampeld, columns=["Time", "240507_complete:ECG"])
    sampeld_df["Time"] = pd.to_datetime(sampeld_df["Time"], unit="s").dt.strftime("%Y-%m-%d %H:%M:%S.%f")

    data["Time"] = pd.to_datetime(data["Time"], unit="s").dt.strftime("%Y-%m-%d %H:%M:%S.%f")
    data["Prediction"] = pred

    sampeld_df["Prediction"] = sampeld_df["Time"].map(data.set_index("Time")["Prediction"])

    return sampeld_df

def binarySearch(sorted_list: pd.DataFrame, key):
    first = 0
    last = (len(sorted_list) - 1)

    while first <= last:
        mid = (first + last) // 2
        
        mid_date = datetime.strptime(sorted_list.iloc[mid]["Time"], "%Y-%m-%d %H:%M:%S.%f")

        if mid_date < key:
            first = mid + 1
        else:
            last = mid - 1

    # print("Key not found, returning None")
    return first

# @profile
def test_get_ecg_pred_resample(start=None, end=None, datasets=None):
    '''
        This function is for benchmarking purposes only.
    '''

    ecg_csv_1hz = datasets[0]
    ecg_csv_20hz = datasets[1]
    ecg_csv_100hz = datasets[2]

    if not start or not end:
        sampeld_start = lttb3(ecg_csv_1hz, 5000)
        return sampeld_start.to_json(orient="records")
    '''
    print("--------------------------------------")
    print("Received start:", start)
    print("Received end:", end)
    print("--------------------------------------")
    '''
    
    start_date = datetime.strptime(start, "%Y-%m-%d %H:%M:%S.%f")
    # print(f"Start date: {start_date}")
    end_date = datetime.strptime(end, "%Y-%m-%d %H:%M:%S.%f")
    # print(f"End date: {end_date}")
    # print("--------------------------------------")
    
    span = (end_date - start_date).total_seconds()
    # print(f"Span: {span}")

    # If the span is greater than 6 hours use the 1hz downsample,
    # then if the span is between 1 and 6 hours use 10hz downsample.
    # For every span less than an hour use the raw file.
    if span > 6 * 3600:
        # print("Swapped to 1hz")
        ecg_pred = ecg_csv_1hz
    elif span > 300:
        # print("Swapped to 20hz")
        ecg_pred = ecg_csv_20hz
    else:
        # print("Swapped to 50hz")
        ecg_pred = ecg_csv_100hz
    
    start_time = time.time()
    start_index = binarySearch(ecg_pred, start_date)
    # print(f"Start index: {start_index}")
    end_time = time.time()
    # print(f"Binary search took: {end_time - start_time:.6f} seconds")
    end_index = binarySearch(ecg_pred, end_date)
    # print(f"End index: {end_index}")

    if start_index is not None and end_index is not None:
        ecg_data = ecg_pred.iloc[start_index:end_index + 1]
    else:
        ecg_data = ecg_pred.copy()

    # print(f"Data lenght: {len(ecg_data)}")
    # print("--------------------------------------")

    # ecg_data = lttb(to_json_friendly(ecg_data), 10000)
    # print(f"Data lenght after lttb: {len(ecg_data)}")

    if len(ecg_data) > 5000:
        sampeld = lttb3(ecg_data, 5000)
        return sampeld.to_json(orient="records")
    
    return ecg_data.to_json(orient="records")

def get_ecg_resample(start: str, end: str, parquet_files: tuple):
    ecg_1hz = parquet_files[0]
    ecg_20hz = parquet_files[1]
    ecg_100hz = parquet_files[2]
    
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
        print("Swapped to 50hz")
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

def stream_parquet(parquet_path: str , start, end):
    parquet_file = pq.ParquetFile(parquet_path)
    start_index = 0
    end_index = 0
    sampled = pd.DataFrame

    for batch in parquet_file.iter_batches():
        df = batch.to_pandas()

def read_multiple_files(parquet_paths: tuple):
    '''
        This function reads multiple parquet files and puts them in a queue using threads.

        It works by defining a temporary worker function that puts the result of a thread in queue.
        The queue is then returned when all threads are done.
    '''
    threads = []
    parquet_files = queue.Queue()

    def read_parquet_worker(parquet_path):
        df = read_parquet(parquet_path)
        parquet_files.put(df)

    for parquet_path in parquet_paths:
        thread = threading.Thread(target=read_parquet_worker, args=(parquet_path,))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    return parquet_files

if __name__ == "__main__":
    # print(ecg_data)
    # ecg_sample = lttb2(ecg_data, 10)
    # print(ecg_sample)
    
    # csv_path = "data/240507_pred_1hz.csv"
    # ecg_data = read_csv_df2(csv_path)
    # print(binarySearch(ecg_data, "2024-05-08 08:51:17.594"))
    
    # sampeld = lttb3(ecg_data, 10000)
    # print(sampeld)

    df = read_csv_df("data/240507_pred_20hz.csv")
    write_df_parquet(df, "240507_20hz.parquet")
    # print(read_parquet("240507_50hz.parquet"))