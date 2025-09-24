#!/usr/bin/env bash
# exit on error
set -o errexit

# Install system dependencies like tesseract and poppler
apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-nep tesseract-ocr-sin poppler-utils

# Install python dependencies
pip install -r requirements.txt