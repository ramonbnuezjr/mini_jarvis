# Changelog

All notable changes, issues, and resolutions for Mini-JARVIS.

## [Phase 4.5] - RAG Memory Tiering (Refinement)

### Added
- **Tiered Memory Architecture**: Three-tier system (core/reference/ephemeral) for intelligent document prioritization
- **Metadata Tracker**: SQLite-based tracking for version hashing, TTL, and access patterns
- **Weighted Retrieval**: Tier-based score boosting (1.5x core, 1.0x reference, 0.7x ephemeral)
- **Automatic Cleanup**: TTL-based expiry for ephemeral documents
- **Enhanced Scripts**:
  - `scripts/cleanup_expired_memory.py`: Cleanup script for expired documents
  - `scripts/test_tiered_memory.py`: Test script for tiered memory system
- **Updated Components**:
  - `RAGServer`: Added tiered collection support with backward compatibility
  - `Retriever`: Added weighted retrieval from tiered collections
  - `ingest_documents.py`: Added `--tier` and `--ttl` options
  - `chat.py`: Enabled tiering by default

### Features
- **Core Tier**: Important, permanent documents with 1.5x retrieval boost
- **Reference Tier**: Standard documents with normal retrieval weight
- **Ephemeral Tier**: Temporary documents with 0.7x weight and TTL-based expiry
- **Backward Compatible**: Single collection mode still supported for existing deployments

### Testing
- Comprehensive unit tests for `MetadataTracker`
- Integration tests for tiered RAG system
- Tests for weighted retrieval, TTL expiry, and tier management
- **UAT Status**: ✅ Passed - User acceptance testing completed successfully

## [Phase 3] - Tool System Implementation

### Added
- Tool Registry and Executor system (MCP-like server)
- 6 integrated tools: Weather, Time, Wikipedia, ArXiv, DuckDuckGo, HackerNews
- Function calling support for Gemini 2.0 Flash
- Multi-turn tool execution with conversation history
- Automatic tool routing (all tool queries go to cloud)

### Fixed

#### Wikipedia Tool Improvements
- **Issue:** Poor results for planet queries (e.g., "Mars" returning "Mar (title)" instead of planet)
- **Resolution:** 
  - Increased default sentences from 3 to 10 for better context
  - Improved disambiguation handling
  - Updated tool description to guide Gemini to use specific queries like "Mars (planet)"
- **Status:** Partially resolved - works better with specific queries

#### DuckDuckGo Web Search Improvements
- **Issue:** Poor results for news queries, rate limit errors
- **Resolution:**
  - Added automatic news search detection
  - Increased default results from 5 to 10
  - Improved query handling for news-specific searches
  - Added retry logic for rate limits with exponential backoff
- **Status:** ✅ Resolved

#### Tool Library Installation
- **Issue:** Tools reporting "library missing" errors despite packages being in requirements.txt
- **Resolution:** Verified and installed all required packages (`wikipedia`, `arxiv`, `duckduckgo-search`)
- **Status:** ✅ Resolved

#### DuckDuckGo Deprecation Warning & Rate Limits
- **Issue:** 
  - RuntimeWarning about `duckduckgo_search` being renamed to `ddgs`
  - Rate limit errors (202 Ratelimit) when making multiple searches
- **Resolution:** 
  - Updated `requirements.txt` to use new `ddgs` package (v9.9.3)
  - Migrated from `duckduckgo-search` to `ddgs`
  - Added retry logic with exponential backoff (3 attempts: 2s, 4s, 6s delays)
  - Improved rate limit detection and error messages
  - Added warning suppression at module level
- **Status:** ✅ Resolved

#### Weather API Key Configuration
- **Issue:** Weather tool reporting "API key missing"
- **Resolution:** Added `OPENWEATHER_API_KEY` to `.env` with documentation
- **Status:** ✅ Resolved

## [Phase 2] - Cloud Burst Implementation

### Fixed

