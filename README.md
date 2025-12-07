# Mini-JARVIS

Local-first AI assistant for Raspberry Pi 5 with hybrid intelligence (local speed + cloud power).

## Architecture

See `.cursor/notepads/architecture.md` for system design.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed history of issues, fixes, and improvements.

## Development Roadmap

**Priority Order:**
1. ✅ **Phase 1 & 2: Brain** (Local + Cloud) - **COMPLETE**
2. ✅ **Phase 3: Agentic Layer** (Tools & MCP Server) - **COMPLETE**
3. ✅ **Phase 4: RAG Pipeline** (Long-term Memory) - **COMPLETE**
4. ✅ **Phase 4.5: RAG Memory Tiering** (Refinement) - **COMPLETE**
5. ✅ **Phase 4.6: Google Drive Sync** (Cloud Integration) - **COMPLETE**
6. 📋 **Phase 5: Voice/Vision Integration** (STT/TTS/VLM) - **NEXT**

**Rationale:** Tools first to enable real-time data access (Weather, Time), then memory for context, then cloud sync for seamless document management, then voice/vision for natural interaction.

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

# Create .env file
cat > .env << EOF
OLLAMA_BASE_URL=http://localhost:11434
# Get your Gemini API key from: https://makersuite.google.com/app/apikey
# GEMINI_API_KEY=your-key-here
EOF
```

#### 3a. Get API Keys (Recommended)

**Gemini API Key (Required for Cloud Burst and Tools):**
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key and add it to `.env`:
   ```bash
   GEMINI_API_KEY=your-actual-key-here
   ```

**OpenWeatherMap API Key (Optional, for Weather Tool):**
1. Go to [OpenWeatherMap](https://openweathermap.org/api)
2. Sign up for a free account
3. Get your API key from the dashboard
4. Add it to `.env`:
   ```bash
   OPENWEATHER_API_KEY=your-actual-key-here
   ```

**Note**: 
- Gemini API key is required for Cloud Burst and tool execution (Wikipedia, ArXiv, Web Search, etc.)
- Weather API key is optional - the weather tool will report if the key is missing
- Other tools (Wikipedia, ArXiv, DuckDuckGo, HackerNews) work without API keys

#### 4. Test the System

```bash
# Test Local Brain only
python scripts/test_brain.py

# Test Cloud Burst (requires GEMINI_API_KEY)
python scripts/test_cloud_burst.py

# Interactive chat (uses both Local and Cloud automatically)
python scripts/chat.py
```

#### 5. Setup RAG Pipeline (Phase 4 - Optional)

The RAG pipeline provides long-term memory by ingesting documents into a vector database.

```bash
# Install RAG dependencies
pip install chromadb sentence-transformers PyPDF2

# Ingest documents into memory (default: reference tier)
python scripts/ingest_documents.py document1.txt document2.md notes.pdf

# Ingest into specific tier
python scripts/ingest_documents.py important_doc.txt --tier core
python scripts/ingest_documents.py temp_notes.txt --tier ephemeral --ttl 3600

# Test RAG retrieval
python scripts/test_rag.py

# Test tiered memory system
python scripts/test_tiered_memory.py

# Clean up expired ephemeral documents
python scripts/cleanup_expired_memory.py

# Chat with RAG enabled (automatic if documents are ingested)
python scripts/chat.py
```

**RAG Features:**
- **Document Support**: Text (.txt), Markdown (.md), PDF (.pdf), Google Docs (exported as text)
- **Local Embeddings**: Uses `sentence-transformers/all-MiniLM-L6-v2` (~80MB, CPU-friendly)
- **Automatic Context**: RAG context is automatically injected into queries when relevant
- **Storage**: Vector database stored at `~/.jarvis/memory` on NVMe
- **Tiered Memory** (Phase 4.5):
  - **Core Tier**: Important documents (1.5x retrieval boost)
  - **Reference Tier**: Standard documents (normal weight)
  - **Ephemeral Tier**: Temporary documents (0.7x weight, TTL-based expiry)
  - **Metadata Tracking**: SQLite database for version hashing, TTL, and access patterns
  - **Automatic Cleanup**: Expired ephemeral documents are automatically removed
- **Google Drive Sync** (Phase 4.6):
  - **Automatic Sync**: Syncs Google Drive folders to RAG memory tiers
  - **Folder Mapping**: `JARVIS-Core/` → core tier, `JARVIS-Reference/` → reference tier, `JARVIS-Ephemeral/` → ephemeral tier
  - **Incremental Sync**: Only downloads and ingests changed files
  - **Version Tracking**: Tracks file hashes and modification times
  - **Google Docs Support**: Exports Google Docs/Sheets/Slides as text

#### 6. Setup Google Drive Sync (Phase 4.6 - Optional)

Sync your Google Drive folders to RAG memory automatically.

```bash
# First-time setup (see scripts/SETUP_GOOGLE_DRIVE.md for detailed instructions)
# 1. Get OAuth credentials from Google Cloud Console
# 2. Save as credentials.json in project root
# 3. Create folders in Google Drive: JARVIS-Core/, JARVIS-Reference/, JARVIS-Ephemeral/

