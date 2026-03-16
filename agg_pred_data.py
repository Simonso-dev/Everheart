import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import time

# Check the columns.
columns = pd.read_csv("./data/240507_complete_predictions.ascii", nrows=0, skiprows=7).columns
print(columns)

def read_large_ecg(file_path, chunk_size):
    for chunk in pd.read_csv(file_path, chunksize=chunk_size, skiprows=7, parse_dates=True, skipinitialspace=True):
        # chunk.rename(columns={'Time    ': 'Time'}, inplace=True)
        yield chunk

agg_data = pd.DataFrame()

# data_chunks = pd.read_csv("./data/240507_complete.ascii", skiprows=6, parse_dates=True, chunksize=1000)
i = 0
start_time = time.time()
for data_chunk in read_large_ecg("./data/240507_complete_predictions.ascii", 1000):
    # Create a new dataframe to manipulate the current chunk.
    # Then replace 'x's with 0.0.
    df = pd.DataFrame(data_chunk)
    df['240507_complete:ECG'] = pd.to_numeric(df["240507_complete:ECG"], errors='coerce').fillna(0.0)
    df['Time'].str.strip()
    
    # Calculate the mean ecg for the chunk and get the last datetime in the chunk.
    avg_ecg = df['240507_complete:ECG'].mean()
    time_col = df['Time'].tail(1).values[0]
    prediction = df["Prediction"].tail(1).values[0]
    
    # Create a new dataframe containing the datetime and avg ecg then 
    # append it to the aggregated dataframe.
    new_row = pd.DataFrame({"Time": [time_col], "240507_complete:ECG": [avg_ecg], "Prediction": [prediction]})
    agg_data = pd.concat([agg_data, new_row], ignore_index=True)
    # print(agg_data)
    
    # i += 1
    # if i == 120000:
    #    break

print(f"Done! This processing took {(time.time() - start_time) / 60} minutes.", end="\n")
print(agg_data.info())

agg_data.to_csv("240507_pred_mean2.csv", index=False)

# plt.plot(agg_data['Time'], agg_data['240507PIG:ECG'])
# plt.show()