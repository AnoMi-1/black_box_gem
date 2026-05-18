#!/bin/bash

# 1. Initialize Virtual CAN interface for Black Box telemetry simulation
echo "⚙️ Setting up Virtual CAN interface..."
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set vcan0 up
echo "✅ vcan0 is now active and listening."

# 2. Start Ollama Server background daemon if not already running
echo "🧠 Initializing Ollama local inference engine..."
if pgrep -x "ollama" > /dev/null
then
    echo "✅ Ollama server is already running."
else
    echo "🚀 Starting Ollama server..."
    ollama serve > /dev/null 2>&1 &
    sleep 3 # Give the server a moment to spin up
fi

# 3. Verify Gemma model presence
echo "🔍 Checking for Gemma 3 model installation..."
ollama pull gemma:e4b

echo "🎉 Environment setup complete! You are ready to run the Streamlit app."
