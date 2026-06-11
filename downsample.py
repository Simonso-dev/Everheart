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
            
            entry = {headers[0]: row[0], headers[1]: row[1]}
            if len(headers) > 2 and len(row) > 2:
                entry[headers[2]] = row[2]
            chunk.append(entry)

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

def uniform_downsample(csv_path: str, factor: int, output_path: str):
    sampled= []
    batch_count = 0
    for batch in stream_csv_chunks(csv_path, 10_000_000):
        sampled_ecg = every(batch, factor)
        sampled.extend(sampled_ecg)
        batch_count += 1
        print(f"Batch {batch_count} done! This processing took {(time.time() - start_time) / 60} minutes.", end="\n")

    print(len(sampled))
    pd.DataFrame(sampled).to_parquet(output_path, index=False)

if __name__ == "__main__":
    import argparse
    import os
    parser = argparse.ArgumentParser()
    parser.add_argument("ascii_file", help="Path to the input ASCII file")
    parser.add_argument("--factor", type=int, default=10, help="Downsampling factor (default: 10)")
    parser.add_argument("--input-freq", type=int, required=True, help="Original sample frequency in Hz (e.g. 1000)")
    parser.add_argument("--output", help="Output path (default: <input_name>_<output_freq>hz.parquet)")
    args = parser.parse_args()

    output_freq = args.input_freq // args.factor
    if args.output:
        output_path = args.output
    else:
        base = os.path.splitext(args.ascii_file)[0]
        output_path = f"{base}_{output_freq}hz.parquet"

    start_time = time.time()
    uniform_downsample(args.ascii_file, args.factor, output_path)
    print("-"*40)
    print(f"Done! This processing took {(time.time() - start_time) / 60} minutes.", end="\n")