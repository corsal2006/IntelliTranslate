#!/usr/bin/env bash
# exit on error
set -o errexit

# FIX: Forcefully upgrade pip and install a specific, stable version of setuptools
pip install --upgrade pip
pip install "setuptools==65.5.0"

# Install system dependencies
apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-nep tesseract-ocr-sin poppler-utils

# Install python dependencies from requirements.txt
pip install -r requirements.txt