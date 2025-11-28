#!/usr/bin/env python3
"""Check if all prerequisites are installed for Mini-JARVIS."""

import sys
import subprocess
import shutil
from pathlib import Path

# Colors for terminal output
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

def check_command(cmd, name, version_flag="--version"):
    """Check if a command exists and optionally get version."""
    if shutil.which(cmd):
        try:
            result = subprocess.run(
                [cmd, version_flag],
                capture_output=True,
                text=True,
                timeout=5
            )
            version = result.stdout.strip() or result.stderr.strip() or "installed"
            return True, version.split('\n')[0]
        except Exception as e:
            return True, "installed (version check failed)"
    return False, None

def check_python_version():
    """Check Python version (need 3.11+)."""
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    if version.major == 3 and version.minor >= 11:
        return True, version_str
    return False, version_str

def check_ollama_model(model_name="llama3.2:3b"):
    """Check if Ollama model is installed."""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if model_name in result.stdout:
            return True, "installed"
        return False, "not found"
    except Exception as e:
        return False, f"error: {str(e)}"

def check_ollama_service():
    """Check if Ollama service is running."""
    try:
        # Try to connect to Ollama API
        import httpx
        response = httpx.get("http://localhost:11434/api/tags", timeout=2.0)
        if response.status_code == 200:
            return True, "running"
        return False, f"HTTP {response.status_code}"
    except ImportError:
        return None, "httpx not installed (can't check)"
    except Exception as e:
        return False, f"not accessible: {str(e)}"

def check_python_packages():
    """Check if required Python packages are installed."""
    # Map package names to their import names
    package_map = {
        "httpx": "httpx",
        "python-dotenv": "dotenv"
    }
    missing = []
    installed = []
    
    for package, import_name in package_map.items():
        try:
            __import__(import_name)
            installed.append(package)
        except ImportError:
            missing.append(package)
    
    return len(missing) == 0, installed, missing

def check_venv():
    """Check if we're in a virtual environment."""
    return hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )

def main():
    """Run all checks."""
    print(f"\n{BLUE}{'='*60}{NC}")
    print(f"{BLUE}Mini-JARVIS: Prerequisites Check{NC}")
    print(f"{BLUE}{'='*60}{NC}\n")
    
    all_ok = True
    
    # Check Python version
    print(f"{YELLOW}Python Version:{NC}")
    py_ok, py_ver = check_python_version()
    if py_ok:
        print(f"  {GREEN}✓ Python {py_ver} (3.11+ required){NC}")
    else:
        print(f"  {RED}✗ Python {py_ver} (need 3.11+){NC}")
        all_ok = False
    print()
    
    # Check virtual environment
    print(f"{YELLOW}Virtual Environment:{NC}")
    if check_venv():
        print(f"  {GREEN}✓ Virtual environment active{NC}")
    else:
        print(f"  {YELLOW}⚠ Not in virtual environment (recommended){NC}")
    print()
    
    # Check Python packages
    print(f"{YELLOW}Python Packages:{NC}")
    pkgs_ok, installed, missing = check_python_packages()
    if pkgs_ok:
        print(f"  {GREEN}✓ All required packages installed: {', '.join(installed)}{NC}")
    else:
        print(f"  {RED}✗ Missing packages: {', '.join(missing)}{NC}")
        print(f"  {YELLOW}  Run: pip install -r requirements.txt{NC}")
        all_ok = False
    print()
    
    # Check Ollama
    print(f"{YELLOW}Ollama:{NC}")
    ollama_ok, ollama_ver = check_command("ollama", "Ollama")
    if ollama_ok:
        print(f"  {GREEN}✓ Ollama installed: {ollama_ver}{NC}")
    else:
        print(f"  {RED}✗ Ollama not installed{NC}")
        print(f"  {YELLOW}  Run: curl -fsSL https://ollama.com/install.sh | sh{NC}")
        all_ok = False
    print()
    
    # Check Ollama service
    if ollama_ok:
        print(f"{YELLOW}Ollama Service:{NC}")
        service_ok, service_status = check_ollama_service()
        if service_ok:
            print(f"  {GREEN}✓ Ollama service is {service_status}{NC}")
        elif service_ok is None:
            print(f"  {YELLOW}⚠ {service_status}{NC}")
        else:
            print(f"  {RED}✗ Ollama service is {service_status}{NC}")
            print(f"  {YELLOW}  Run: ollama serve{NC}")
            all_ok = False
        print()
    
    # Check Llama 3.2 3B model
    if ollama_ok:
        print(f"{YELLOW}Llama 3.2 3B Model:{NC}")
        model_ok, model_status = check_ollama_model("llama3.2:3b")
        if model_ok:
            print(f"  {GREEN}✓ Llama 3.2 3B is {model_status}{NC}")
        else:
            print(f"  {RED}✗ Llama 3.2 3B is {model_status}{NC}")
            print(f"  {YELLOW}  Run: ollama pull llama3.2:3b{NC}")
            all_ok = False
        print()
    
    # Check .env file
    print(f"{YELLOW}Environment File:{NC}")
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    if env_file.exists():
        print(f"  {GREEN}✓ .env file exists{NC}")
    else:
        print(f"  {YELLOW}⚠ .env file not found (will use defaults){NC}")
    print()
    
    # Summary
    print(f"{BLUE}{'='*60}{NC}")
    if all_ok:
        print(f"{GREEN}✓ All prerequisites are installed!{NC}")
        print(f"{GREEN}You're ready to test: python scripts/test_brain.py{NC}")
    else:
        print(f"{RED}✗ Some prerequisites are missing{NC}")
        print(f"{YELLOW}Run: bash scripts/setup.sh to install missing components{NC}")
    print(f"{BLUE}{'='*60}{NC}\n")
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())

