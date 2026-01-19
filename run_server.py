#!/usr/bin/env python3
"""Start dev server and keep it running"""
import subprocess
import sys
import time

if __name__ == "__main__":
    print("Starting FastAPI dev server on port 8005...")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8005"],
        cwd="/Users/adria/Desktop/bpm-internal-tool-v2"
    )
    
    # Give it time to start
    time.sleep(3)
    
    print(f"Server process PID: {proc.pid}")
    print("Server should be running on http://localhost:8005")
    print("Press Ctrl+C to stop...")
    
    try:
        proc.wait()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        proc.terminate()
        proc.wait()
    
    sys.exit(0)
