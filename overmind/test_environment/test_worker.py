#!/usr/bin/env python3
"""Simple worker process that outputs job processing to stdout."""

import time
import sys
import random
from datetime import datetime

def main():
    print("Starting background worker process...", flush=True)
    job_id = 1
    
    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Simulate job processing
        processing_time = random.randint(2, 8)
        print(f"[WORKER] {timestamp} - Processing job #{job_id} (estimated {processing_time}s)", flush=True)
        
        # Simulate work being done
        for i in range(processing_time):
            time.sleep(1)
            if i == processing_time // 2:
                print(f"[WORKER] {timestamp} - Job #{job_id} 50% complete", flush=True)
        
        print(f"[WORKER] {timestamp} - Job #{job_id} completed successfully", flush=True)
        
        job_id += 1
        time.sleep(random.randint(1, 3))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[WORKER] Shutting down worker process...", flush=True)
        sys.exit(0) 