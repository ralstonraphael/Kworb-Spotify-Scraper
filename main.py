"""Main entry point for the Spotify Chart Analyzer application."""
from pathlib import Path
import sys

# Add the project root to Python path
project_root = str(Path(__file__).parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from src.ui.streamlit_app import main

if __name__ == "__main__":
    main() 