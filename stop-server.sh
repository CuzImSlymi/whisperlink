#!/bin/bash

echo "🛑 Stopping WhisperLink development servers..."

# Kill all related processes with force
pkill -f "react-scripts start" 2>/dev/null
pkill -f "electron" 2>/dev/null  
pkill -f "concurrently" 2>/dev/null
pkill -f "python_bridge.py" 2>/dev/null
pkill -f "npm.*dev" 2>/dev/null
pkill -f "npm.*start" 2>/dev/null

# Kill processes on port 3000 specifically
echo "Freeing port 3000..."
lsof -ti:3000 | xargs kill -9 2>/dev/null

# Force kill any remaining node processes related to this project
ps aux | grep -E "(whisperlink|WhisperLink)" | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null

echo "✅ All WhisperLink development servers stopped"