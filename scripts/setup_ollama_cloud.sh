#!/bin/bash
# Setup script for Ollama Cloud integration
# This sets up the hybrid pattern: local Ollama gateway with cloud models

set -e

echo "=========================================="
echo "Ollama Cloud Setup for Mini-JARVIS"
echo "=========================================="
echo ""

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama is not installed."
    echo "   Install it from: https://ollama.com/download"
    exit 1
fi

echo "✅ Ollama is installed: $(ollama --version | head -n1)"
echo ""

# Step 1: Sign in to Ollama Cloud
echo "Step 1: Sign in to Ollama Cloud"
echo "--------------------------------"
echo "This will authenticate your local Ollama with Ollama Cloud."
echo "You'll need your Ollama Cloud account credentials."
echo ""
read -p "Press Enter to continue with 'ollama signin'..."
ollama signin

if [ $? -eq 0 ]; then
    echo "✅ Successfully signed in to Ollama Cloud"
else
    echo "❌ Sign-in failed. Please try again."
    exit 1
fi

echo ""
echo "Step 2: Pull cloud model"
echo "--------------------------------"
echo "This will download the cloud model metadata."
echo "The model will run on Ollama Cloud infrastructure automatically."
echo ""
read -p "Press Enter to pull gpt-oss:120b-cloud..."
ollama pull gpt-oss:120b-cloud

if [ $? -eq 0 ]; then
    echo "✅ Successfully pulled gpt-oss:120b-cloud"
else
    echo "❌ Failed to pull model. Please check your connection and try again."
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Your Mini-JARVIS is now configured to use:"
echo "  - Local Ollama gateway: http://localhost:11434"
echo "  - Cloud model: gpt-oss:120b-cloud"
echo ""
echo "The cloud model will automatically offload to Ollama Cloud"
echo "when used, while your code only talks to the local endpoint."
echo ""
echo "Test it with:"
echo "  python scripts/test_cloud_burst.py"

