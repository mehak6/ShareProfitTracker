#!/usr/bin/env python3
"""
Refactored main entry point using new architecture
Uses controller pattern with separated concerns
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    from gui.main_window_refactored import MainWindowRefactored
    from utils.config import AppConfig
    
    def main():
        # Ensure required directories exist
        AppConfig.ensure_directories()
        
        # Create and run the refactored application
        app = MainWindowRefactored()
        app.run()

    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all required packages are installed:")
    print("pip install yfinance")
    sys.exit(1)
except Exception as e:
    print(f"Error starting application: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)