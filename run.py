#!/usr/bin/env python3
"""
Run script for Database Editor
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from main import main
    main()
except ImportError as e:
    print(f"Import error: {e}")
    print("Please install required packages:")
    print("pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
