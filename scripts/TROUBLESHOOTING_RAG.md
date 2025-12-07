# Troubleshooting RAG Pipeline Tests

## Issue: Test Scripts Hang or Take Too Long

### Problem
When running RAG tests (especially `manual_test_rag_2_pdf_chunking.py`), the script may appear to hang or take a very long time.

### Root Cause
The embedding model (`sentence-transformers/all-MiniLM-L6-v2`) needs to be downloaded on first use:
- **Model size:** ~80MB
- **First download:** Can take 5-10 minutes on Pi5
- **Subsequent runs:** Much faster (model is cached)

### Solution 1: Pre-load the Model (Recommended)

Before running tests, pre-download the model:

```bash
cd /home/ramon/ai_projects/mini_jarvis
source venv/bin/activate
python scripts/preload_embedding_model.py
```

This will:
- Download and cache the model once
- Make all subsequent RAG operations much faster
- Only needs to be done once (or after clearing cache)

### Solution 2: Wait Patiently

If you're running tests for the first time:
- The script will download the model automatically
- This can take 5-10 minutes on Pi5
- Look for progress messages in the output
- The model will be cached for future use

### Solution 3: Check if Model is Already Cached

The model is cached in:
```
~/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/
```

If this directory exists and has files, the model is already downloaded.

### Updated Test Scripts

All manual test scripts now include:
- Clear warnings about first-time model download
- 10-minute timeout to prevent indefinite hangs
- Better progress indicators

### Performance Expectations

**First Run (model download):**
- Model download: 5-10 minutes
- Model loading: 30-60 seconds
- Total: ~6-11 minutes

**Subsequent Runs (model cached):**
- Model loading: 5-15 seconds
- Document ingestion: 1-5 seconds (depending on size)
- Total: ~10-20 seconds

### If Script Still Hangs

1. **Check if process is running:**
   ```bash
   ps aux | grep manual_test_rag
   ```

2. **Kill stuck process:**
   ```bash
   kill -9 <PID>
   ```

3. **Pre-load model first:**
   ```bash
   python scripts/preload_embedding_model.py
   ```

4. **Then retry the test**

### Network Issues

If download fails due to network:
- Check internet connection
- Try again later
- The model download will resume from where it left off

## Issue: Document Chunking Infinite Loop (FIXED)

### Problem
Document ingestion hangs indefinitely during chunking, consuming 100% CPU and never completing.

### Root Cause
Critical bug in `_chunk_text()` method where the `start` position was advancing by 1 character instead of `stride = chunk_size - overlap`. This caused an infinite loop, creating excessive chunks (e.g., 16+ chunks instead of 7 for an 821-character document).

### Solution
✅ **FIXED** - The stride calculation has been corrected. The `start` position now advances by `chunk_size - overlap` (e.g., 120 chars) instead of 1.

### Prevention
Regression tests have been added to prevent this bug from reappearing:
- `test_chunking_stride_bug_regression()` - Reproduces exact bug scenario
- `test_chunking_stride_calculation()` - Validates stride math
- `test_chunking_produces_expected_stride_pattern()` - Verifies chunk boundaries

### How to Verify Fix
Run the regression tests:
```bash
source venv/bin/activate
python -m pytest tests/test_document_ingester.py::TestDocumentIngester::test_chunking_stride_bug_regression -v
```

All three regression tests should pass, confirming the bug is fixed.

