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

# Create .env file (or copy from .env.example if it exists)
cat > .env << EOF
OLLAMA_BASE_URL=http://localhost:11434
EOF
```

#### 4. Test Local Brain

```bash
# Run test script
python scripts/test_brain.py

# Or chat with JARVIS interactively
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
│       ├── local_brain.py    # Ollama client
│       └── router.py         # Local vs Cloud routing
├── scripts/
│   ├── test_brain.py         # Test script
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

## Next Steps

- [ ] Add Cloud Burst (Anthropic/OpenAI API)
- [ ] Implement Senses (Voice Input, Camera)
- [ ] Add Memory & Tools (RAG, MCP Server)
- [ ] Implement Expression (TTS Output)

