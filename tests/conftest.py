"""Pytest configuration and shared fixtures."""

import pytest
import tempfile
import shutil
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_text_file(temp_dir):
    """Create a sample text file for testing."""
    file_path = Path(temp_dir) / "sample.txt"
    content = """This is a test document about artificial intelligence.
    
Artificial intelligence (AI) is the simulation of human intelligence by machines.
Machine learning is a subset of AI that enables systems to learn from data.
Deep learning uses neural networks with multiple layers.

Natural language processing allows computers to understand human language.
Computer vision enables machines to interpret visual information.
"""
    file_path.write_text(content)
    return str(file_path)


@pytest.fixture
def sample_markdown_file(temp_dir):
    """Create a sample markdown file for testing."""
    file_path = Path(temp_dir) / "sample.md"
    content = """# Test Document

## Introduction

This is a markdown document for testing the RAG pipeline.

## Key Points

1. First point about testing
2. Second point about RAG
3. Third point about embeddings

## Conclusion

This document tests markdown ingestion.
"""
    file_path.write_text(content)
    return str(file_path)