# Run sync (authenticates on first run)
python scripts/sync_google_drive.py

# Sync specific folder
python scripts/sync_google_drive.py --folder JARVIS-Core

# Dry run (see what would sync)
python scripts/sync_google_drive.py --dry-run
```

**Google Drive Sync Features:**
- **OAuth 2.0 Authentication**: Secure authentication with token persistence
- **Folder-to-Tier Mapping**: Automatic mapping of Google Drive folders to RAG tiers
- **Incremental Sync**: Only syncs new or modified files (tracks hashes and modification times)
- **Google Docs Support**: Exports Google Docs, Sheets, and Slides as text
- **Recursive Scanning**: Scans subfolders recursively
- **Sync State Tracking**: Maintains sync state for efficient incremental updates

See `scripts/SETUP_GOOGLE_DRIVE.md` for detailed setup instructions.

## Project Structure

```
mini_jarvis/
├── .cursorrules              # Coding standards
├── .cursor/
│   └── notepads/
│       ├── architecture.md   # System architecture
│       └── technical_specs.md # Hardware constraints
├── src/
│   ├── brain/
│   │   ├── __init__.py
│   │   ├── local_brain.py    # Ollama client (Llama 3.2 3B)
│   │   ├── cloud_brain.py    # Gemini 2.0 Flash API client
│   │   ├── router.py         # Local vs Cloud routing logic
│   │   ├── orchestrator.py  # Coordinates Local and Cloud brains
│   │   └── tool_executor.py # Executes tools from LLM function calls
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── base_tool.py      # Abstract base class for tools
│   │   ├── tool_registry.py  # Tool registry (MCP-like server)
│   │   ├── default_registry.py # Creates registry with all tools
│   │   ├── weather_tool.py    # Weather API tool
│   │   ├── time_tool.py       # Time/Date tool
│   │   ├── knowledge_tool.py # Wikipedia & ArXiv tools
│   │   └── search_tool.py    # DuckDuckGo & HackerNews tools
│   └── memory/               # RAG Pipeline (Phase 4)
│       ├── __init__.py
│       ├── rag_server.py     # Main RAG server interface
│       ├── document_ingester.py  # Document loading and chunking
│       ├── retriever.py      # Semantic search and retrieval
│       └── metadata_tracker.py  # Metadata tracking (Phase 4.5)
├── scripts/
│   ├── test_brain.py         # Test Local Brain
│   ├── test_cloud_burst.py   # Test Cloud Burst
│   ├── diagnose_gemini.py    # Diagnose Gemini API issues
│   ├── test_tools.py         # Test tool registry
│   ├── test_tool_prompts.py  # Test prompts that trigger tools
│   ├── test_tools_live.py    # Test tools through orchestrator
│   ├── ingest_documents.py   # Ingest documents into RAG memory
│   ├── sync_google_drive.py  # Google Drive sync (Phase 4.6)
│   ├── cleanup_expired_memory.py  # Cleanup expired ephemeral docs
│   ├── test_rag.py           # Test RAG retrieval
│   ├── test_drive_sync_retrieval.py  # Test retrieval from synced docs
│   ├── chat.py               # Interactive chat interface
│   ├── setup.sh              # Automated setup script
│   ├── check_setup.py        # Prerequisites checker
│   ├── SETUP_GOOGLE_DRIVE.md # Google Drive setup guide
│   └── GOOGLE_DRIVE_QUICKSTART.md  # Quick start guide
└── requirements.txt
```

## Development

- **Language**: Python 3.11+ with type hints
- **Style**: Small, modular functions; prefer `asyncio` for I/O
- **Privacy**: Local-first; sensitive data stays on device
- **Secrets**: Use `.env` file (never hardcode)

## Features

- ✅ **Local Brain**: Ollama with Llama 3.2 3B for fast, private inference
- ✅ **Cloud Burst**: Gemini 2.0 Flash API for complex reasoning
- ✅ **Smart Router**: Automatically routes queries to local or cloud based on complexity
- ✅ **Orchestrator**: Seamlessly coordinates between Local Brain and Cloud Burst
- ✅ **Tool System**: 6 tools integrated (Weather, Time, Wikipedia, ArXiv, DuckDuckGo, HackerNews)
- ✅ **Function Calling**: Gemini can invoke tools automatically based on user queries
- ✅ **RAG Pipeline**: Long-term memory with ChromaDB, document ingestion, and semantic search
- ✅ **Tiered Memory**: Three-tier architecture (core/reference/ephemeral) with weighted retrieval
- ✅ **Google Drive Sync**: Automatic sync of Google Drive folders to RAG memory tiers
- ✅ **Interactive Chat**: Command-line interface with RAG context integration

## Current Status

### ✅ Implemented (Phase 1, 2, 3, 4, 4.5 & 4.6)
- **Phase 1: Local Brain** - Ollama with Llama 3.2 3B for fast, private inference
- **Phase 2: Cloud Burst** - Gemini 2.0 Flash API for complex reasoning
- **Phase 3: Agentic Layer** - Tool system with 6 integrated tools:
  - ✅ Weather Tool (requires OpenWeatherMap API key)
  - ✅ Time/Date Tool
  - ✅ Wikipedia Search Tool
  - ✅ ArXiv Research Paper Search Tool
  - ✅ DuckDuckGo Web Search Tool
  - ✅ HackerNews Tech News Tool
- **Phase 4: RAG Pipeline** - Long-term memory system:
  - ✅ ChromaDB vector database (persistent storage on NVMe)
  - ✅ Document ingestion (text, markdown, PDF support)
  - ✅ Local embeddings (sentence-transformers/all-MiniLM-L6-v2)
  - ✅ Semantic search with top-k retrieval
  - ✅ Automatic context injection into queries with proper formatting
- **Phase 4.5: RAG Memory Tiering** - Intelligent memory management:
  - ✅ Three-tier architecture (core/reference/ephemeral)
  - ✅ Weighted retrieval (1.5x core, 1.0x reference, 0.7x ephemeral)
  - ✅ Metadata tracking with SQLite (version hashing, TTL, access patterns)
  - ✅ Automatic cleanup for expired ephemeral documents
  - ✅ Backward compatible with single collection mode
- **Phase 4.6: Google Drive Sync** - Cloud document integration:
  - ✅ OAuth 2.0 authentication with token persistence
  - ✅ Folder-to-tier mapping (JARVIS-Core/ → core, JARVIS-Reference/ → reference, JARVIS-Ephemeral/ → ephemeral)
  - ✅ Incremental sync (only changed files)
  - ✅ Version hash tracking (SHA256)
  - ✅ Google Docs/Sheets/Slides export support
  - ✅ Recursive folder scanning
- Smart Router (automatic local/cloud routing, routes tool queries to cloud)
- Orchestrator (seamless brain coordination with multi-turn tool execution and RAG context)
- Tool Registry & Executor (MCP-like server for tool management)
- Interactive Chat Interface with RAG context integration

### 🚧 Development Phases

#### ✅ Phase 4: RAG Pipeline (Long-term Memory) - **COMPLETE**
- ✅ Implement vector database (ChromaDB)
- ✅ Document ingestion and embedding (text, markdown, PDF)
- ✅ Context retrieval system (semantic search with top-k chunks)
- ✅ Long-term memory integration with Orchestrator
- ✅ Local embeddings (sentence-transformers/all-MiniLM-L6-v2) with API fallback
- ✅ Automatic RAG context injection for relevant queries

#### ✅ Phase 4.5: RAG Memory Tiering (Refinement) - **COMPLETE**
- ✅ Tiered memory architecture (core/reference/ephemeral)
- ✅ Metadata tracking with SQLite (version hashing, TTL, access patterns)
- ✅ Weighted retrieval (1.5x core, 1.0x reference, 0.7x ephemeral)
- ✅ Automatic cleanup for expired ephemeral documents
- ✅ Backward compatible with single collection mode
- ✅ **UAT Passed**: User acceptance testing completed successfully

#### ✅ Phase 4.6: Google Drive Sync (Cloud Integration) - **COMPLETE**
- ✅ OAuth 2.0 authentication with Google Drive API
- ✅ Folder-to-tier mapping (JARVIS-Core/ → core tier, etc.)
- ✅ Incremental sync with version hash tracking
- ✅ Google Docs/Sheets/Slides export support
- ✅ Recursive folder scanning
- ✅ Sync state persistence for efficient updates
- ✅ Integration with tiered RAG memory system

#### Phase 5: Voice/Vision Integration (STT/TTS/VLM)
- [ ] Voice Input (STT with Whisper)
- [ ] Voice Output (TTS)
- [ ] Camera integration for vision tasks
- [ ] Vision Language Model (VLM) integration

## Troubleshooting & Known Issues

### Tool Issues & Resolutions

#### 1. Wikipedia Tool - Disambiguation Problems

**Problem:** When querying simple planet names like "Mars", the tool was returning incorrect articles (e.g., "Mar (title)" instead of "Mars (planet)").

**Root Cause:** Wikipedia's disambiguation system. Simple queries like "Mars" can match multiple articles, and the library's auto-suggestion wasn't reliably selecting the planet article.

**Resolution:**
- Increased default sentences from 3 to 10 for better context
- Improved disambiguation handling logic
- Updated tool description to guide Gemini to use specific queries like "Mars (planet)" for planets
- **Workaround:** When asking about planets, use specific names like "Mars (planet)" or "Jupiter (planet)" in queries

**Status:** Partially resolved. The tool works better with specific queries. Simple planet names may still hit disambiguation, but the tool description now guides Gemini to use specific names.

#### 2. DuckDuckGo Web Search - Poor News Results & Rate Limits

**Problem:** 
- Web search wasn't returning good results for news queries like "latest news about Raspberry Pi 5"
- Rate limit errors (202 Ratelimit) when making multiple searches

**Root Cause:** 
- General web search (`ddgs.text()`) isn't optimized for news queries. DuckDuckGo has a dedicated news search API
- DuckDuckGo enforces strict rate limits

**Resolution:**
- Added automatic news search detection (queries with "news", "latest", "recent", "breaking" use `ddgs.news()`)
- Increased default results from 5 to 10
- Improved query handling for news-specific searches
- Added retry logic with exponential backoff for rate limits
- Better error messages suggesting HackerNews as alternative

**Status:** ✅ Resolved. News queries work better, and rate limits are handled gracefully.

#### 3. Tool Libraries "Missing" Errors

**Problem:** Tools were reporting "library missing" errors even though libraries (`wikipedia`, `arxiv`, `duckduckgo-search`) were installed.

**Root Cause:** 
- Libraries were in `requirements.txt` but not installed in the virtual environment
- Error messages from tools were being misinterpreted by Gemini

**Resolution:**
- Verified packages were installed: `pip install wikipedia arxiv duckduckgo-search`
- Tested tools directly - they were working correctly
- The issue was likely temporary or related to error message interpretation

**Status:** ✅ Resolved. All required packages are now properly installed and tested.

#### 4. DuckDuckGo Deprecation Warning & Rate Limits

**Problem:** 
- RuntimeWarning: `duckduckgo_search` package has been renamed to `ddgs`
- Rate limit errors (202 Ratelimit) when making multiple searches quickly

**Root Cause:** 
- The `duckduckgo-search` package was deprecated in favor of `ddgs`
- DuckDuckGo enforces strict rate limits to prevent abuse

**Resolution:**
- Updated `requirements.txt` to use new `ddgs` package
- Migrated from `duckduckgo-search` to `ddgs` (v9.9.3)
- Added retry logic with exponential backoff (3 attempts: 2s, 4s, 6s delays)
- Improved rate limit detection and error messages
- Added warning suppression at module level
- Tool now suggests using HackerNews tool as alternative when rate limited

**Status:** ✅ Resolved. Package updated and rate limit handling improved.

#### 5. RAG Pipeline - Document Chunking Infinite Loop Bug

**Problem:** 
- RAG document ingestion was hanging indefinitely during chunking
- Process would consume 100% CPU and never complete
- Affected documents of specific sizes (e.g., 821 characters with chunk_size=150, overlap=30)

**Root Cause:** 
- Critical bug in `_chunk_text()` method in `document_ingester.py`
- The `start` position was advancing by 1 character instead of `stride = chunk_size - overlap`
- This caused an infinite loop, creating 16+ chunks instead of the expected 7 chunks
- The bug was triggered when the chunking logic didn't properly advance the start position

**Resolution:**
- Fixed stride calculation: `start` now advances by `chunk_size - overlap` (120 chars) instead of 1
- Added regression tests to prevent the bug from reappearing:
  - `test_chunking_stride_bug_regression()` - Reproduces exact bug scenario
  - `test_chunking_stride_calculation()` - Validates stride math for various parameters
  - `test_chunking_produces_expected_stride_pattern()` - Verifies chunk boundaries
- Tests ensure correct chunk count (7 chunks, not 16) and prevent infinite loops

**Status:** ✅ Resolved. Bug fixed and regression tests added.

#### 6. Weather API Key Configuration

**Problem:** Weather tool was reporting "API key missing" errors.

**Root Cause:** `OPENWEATHER_API_KEY` was not set in `.env` file.

**Resolution:**
- Added `OPENWEATHER_API_KEY` placeholder to `.env` file
- Updated README with instructions for getting free OpenWeatherMap API key
- Tool gracefully reports when API key is missing

**Status:** ✅ Resolved. API key configuration is documented and optional (tool reports when missing).

### API & Configuration Issues

#### 7. Gemini API Model Name Change

**Problem:** `404 Not Found` errors when calling Gemini API with `gemini-1.5-flash`.

**Root Cause:** Google updated the model name to `gemini-2.0-flash`.

**Resolution:**
- Created diagnostic script (`scripts/diagnose_gemini.py`) to test available models
- Updated `CloudBrain` to use `gemini-2.0-flash` as default model
- Updated all test scripts to use correct model name

**Status:** ✅ Resolved. All code now uses `gemini-2.0-flash`.

#### 8. Conversation History Format for Function Calling

**Problem:** `400 Bad Request` errors when Gemini tried to process tool results in multi-turn conversations.

**Root Cause:** Incorrect conversation history format when sending function responses back to Gemini. The API expects a specific format for multi-turn function calling.

**Resolution:**
- Refactored `CloudBrain.think_with_history()` to maintain full conversation history
- Fixed conversation history format to include:
  - User queries
  - Model function calls
  - User function responses (tool results)
- Updated `Orchestrator._think_with_tools()` to correctly format and send conversation history

**Status:** ✅ Resolved. Multi-turn tool execution now works correctly.

### Development Issues

#### 9. Router Not Routing Tool Queries to Cloud

**Problem:** Simple tool-requiring queries (e.g., "What's the weather?") were being routed to local brain, which doesn't support function calling.

**Root Cause:** Router wasn't recognizing tool-requiring queries. Local LLM (Llama 3.2 3B) doesn't support function calling, so all tool queries must go to cloud.

**Resolution:**
- Added `TOOL_KEYWORDS` to router for detecting tool-requiring queries
- Added `route_tools_to_cloud` parameter (default: `True`)
- Updated router to route all tool queries to cloud
- Added search-related keywords to ensure Wikipedia/ArXiv/Web queries route to cloud

**Status:** ✅ Resolved. All tool-requiring queries are now correctly routed to cloud.

## Known Limitations

1. **Wikipedia Disambiguation:** Simple planet names (e.g., "Mars") may hit disambiguation. Use specific names like "Mars (planet)" for best results.

2. **Local LLM Function Calling:** Llama 3.2 3B doesn't support function calling, so all tool queries must use cloud (Gemini 2.0 Flash).

3. **Weather API Key:** Optional but required for weather tool functionality. Tool gracefully reports when API key is missing.

4. **DuckDuckGo Rate Limits:** DuckDuckGo enforces strict rate limits. If you encounter "rate limit exceeded" errors:
   - Wait a few minutes between searches
   - Use the HackerNews tool (`get_tech_news`) for tech news instead
   - The tool automatically retries up to 3 times with exponential backoff (2s, 4s, 6s delays)

## Testing

### Automated Tests

The project includes comprehensive automated tests:

- **Unit Tests:** `tests/test_<module_name>.py` - Test individual components
- **Integration Tests:** `tests/test_integration.py` - Test component interactions
- **Regression Tests:** Located in `TestRegressions` classes within test files
- **UAT Tests:** `tests/test_uat_rag.py` - Real-world scenario testing

Run all tests:
```bash
source venv/bin/activate
python -m pytest tests/ -v
```

### Regression Test Standards

When fixing bugs, regression tests are **MANDATORY**:
- Test must reproduce the original bug scenario
- Include detailed docstring explaining what broke, why, and how the test prevents it
- Reference the Experiment # where the bug was discovered
- Located in `TestRegressions` classes within test files

Example: `test_chunking_stride_bug_regression()` prevents the RAG chunking infinite loop bug from reappearing.

### Manual Testing

See `MANUAL_TEST_PROMPTS.md` for example prompts to test each tool.

## Contributing

When adding new tools or features:
1. Follow the coding standards in `.cursorrules`
2. Check hardware constraints in `.cursor/notepads/technical_specs.md`
3. Update this README with any new issues/resolutions
4. Test tools through the orchestrator, not just directly

