#!/bin/bash
# Startup script for Newsletter Aggregator Flask app

set -e  # Exit on error

echo "Starting Newsletter Aggregator..."
echo "================================"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Warning: .env file not found. Make sure GEMINI_API_KEY is set."
fi

# Check if config file exists
if [ ! -f config/senders.json ]; then
    echo "Error: config/senders.json not found!"
    exit 1
fi

# Start Flask app
echo "Starting Flask development server..."
echo "Access the app at: http://127.0.0.1:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uv run flask --app src.web.app run --host=127.0.0.1 --port=5000 --debug
