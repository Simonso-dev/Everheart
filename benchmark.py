import time, statistics, random
from datetime import datetime, timedelta
from util import read_csv_df, test_get_ecg_pred_resample, read_multiple_files
import numpy as np

'''
    This script is for benchmarking the resample function only.

    The benchmark uses randomization to get 100 start and end dates. These dates
    is then used as input to run the resample funciton 100 times. Where time spent 
    running the function in milisecond (ms) is measured to analyse how fast it is.
'''

# Amount of tests to run.
TESTS = 100

#
#  Load data (old version)
#
# start_time = time.time()
# ecg_csv_100hz = read_csv_df("data/240507_pred_100hz.csv")
# ecg_csv_20hz = read_csv_df("data/240507_pred_20hz.csv")
# ecg_csv_1hz = read_csv_df("data/240507_pred_1hz.csv")
# end_time = time.time()
# print(f"Loading all datasets took: {end_time - start_time:.6f} seconds")
# print(f"{'-'*5}")
# 

#
# Load data (new version)
#
parquet_paths = ("data/240220PIG_complete_1hz.parquet", "data/240220PIG_complete_10hz.parquet", "data/240220PIG_complete_100hz.parquet")

start_time = time.time()
parquet_files = read_multiple_files(parquet_paths)

ecg_1hz = parquet_files.get()
ecg_20hz = parquet_files.get()
ecg_100hz = parquet_files.get()

end_time = time.time()
print(f"Loading all datasets took: {end_time - start_time:.6f} seconds")
print(f"{'-'*5}")

datasets = (ecg_1hz, ecg_20hz, ecg_100hz)

# Inputs
random_inputs = []

# Set a base minimum and maximum date
base_min_date = datetime(2024, 5, 7, 0, 0, 0)
base_max_date = datetime(2024, 5, 14, 23, 59, 59)

total_range_seconds = int((base_max_date - base_min_date).total_seconds())

# Generate 100 random datetime ranges
for i in range(TESTS):
    start_seconds = random.randint(0, total_range_seconds)
    end_seconds = random.randint(start_seconds + 1, total_range_seconds)
    
    # Convert back to datetime objects
    start_time_dt = base_min_date + timedelta(seconds=start_seconds)
    end_time_dt = base_min_date + timedelta(seconds=end_seconds)
    
    # Format to match your existing input format (with milliseconds)
    # Remove trailing zeros after decimal point for cleaner output
    start_str = start_time_dt.strftime("%Y-%m-%d %H:%M:%S.%f")
    end_str = end_time_dt.strftime("%Y-%m-%d %H:%M:%S.%f")
    
    random_inputs.append((start_str, end_str))

# List of time elapsed per test
times = []
times_no_input = []

# Test all inputs
for i, (start_date, end_date) in enumerate(random_inputs):
    start = time.perf_counter()
    test_get_ecg_pred_resample(start_date, end_date, datasets)
    end = time.perf_counter()

    elapsed = (end - start) * 1000

    times.append(elapsed)

# Test with no inputs
for _ in range(TESTS):
    start = time.perf_counter()
    test_get_ecg_pred_resample(datasets=datasets)
    end = time.perf_counter()

    elapsed = (end - start) * 1000

    times_no_input.append(elapsed)

if times:
    print("With inputs")
    print("-" * 40)
    print(f"{'Index':<6} | {'Time (ms)':<12} | {'Duration (s)'}")
    print("-" * 40)
    
    mean_time = statistics.mean(times)
    median_time = statistics.median(times)
    IQR_INPUTS = np.percentile(times, 75) - np.percentile(times, 25)
    
    # Print individual times in ms and seconds
    for i, t in enumerate(times):
        print(f"{i+1:<6} | {t:<12.2f} | {(t/1000):.4f}s")
        
    print(f"{'-'*5}")
    print(f"Average Time: {mean_time:.2f} ms")
    print(f"Median Time:  {median_time:.2f} ms")
    print(f"Min/Max:      {min(times):.2f} / {max(times):.2f} ms")
    print(f"IQR:          {IQR_INPUTS} ms")
    print("")

if times_no_input:
    print("Without inputs")
    print("-" * 40)
    print(f"{'Index':<6} | {'Time (ms)':<12} | {'Duration (s)'}")
    print("-" * 40)
    
    mean_time_no_input = statistics.mean(times_no_input)
    median_time_no_input = statistics.median(times_no_input)
    IQR_NO_INPUTS = np.percentile(times_no_input, 75) - np.percentile(times_no_input, 25)
    
    # Print individual times in ms and seconds
    for i, t in enumerate(times_no_input):
        print(f"{i+1:<6} | {t:<12.2f} | {(t/1000):.4f}s")
        
    print(f"{'-'*5}")
    print(f"Average Time: {mean_time_no_input:.2f} ms")
    print(f"Median Time:  {median_time_no_input:.2f} ms")
    print(f"Min/Max:      {min(times_no_input):.2f} / {max(times_no_input):.2f} ms")
    print(f"IQR:          {IQR_NO_INPUTS} ms")
    print("")