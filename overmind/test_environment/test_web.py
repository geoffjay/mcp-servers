#!/usr/bin/env python3
"""Simple web-like process that outputs to stdout periodically."""

import time
import sys
from datetime import datetime

def main():
    print("Starting web server process...", flush=True)
    port = 8000
    
    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[WEB:{port}] {timestamp} - Server listening on port {port}", flush=True)
        
        # Simulate some request handling
        time.sleep(3)
        print(f"[WEB:{port}] {timestamp} - Handling request from 192.168.1.100", flush=True)
        
        time.sleep(2)
        print(f"[WEB:{port}] {timestamp} - Request completed successfully", flush=True)
        
        time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[WEB] Shutting down web server...", flush=True)
        sys.exit(0) 