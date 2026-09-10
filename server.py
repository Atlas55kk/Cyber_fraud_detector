"""
Server launcher for the Crypto Fraud Tracing Engine Web Dashboard.
Usage:
    python server.py
Then open http://localhost:8000 in your browser.
"""

import uvicorn
from src.web.app import app

if __name__ == "__main__":
    print("=" * 80)
    print("LAUNCHING FORENSIC INVESTIGATION WEB DASHBOARD (MHA / SIH PS 26183)")
    print("Access portal at: http://localhost:8000")
    print("Press Ctrl+C to stop.")
    print("=" * 80)
    uvicorn.run("src.web.app:app", host="127.0.0.1", port=8000, reload=False)
