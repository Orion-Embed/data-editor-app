#!/bin/bash
# setup.sh

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install Qt Designer (optional but recommended)
# On Ubuntu/Debian:
# sudo apt install qttools5-dev-tools qt6-tools-dev
# On macOS:
# brew install qt6
# On Windows: Download from qt.io

echo "Setup complete! Activate with: source venv/bin/activate"
