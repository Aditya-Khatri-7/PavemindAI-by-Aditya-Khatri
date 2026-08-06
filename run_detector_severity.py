"""
run_detector_severity.py  —  CLI tool for Road Pothole Detection & Severity System (Root Wrapper)
IBM Internship | Group 74 | AIML74 | UPES Dehradun
"""

import os
import sys
from pathlib import Path

# Add the subfolder Pothole-detection to sys.path so we can import pothole_analyzer
subfolder_path = Path(__file__).parent / 'Pothole-detection'
sys.path.append(str(subfolder_path))

# Change current working directory to the subfolder so relative paths (data/, runs/) resolve correctly
os.chdir(str(subfolder_path))

# Run the script
if __name__ == '__main__':
    import run_detector_severity
    run_detector_severity.main()
