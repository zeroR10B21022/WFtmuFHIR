"""
Streamlit Cloud Entry Point
ICH Blood Pressure Management Application
"""
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import and run the main app
from ich_bp_agent.ui.app import main

if __name__ == "__main__":
    main()
