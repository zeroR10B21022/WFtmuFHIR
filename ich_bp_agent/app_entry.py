"""
Entry point for Streamlit Cloud deployment
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the main app
from ui.app import main

if __name__ == "__main__":
    main()
