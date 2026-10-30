#!/usr/bin/env bash
# Render Build Script
set -o errexit

echo "==> Installing Python dependencies..."
pip install --upgrade pip
pip install -r backend/requirements.txt

echo "==> Initializing and seeding database if needed..."
python backend/seed.py

echo "==> Build complete!"
