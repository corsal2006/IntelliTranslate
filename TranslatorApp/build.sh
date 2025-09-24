#!/usr/bin/env bash
# exit on error
set -o errexit

# NEW: Upgrade pip and build tools first
pip install --upgrade pip setuptools wheel

# Install system dependencies
apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-nep tesseract-ocr-sin poppler-utils

# Install python dependencies from requirements.txt
pip install -r requirements.txt