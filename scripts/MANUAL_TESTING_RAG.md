# Manual Testing Scripts for RAG Pipeline

This directory contains lightweight, interactive manual testing scripts for the RAG pipeline. These scripts are optimized for Raspberry Pi 5 and avoid resource-intensive operations that could cause system freezes.

## Available Tests

### Test 1: Ingest TXT → Verify Retrieval
**Script:** `manual_test_rag_1_txt_retrieval.py`

Tests basic text document ingestion and retrieval functionality.

**What it tests:**
- Creating and ingesting a text document
- Retrieving relevant chunks based on queries
- Verifying retrieval quality

**Run:**
```bash
python scripts/manual_test_rag_1_txt_retrieval.py
```

---

### Test 2: Ingest PDF → Test Chunking
**Script:** `manual_test_rag_2_pdf_chunking.py`

Tests document chunking with smaller chunk sizes.

**What it tests:**
- Chunking documents into smaller pieces
- Verifying chunk sizes are appropriate
- Ensuring chunks are searchable

**Run:**
```bash
python scripts/manual_test_rag_2_pdf_chunking.py
```

**Note:** If PyPDF2 is not installed, the test will use a markdown file instead.

---

### Test 3: Query with No Matches → Graceful Failure
**Script:** `manual_test_rag_3_no_matches.py`

Tests graceful handling of queries with no relevant matches.

**What it tests:**
- Handling queries with no relevant matches
- Empty collection handling
- min_score filtering

**Run:**
```bash
python scripts/manual_test_rag_3_no_matches.py
```

---

### Test 4: Large Document → Performance Test
**Script:** `manual_test_rag_4_performance.py`

Tests performance with medium-sized documents (optimized for Pi5).

**What it tests:**
- Performance with larger documents (lightweight version)
- Ingestion speed
- Retrieval speed

**Run:**
```bash
python scripts/manual_test_rag_4_performance.py
```

**Note:** This is a lightweight version (30 sections instead of 100) to avoid overwhelming the Pi5.

---

### Test 5: Reboot → Persistence Check
**Script:** `manual_test_rag_5_persistence.py`

Tests data persistence across server restarts.

**What it tests:**
- Data persistence across server restarts
- ChromaDB persistence
- Retrieval after "reboot"

**Run:**
```bash
python scripts/manual_test_rag_5_persistence.py
```

---

## Running All Tests

To run all tests sequentially:

```bash
python scripts/run_all_manual_rag_tests.py
```

This will:
1. Prompt you to confirm before starting
2. Run each test one by one
3. Ask if you want to continue after each test
4. Provide a summary at the end

## Differences from UAT Tests

The manual testing scripts are designed to be:
- **Lightweight:** Avoid resource-intensive operations
- **Interactive:** Step-by-step output with clear status messages
- **Pi5-friendly:** Optimized for Raspberry Pi 5 hardware constraints
- **Individual:** Can be run separately or all together

The automated UAT tests (`tests/test_uat_rag.py`) are more comprehensive but may be too resource-intensive for Pi5 in some scenarios.

## Troubleshooting

### Script hangs or Pi5 becomes unresponsive
- Run tests individually instead of all at once
- Test 4 (performance) uses a smaller document size - if it still causes issues, reduce the number of sections in the script

### PDF support not available
- Install PyPDF2: `pip install PyPDF2`
- Or the test will automatically use markdown files instead

### Import errors
- Make sure you're in the project root directory
- Activate the virtual environment: `source venv/bin/activate`

## Expected Results

All tests should pass with:
- ✅ Clear success messages
- ⚠️  Warnings for non-critical issues
- ❌ Failures only for critical problems

Each test provides detailed output showing what it's testing and the results.

