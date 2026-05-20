import pandas as pd
import numpy as np
import time, csv

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

def every(data, factor: int):
    '''
        Downsampling data with uniform sampling.
    '''
    reduced = []
    base_factor = factor
    while factor <= len(data) - 1:
        reduced.append(data[factor])
        factor += base_factor
    
    return reduced

def uniform_downsample(csv_path:str, factor: int):
    sampled= []
    batch_count = 0
    for batch in stream_csv_chunks(csv_path, 10_000_000):
        # sampled_ecg = lttb(batch, 2500000)
        sampled_ecg = every(batch, factor)
        sampled.extend(sampled_ecg)
        batch_count += 1
        print(f"Batch {batch_count} done! This processing took {(time.time() - start_time) / 60} minutes.", end="\n")

        # if batch_count == 1:
        #    break

    # reduced2 = lttb(sampled, 10000)
    # final = lttb(reduced2, 5000)

    print(len(sampled))
    keys = sampled[0].keys()
    with open("./data/240507_pred_100hz.csv", "w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, keys)
        writer.writeheader()
        writer.writerows(sampled)

if __name__ == "__main__":
    start_time = time.time()
    uniform_downsample("./data/raw/240507_complete_predictions.ascii", 10)
    print("-"*40)
    print(f"Done! This processing took {(time.time() - start_time) / 60} minutes.", end="\n")