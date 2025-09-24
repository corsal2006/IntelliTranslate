#!/usr/bin/env bash
# exit on error
set -o errexit

# Upgrade pip to ensure it can handle modern packages
pip install --upgrade pip

# Install system dependencies
apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-nep tesseract-ocr-sin poppler-utils

# Install the clean, minimal list of python dependencies
pip install -r requirements.txt