#### Gemini API Model Name
- **Issue:** `404 Not Found` errors with `gemini-1.5-flash`
- **Resolution:** Updated to `gemini-2.0-flash` model name
- **Status:** ✅ Resolved

#### Conversation History Format
- **Issue:** `400 Bad Request` errors in multi-turn function calling
- **Resolution:** 
  - Fixed conversation history format in `CloudBrain.think_with_history()`
  - Correctly format user queries, model function calls, and function responses
- **Status:** ✅ Resolved

## [Phase 4] - RAG Pipeline Implementation

### Added
- RAG Server with ChromaDB vector database
- Document ingestion system (text, markdown, PDF support)
- Local embeddings (sentence-transformers/all-MiniLM-L6-v2) with API fallback
- Semantic search with top-k retrieval
- Automatic RAG context injection into queries
- Comprehensive test suite (unit, integration, UAT tests)

### Fixed

#### Document Chunking Infinite Loop Bug
- **Issue:** RAG document ingestion hanging indefinitely during chunking. Process would consume 100% CPU and never complete. Affected documents of specific sizes (e.g., 821 characters with chunk_size=150, overlap=30).
- **Root Cause:** Critical bug in `_chunk_text()` method where `start` position was advancing by 1 character instead of `stride = chunk_size - overlap`. This caused an infinite loop, creating 16+ chunks instead of the expected 7 chunks.
- **Resolution:**
  - Fixed stride calculation: `start` now advances by `chunk_size - overlap` (120 chars) instead of 1
  - Added comprehensive regression tests:
    - `test_chunking_stride_bug_regression()` - Reproduces exact bug scenario (821 chars → 7 chunks, not 16)
    - `test_chunking_stride_calculation()` - Validates stride math for various parameters
    - `test_chunking_produces_expected_stride_pattern()` - Verifies chunk boundaries follow correct stride pattern
  - Tests ensure correct chunk count and prevent infinite loops
- **Status:** ✅ Resolved. Bug fixed and regression tests added.
- **Reference:** Experiment #6 (continued 3) and #7 in project docs

#### Embedding Dimension Mismatch
- **Issue:** `chromadb.errors.InvalidArgumentError: Collection expecting embedding with dimension of 384, got 768`
- **Root Cause:** Inconsistent embedding dimensions between local model (384-dim) and API fallback (768-dim)
- **Resolution:** 
  - Removed API fallback in `document_ingester.py` and `retriever.py`, forcing use of local 384-dimension model
  - Explicitly set `embedding_dimension=384` when creating ChromaDB collection
- **Status:** ✅ Resolved

#### Virtual Environment Activation
- **Issue:** `ModuleNotFoundError: No module named 'sentence_transformers'` when running RAG scripts
- **Root Cause:** Virtual environment not activated before running scripts
- **Resolution:** Added clear instructions and checks in scripts to ensure venv is activated
- **Status:** ✅ Resolved

## [Phase 1] - Local Brain Implementation

### Fixed

#### Router Tool Routing
- **Issue:** Tool-requiring queries being routed to local brain (which doesn't support function calling)
- **Resolution:**
  - Added `TOOL_KEYWORDS` to router
  - Added `route_tools_to_cloud` parameter
  - All tool queries now route to cloud
- **Status:** ✅ Resolved

---

## Known Limitations

1. **Wikipedia Disambiguation:** Simple planet names (e.g., "Mars") may hit disambiguation. Use specific names like "Mars (planet)" for best results.

2. **Local LLM Function Calling:** Llama 3.2 3B doesn't support function calling, so all tool queries must use cloud (Gemini 2.0 Flash).

3. **Weather API Key:** Optional but required for weather tool functionality.

4. **DuckDuckGo Rate Limits:** DuckDuckGo enforces strict rate limits. If you encounter "rate limit exceeded" errors:
   - Wait a few minutes between searches
   - Use the HackerNews tool (`get_tech_news`) for tech news instead
   - The tool automatically retries up to 3 times with exponential backoff (2s, 4s, 6s delays)

