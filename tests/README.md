# Mini-JARVIS Test Suite

## Overview

Automated test suite for Mini-JARVIS using pytest. Tests are organized by module and include unit tests, integration tests, and coverage reporting.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures and pytest configuration
├── test_document_ingester.py # Tests for document ingestion and chunking
├── test_retriever.py        # Tests for semantic search and retrieval
├── test_rag_server.py      # Tests for RAG server operations
├── test_rag_integration.py # Integration tests for full RAG pipeline
└── run_tests.py            # Test runner script
```

## Running Tests

### Run All Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest tests/

# Or use the test runner
python tests/run_tests.py
```

### Run Specific Test Files

```bash
# Test document ingester only
pytest tests/test_document_ingester.py -v

# Test RAG server only
pytest tests/test_rag_server.py -v

# Test integration tests
pytest tests/test_rag_integration.py -v
```

### Run with Coverage

```bash
# Generate coverage report
pytest tests/ --cov=src/memory --cov-report=term-missing

# Generate HTML coverage report
pytest tests/ --cov=src/memory --cov-report=html
# View report: open htmlcov/index.html
```

## Test Coverage

### Phase 4: RAG Pipeline Tests

**DocumentIngester (10 tests)**
- ✅ Text file loading
- ✅ Markdown file loading
- ✅ Text chunking (small and large texts)
- ✅ Chunk overlap handling
- ✅ Document ingestion (text and markdown)
- ✅ Error handling (nonexistent files, unsupported types)
- ✅ Local embedding generation

**Retriever (6 tests)**
- ✅ Semantic search with results
- ✅ Minimum score filtering
- ✅ Empty collection handling
- ✅ Context formatting
- ✅ Query embedding (local model)

**RAGServer (8 tests)**
- ✅ Server initialization
- ✅ Statistics retrieval
- ✅ Single document ingestion
- ✅ Multiple document ingestion (with duplicate ID prevention)
- ✅ Context retrieval
- ✅ Empty collection retrieval
- ✅ Minimum score filtering
- ✅ Memory clearing

**Integration Tests (3 tests)**
- ✅ Full pipeline (ingest → retrieve → format)
- ✅ Multiple queries against same collection
- ✅ Persistent storage across server instances

**Total: 28 tests, all passing ✅**

## Test Requirements

Tests require:
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage reporting
- `chromadb` - Vector database (for RAG tests)
- `sentence-transformers` - Local embeddings (for embedding tests)

Install with:
```bash
pip install pytest pytest-asyncio pytest-cov chromadb sentence-transformers
```

## Test Fixtures

Shared fixtures in `conftest.py`:
- `temp_dir` - Temporary directory for test files
- `sample_text_file` - Sample text document
- `sample_markdown_file` - Sample markdown document
- `temp_rag_dir` - Temporary directory for RAG storage
- `rag_server` - RAGServer instance for testing

## Notes

- Tests use temporary directories that are cleaned up after each test
- Embedding tests require `sentence-transformers` to be installed
- Tests are designed to work without API keys (local embeddings only)
- ChromaDB collections are created fresh for each test to avoid conflicts

