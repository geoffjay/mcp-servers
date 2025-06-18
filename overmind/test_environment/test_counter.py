#!/usr/bin/env python3
"""Simple counter process that outputs incrementing numbers."""

import time
import sys
from datetime import datetime

counter = 0  # Global counter for access in exception handler

def main():
    global counter
    print("Starting counter process...", flush=True)
    counter = 0
    
    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        counter += 1
        
        print(f"[COUNTER] {timestamp} - Count: {counter}", flush=True)
        
        # Every 10th count, show additional info
        if counter % 10 == 0:
            print(f"[COUNTER] {timestamp} - Reached milestone: {counter}", flush=True)
        
        # Every 25th count, simulate some work
        if counter % 25 == 0:
            print(f"[COUNTER] {timestamp} - Performing periodic maintenance...", flush=True)
            time.sleep(2)
            print(f"[COUNTER] {timestamp} - Maintenance completed", flush=True)
        
        time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n[COUNTER] Shutting down counter process... Final count: {counter}", flush=True)
        sys.exit(0) 