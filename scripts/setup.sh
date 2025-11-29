#!/bin/bash
# Mini-JARVIS Setup Script for Raspberry Pi 5
# Installs all prerequisites and dependencies

set -e  # Exit on error

echo "=========================================="
echo "Mini-JARVIS Setup for Raspberry Pi 5"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running on Pi 5
check_pi5() {
    echo -e "${YELLOW}Checking Raspberry Pi 5...${NC}"
    if [ -f /proc/device-tree/model ]; then
        MODEL=$(cat /proc/device-tree/model)
        if [[ $MODEL == *"Raspberry Pi 5"* ]]; then
            echo -e "${GREEN}✓ Raspberry Pi 5 detected${NC}"
            return 0
        else
            echo -e "${RED}✗ Not a Raspberry Pi 5. This script is designed for Pi 5.${NC}"
            read -p "Continue anyway? (y/N) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    else
        echo -e "${YELLOW}⚠ Could not detect Pi model. Continuing...${NC}"
    fi
}

# Update system
update_system() {
    echo ""
    echo -e "${YELLOW}Updating system packages...${NC}"
    sudo apt update
    sudo apt full-upgrade -y
    echo -e "${GREEN}✓ System updated${NC}"
}

# Install Python 3.11+ if needed
install_python() {
    echo ""
    echo -e "${YELLOW}Checking Python version...${NC}"
    if command -v python3.11 &> /dev/null || command -v python3.12 &> /dev/null; then
        PYTHON_VER=$(python3 --version | cut -d' ' -f2)
        echo -e "${GREEN}✓ Python $PYTHON_VER found${NC}"
    else
        PYTHON_VER=$(python3 --version | cut -d' ' -f2)
        echo -e "${YELLOW}Python $PYTHON_VER found. Python 3.11+ recommended.${NC}"
        read -p "Install Python 3.11? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo apt install -y python3.11 python3.11-venv python3.11-dev
            echo -e "${GREEN}✓ Python 3.11 installed${NC}"
        fi
    fi
}

# Install Ollama
install_ollama() {
    echo ""
    echo -e "${YELLOW}Checking Ollama installation...${NC}"
    if command -v ollama &> /dev/null; then
        OLLAMA_VER=$(ollama --version 2>&1 | head -n1 || echo "installed")
        echo -e "${GREEN}✓ Ollama is installed: $OLLAMA_VER${NC}"
    else
        echo -e "${YELLOW}Installing Ollama...${NC}"
        curl -fsSL https://ollama.com/install.sh | sh
        echo -e "${GREEN}✓ Ollama installed${NC}"
    fi
    
    # Check if Ollama service is running
    if systemctl is-active --quiet ollama || pgrep -x ollama > /dev/null; then
        echo -e "${GREEN}✓ Ollama service is running${NC}"
    else
        echo -e "${YELLOW}Starting Ollama service...${NC}"
        ollama serve &
        sleep 2
        echo -e "${GREEN}✓ Ollama service started${NC}"
    fi
}

# Pull Llama 3.2 3B model
install_llama_model() {
    echo ""
    echo -e "${YELLOW}Checking for Llama 3.2 3B model...${NC}"
    if ollama list 2>/dev/null | grep -q "llama3.2:3b"; then
        echo -e "${GREEN}✓ Llama 3.2 3B is already installed${NC}"
    else
        echo -e "${YELLOW}Pulling Llama 3.2 3B model (this may take a while)...${NC}"
        ollama pull llama3.2:3b
        echo -e "${GREEN}✓ Llama 3.2 3B model installed${NC}"
    fi
}

# Setup Python virtual environment
setup_venv() {
    echo ""
    echo -e "${YELLOW}Setting up Python virtual environment...${NC}"
    
    PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    cd "$PROJECT_DIR"
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo -e "${GREEN}✓ Virtual environment created${NC}"
    else
        echo -e "${GREEN}✓ Virtual environment already exists${NC}"
    fi
    
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    echo -e "${GREEN}✓ Python dependencies installed${NC}"
}

# Create .env file if it doesn't exist
setup_env() {
    echo ""
    echo -e "${YELLOW}Setting up environment file...${NC}"
    PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    cd "$PROJECT_DIR"
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            echo -e "${GREEN}✓ Created .env from .env.example${NC}"
        else
            cat > .env << EOF
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434

# Cloud API Keys (for Cloud Burst feature)
# Get your Gemini API key from: https://makersuite.google.com/app/apikey
# GEMINI_API_KEY=your-key-here

# Optional: Other cloud providers
# ANTHROPIC_API_KEY=your-key-here
# OPENAI_API_KEY=your-key-here
EOF
            echo -e "${GREEN}✓ Created .env file${NC}"
        fi
    else
        echo -e "${GREEN}✓ .env file already exists${NC}"
    fi
}

# Main installation flow
main() {
    check_pi5
    update_system
    install_python
    install_ollama
    install_llama_model
    setup_venv
    setup_env
    
    echo ""
    echo "=========================================="
    echo -e "${GREEN}Setup Complete!${NC}"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo "  1. Activate virtual environment: source venv/bin/activate"
    echo "  2. Run test script: python scripts/test_brain.py"
    echo ""
}

main "$@"

