#!/usr/bin/env python3

import time
import psutil
import sys

import pandas as pd


min_duration = 60 # duration in minutes
interval = 30 # profile interval in seconds

filename = sys.argv[1]
sec_duration = min_duration * 60 # duration in seconds
data = []
time_spent = 0
psutil.cpu_percent(interval=None)

while time_spent < sec_duration:
    time.sleep(interval)
    
    ts = time.time()
    cpu = psutil.cpu_percent(interval=None)
    memory = psutil.virtual_memory().percent
    row = (ts, cpu, memory)
    data.append(row)

    time_spent += interval


df = pd.DataFrame(data=data, columns=['timestamp', 'cpu', 'memory'])
df.to_csv(filename, index=False)