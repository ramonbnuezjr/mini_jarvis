# Mini-JARVIS

Local-first AI assistant for Raspberry Pi 5 with hybrid intelligence (local speed + cloud power).

## Architecture

See `.cursor/notepads/architecture.md` for system design.

## Hardware Setup

**Note:** This project assumes Raspberry Pi 5 with 2TB NVMe SSD as the primary/boot drive. All models, data, and OS run on fast NVMe storage for optimal performance.

- Ollama models are stored in `~/.ollama/models` (on NVMe by default)
- Project data will be stored on NVMe for fast I/O
- No external storage configuration needed

## Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# Run the setup script (installs everything)
bash scripts/setup.sh

# Activate virtual environment
source venv/bin/activate

# Check if everything is installed
python scripts/check_setup.py

# Test Local Brain
python scripts/test_brain.py
```

### Option 2: Manual Setup

#### 1. Check Prerequisites

```bash
# Check what's installed
python3 scripts/check_setup.py
```

#### 2. Install Ollama (if needed)

```bash
# Install Ollama on Raspberry Pi 5
curl -fsSL https://ollama.com/install.sh | sh

# Pull Llama 3.2 3B (fits in 6GB RAM budget, good balance)
# Models are stored on NVMe at ~/.ollama/models
ollama pull llama3.2:3b

# Start Ollama service (if not running)
ollama serve
```

#### 3. Setup Python Environment

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
OLLAMA_BASE_URL=http://localhost:11434
# Get your Gemini API key from: https://makersuite.google.com/app/apikey
# GEMINI_API_KEY=your-key-here
EOF
```

#### 3a. Get Gemini API Key (Recommended, for Cloud Burst)

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key and add it to `.env`:
   ```bash
   GEMINI_API_KEY=your-actual-key-here
   ```

**Note**: Cloud Burst is optional but recommended. The system works with just the Local Brain, but Cloud Burst enables complex queries, better reasoning, and prepares for future tool-use capabilities.

#### 4. Test the System

```bash
# Test Local Brain only
python scripts/test_brain.py

# Test Cloud Burst (requires GEMINI_API_KEY)
python scripts/test_cloud_burst.py

# Interactive chat (uses both Local and Cloud automatically)
python scripts/chat.py
```

## Project Structure

```
mini_jarvis/
├── .cursorrules              # Coding standards
├── .cursor/
│   └── notepads/
│       ├── architecture.md   # System architecture
│       └── technical_specs.md # Hardware constraints
├── src/
│   └── brain/
│       ├── __init__.py
│       ├── local_brain.py    # Ollama client (Llama 3.2 3B)
│       ├── cloud_brain.py    # Gemini 2.0 Flash API client
│       ├── router.py         # Local vs Cloud routing logic
│       └── orchestrator.py  # Coordinates Local and Cloud brains
├── scripts/
│   ├── test_brain.py         # Test Local Brain
│   ├── test_cloud_burst.py   # Test Cloud Burst
│   ├── diagnose_gemini.py    # Diagnose Gemini API issues
│   ├── chat.py               # Interactive chat interface
│   ├── setup.sh              # Automated setup script
│   └── check_setup.py        # Prerequisites checker
└── requirements.txt
```

## Development

- **Language**: Python 3.11+ with type hints
- **Style**: Small, modular functions; prefer `asyncio` for I/O
- **Privacy**: Local-first; sensitive data stays on device
- **Secrets**: Use `.env` file (never hardcode)

## Features

- ✅ **Local Brain**: Ollama with Llama 3.2 3B for fast, private inference
- ✅ **Cloud Burst**: Gemini 2.0 Flash API for complex reasoning (implemented)
- ✅ **Smart Router**: Automatically routes queries to local or cloud based on complexity
- ✅ **Orchestrator**: Seamlessly coordinates between Local Brain and Cloud Burst
- ✅ **Interactive Chat**: Command-line interface for testing

## Current Status

### ✅ Implemented
- Local Brain (Llama 3.2 3B via Ollama)
- Cloud Burst (Gemini 2.0 Flash API)
- Smart Router (automatic local/cloud routing)
- Orchestrator (seamless brain coordination)
- Interactive Chat Interface

### 🚧 Next Steps
- [ ] Build MCP Server with Weather API tool
- [ ] Implement RAG pipeline for long-term memory
- [ ] Add Voice Input (STT) and Output (TTS)
- [ ] Add Camera integration for vision tasks

