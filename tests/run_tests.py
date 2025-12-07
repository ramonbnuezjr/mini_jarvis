#!/usr/bin/env python3
"""Test runner for Mini-JARVIS test suite."""

import sys
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_tests():
    """Run all tests using pytest."""
    print("="*60)
    print("Mini-JARVIS Test Suite")
    print("="*60)
    print()
    
    # Run pytest with coverage
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",  # Verbose
        "--tb=short",  # Short traceback format
        "--cov=src",  # Coverage for src/
        "--cov-report=term-missing",  # Show missing lines
        "--cov-report=html:htmlcov",  # HTML report
    ]
    
    result = subprocess.run(cmd, cwd=project_root)
    
    if result.returncode == 0:
        print("\n" + "="*60)
        print("✅ All tests passed!")
        print("="*60)
        print("\nCoverage report generated in htmlcov/index.html")
    else:
        print("\n" + "="*60)
        print("❌ Some tests failed")
        print("="*60)
    
    return result.returncode


if __name__ == "__main__":
    sys.exit(run_tests())

