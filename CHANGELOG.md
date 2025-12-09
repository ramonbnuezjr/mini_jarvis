# Changelog

All notable changes, issues, and resolutions for Mini-JARVIS.

## [Migration] - Gemini 2.0 Flash → Ollama Cloud (Hybrid Pattern)

### Changed
- **Cloud Burst Migration**: Migrated from Google Gemini 2.0 Flash API to Ollama Cloud using hybrid pattern
- **Architecture**: Now uses local Ollama gateway (`http://localhost:11434`) for both local and cloud models
- **Authentication**: Removed API key requirement - authentication handled by `ollama signin` (one-time)
- **Model**: Updated from `gpt-oss:20b-cloud` to `gpt-oss:120b-cloud`

### Added
- **Hybrid Pattern**: Local Ollama gateway with automatic cloud model offloading
- **Setup Scripts**:
  - `scripts/setup_ollama_cloud.sh`: Interactive setup for Ollama Cloud authentication
  - `scripts/test_hybrid_ollama.py`: Test script for hybrid pattern verification
- **Regression Tests**: `tests/test_cloud_brain_regression.py` - Comprehensive regression test suite (10/10 passed)

### Removed
- `GEMINI_API_KEY` environment variable (no longer needed)
- `OLLAMA_CLOUD_API_KEY` environment variable (authentication via `ollama signin`)
- `OLLAMA_CLOUD_BASE_URL` environment variable (uses local Ollama gateway)

### Benefits
- **No API keys in code**: More secure, no risk of committing secrets
- **Single endpoint**: Simpler architecture, easier debugging
- **Same API format**: Works with existing tools and integrations
- **Automatic offloading**: Cloud models handled transparently
- **Simplified router**: Just chooses model name, not provider
- **Better pricing**: Flat-fee model vs per-token pricing

### Migration Steps
1. Run `ollama signin` to authenticate with Ollama Cloud (one-time)
2. Run `ollama pull gpt-oss:120b-cloud` to download cloud model metadata
3. Update `.env` to remove API key variables
4. Test with `python scripts/test_hybrid_ollama.py`

### Testing
- ✅ All regression tests passed (10/10)
- ✅ Tool calling works with cloud brain
- ✅ RAG context injection works with cloud brain
- ✅ Multi-turn conversations work
- ✅ Router logic unchanged and working
- ✅ Backward compatibility maintained

### Documentation
- Updated `README.md` with hybrid pattern setup instructions
- Updated `MIGRATION_OLLAMA_CLOUD.md` with complete migration guide
- Updated `architecture.md` to reflect new cloud burst architecture

## [Phase 4.6] - Google Drive Sync (Cloud Integration)

### Added
- **Google Drive Sync**: Automatic synchronization of Google Drive folders to RAG memory tiers
- **OAuth 2.0 Authentication**: Secure authentication with Google Drive API using OAuth 2.0
- **Folder-to-Tier Mapping**: Automatic mapping of Google Drive folders to RAG tiers:
  - `JARVIS-Core/` → core tier (1.5x retrieval boost, permanent)
  - `JARVIS-Reference/` → reference tier (1.0x normal weight, permanent)
  - `JARVIS-Ephemeral/` → ephemeral tier (0.7x weight, 30-day TTL)
- **Incremental Sync**: Only downloads and ingests changed files (tracks file hashes and modification times)
- **Version Hash Tracking**: SHA256 hash tracking for detecting content changes
- **Google Docs Support**: Exports Google Docs, Sheets, and Slides as text for ingestion
- **Recursive Folder Scanning**: Scans subfolders recursively to find all documents
- **Sync State Persistence**: Maintains sync state in `.drive_sync_state.json` for efficient updates
- **Enhanced Scripts**:
  - `scripts/sync_google_drive.py`: Main sync script with OAuth authentication
  - `scripts/SETUP_GOOGLE_DRIVE.md`: Comprehensive setup guide
  - `scripts/GOOGLE_DRIVE_QUICKSTART.md`: Quick start reference
  - `scripts/test_drive_sync_retrieval.py`: Test retrieval from synced documents

### Features
- **Automatic Tier Assignment**: Documents are automatically assigned to the correct tier based on folder location
- **Efficient Updates**: Only processes new or modified files, making subsequent syncs fast
- **Token Persistence**: OAuth token saved for future syncs (no re-authentication needed)
- **Error Handling**: Graceful error handling with detailed logging
- **Dry Run Mode**: Preview what would be synced without actually syncing

### Fixed

#### RAG Context Integration with Cloud Brain
- **Issue:** RAG context was being retrieved but not properly formatted for Gemini, causing it to ignore the context
- **Resolution:**
  - Updated `orchestrator.py` to format RAG context as a system prompt that explicitly instructs the model to use the provided context
  - Added proper context formatting: "You have access to the following context documents... Please use this information to answer..."
  - Both Cloud Brain (Gemini) and Local Brain now receive RAG context as system prompts
  - Responses now properly cite sources (Context 1, Context 2, etc.)
- **Status:** ✅ Resolved - RAG context now properly integrated with both local and cloud inference

### Testing
- Manual testing completed with real Google Drive folders
- Verified incremental sync (only changed files are processed)
- Verified tier mapping (folders correctly map to tiers)
- Verified Google Docs export functionality
- Tested retrieval from synced documents

### Dependencies Added
- `google-api-python-client>=2.100.0` - Google Drive API client
- `google-auth-httplib2>=0.1.1` - HTTP transport for Google Auth
- `google-auth-oauthlib>=1.1.0` - OAuth 2.0 for Google APIs

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

