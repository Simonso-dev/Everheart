import pandas as pd
import numpy as np
import time, csv
from util import read_large_ecg_pred, lttb

def very_slow_processing(): 
    agg_data = pd.DataFrame()

    i = 0
    start_time = time.time()
    for data_chunk in read_large_ecg_pred("./data/240507_complete_predictions.ascii", 1000):
        # Create a new dataframe to manipulate the current chunk.
        # Then replace 'x's with 0.0.
        df = pd.DataFrame(data_chunk)
        df['240507_complete:ECG'] = pd.to_numeric(df["240507_complete:ECG"], errors='coerce').fillna(0.0)
        df['Time'].str.strip()

        # Downsample from 1000hz to 50hz using the LTTB algorithm.
        sampled_ecg = lttb(data=df.to_dict("records"), threshold=50)
        df_sampled_ecg = pd.DataFrame(sampled_ecg)

        agg_data = pd.concat([df, df_sampled_ecg], ignore_index=True)
        # print(agg_data)

    print(f"Done! This processing took {(time.time() - start_time) / 60} minutes.", end="\n")
    print(agg_data.info())

    agg_data.to_csv("240507_pred_50hz.csv", index=False)

def maybe_fast(csv_path):
    sampled = []
    batch = []
    headers = None
    with open(csv_path, "r") as csv_file:
        ecg_csv = csv.reader(csv_file)
        
        for _ in range(7):
            next(ecg_csv, None)

        headers = next(ecg_csv)
        
        batch_count = 0
        count = 0
        for row in ecg_csv:
            if row[1] in ("", "NA", "N/A", "null", "nan", "x", "X"):
                row[1] = "0.0"

            batch.append({headers[0]: row[0], headers[1]: row[1], headers[2]: row[2]})
            count += 1

            if count == 10000000:
                sampled_ecg = lttb(batch, 10000)
                sampled.extend(sampled_ecg)
                batch.clear()
                count = 0
                batch_count += 1
                print(f"Batch {batch_count} done! This processing took {(time.time() - start_time) / 60} minutes.", end="\n")
            
            # if batch_count == 1:
            #    break

        # print(batch)
        # print(count)
        # threshold = count * 0.05
        # sampled = lttb(batch, threshold)
    '''
    with open("240507_pred_50hz.csv", "w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(headers)
        for row in sampled:
            writer.writerow([row])
    '''
    print(len(sampled))
    keys = sampled[0].keys()
    with open("240507_pred_1hz.csv", "w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, keys)
        writer.writeheader()
        writer.writerows(sampled)

def fill_nan(value):
    if value in ("", "NA", "N/A", "null", "nan", "x", "X"):
        return str(0.0)
    else:
        return value

def stream_csv_chunks(filename: str, chunk_size: int):
    chunk = []
    with open(filename, "r") as csv_file:
        ecg_csv = csv.reader(csv_file)
        
        for _ in range(7):
            next(ecg_csv, None)

        headers = next(ecg_csv)
        print(headers)
        
        for row in ecg_csv:
            if row[1] in ("", "NA", "N/A", "null", "nan", "x", "X"):
                row[1] = "0.0"
            
            chunk.append({headers[0]: row[0], headers[1]: row[1], headers[2]: row[2]})

            if len(chunk) >= chunk_size:
                yield chunk
                chunk = []

    if chunk:
        yield chunk

def every(data, factor):
    reduced = []
    base_factor = factor
    while factor <= len(data) - 1:
        reduced.append(data[factor])
        factor += base_factor
    
    return reduced

def maybe_2fast(csv_path):
    sampled= []
    batch_count = 0
    for batch in stream_csv_chunks(csv_path, 10_000_000):
        # sampled_ecg = lttb(batch, 2500000)
        sampled_ecg = every(batch, 1000)
        sampled.extend(sampled_ecg)
        batch_count += 1
        print(f"Batch {batch_count} done! This processing took {(time.time() - start_time) / 60} minutes.", end="\n")

        # if batch_count == 1:
        #    break

    # reduced2 = lttb(sampled, 10000)
    # final = lttb(reduced2, 5000)

    print(len(sampled))
    keys = sampled[0].keys()
    with open("240507_pred_1hz.csv", "w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, keys)
        writer.writeheader()
        writer.writerows(sampled)

if __name__ == "__main__":
    start_time = time.time()
    # maybe_fast("./data/240507_complete_predictions.ascii")
    maybe_2fast("./data/240507_complete_predictions.ascii")
    print("-------------------------------------------------")
    print(f"Done! This processing took {(time.time() - start_time) / 60} minutes.", end="\n")