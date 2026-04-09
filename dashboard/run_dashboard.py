"""
Script to run the Streamlit dashboard
"""

import streamlit.web.cli as stcli
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == "__main__":
    sys.argv = ["streamlit", "run", "dashboard/app.py", "--server.port", "8501"]
    sys.exit(stcli.main())
