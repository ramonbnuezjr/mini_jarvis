#!/bin/bash
# Helper script to set Ollama Cloud API key in .env file

if [ -z "$1" ]; then
    echo "Usage: ./scripts/set_ollama_key.sh YOUR_API_KEY"
    echo ""
    echo "Example:"
    echo "  ./scripts/set_ollama_key.sh ollama_abc123xyz..."
    exit 1
fi

API_KEY="$1"
ENV_FILE=".env"

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ .env file not found!"
    exit 1
fi

# Update the API key
if grep -q "OLLAMA_CLOUD_API_KEY=" "$ENV_FILE"; then
    # Use sed to replace the key (works on both Linux and macOS)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|OLLAMA_CLOUD_API_KEY=.*|OLLAMA_CLOUD_API_KEY=$API_KEY|" "$ENV_FILE"
    else
        sed -i "s|OLLAMA_CLOUD_API_KEY=.*|OLLAMA_CLOUD_API_KEY=$API_KEY|" "$ENV_FILE"
    fi
    echo "✅ Updated OLLAMA_CLOUD_API_KEY in .env"
else
    echo "❌ OLLAMA_CLOUD_API_KEY not found in .env"
    exit 1
fi

