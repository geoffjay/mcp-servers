#!/usr/bin/env python3
"""Simple logger process that outputs log entries to stdout."""

import time
import sys
import random
from datetime import datetime

LOG_LEVELS = ["INFO", "DEBUG", "WARN", "ERROR"]
COMPONENTS = ["auth", "database", "cache", "api", "scheduler"]

def main():
    print("Starting logging service...", flush=True)
    
    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        level = random.choice(LOG_LEVELS)
        component = random.choice(COMPONENTS)
        
        if level == "ERROR":
            messages = [
                "Connection timeout after 30 seconds",
                "Failed to authenticate user",
                "Database query failed",
                "Invalid request format"
            ]
        elif level == "WARN":
            messages = [
                "High memory usage detected",
                "Slow query detected (2.5s)",
                "Rate limit threshold approaching",
                "Cache miss ratio high"
            ]
        else:
            messages = [
                "Request processed successfully",
                "User logged in",
                "Database connection established",
                "Cache updated",
                "Background task completed"
            ]
        
        message = random.choice(messages)
        print(f"[LOGGER] {timestamp} [{level}] {component}: {message}", flush=True)
        
        time.sleep(random.randint(1, 4))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[LOGGER] Shutting down logging service...", flush=True)
        sys.exit(0) 