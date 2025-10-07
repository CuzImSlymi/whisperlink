#!/bin/bash

echo "🚀 Starting WhisperLink development environment..."

# Clean up any existing processes first
./stop-server.sh 2>/dev/null

echo "Starting React development server and Electron app..."
npm run dev

echo "Development servers started!"
echo "To stop the servers, run: npm run stop or ./stop-server.sh"