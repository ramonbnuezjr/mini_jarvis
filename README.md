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
3. 📋 **Phase 4: RAG Pipeline** (Long-term Memory) - **NEXT**
4. 📋 **Phase 5: Voice/Vision Integration** (STT/TTS/VLM)

**Rationale:** Tools first to enable real-time data access (Weather, Time), then memory for context, then voice/vision for natural interaction.

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
│   └── tools/
│       ├── __init__.py
│       ├── base_tool.py      # Abstract base class for tools
│       ├── tool_registry.py  # Tool registry (MCP-like server)
│       ├── default_registry.py # Creates registry with all tools
│       ├── weather_tool.py    # Weather API tool
│       ├── time_tool.py       # Time/Date tool
│       ├── knowledge_tool.py # Wikipedia & ArXiv tools
│       └── search_tool.py    # DuckDuckGo & HackerNews tools
├── scripts/
│   ├── test_brain.py         # Test Local Brain
│   ├── test_cloud_burst.py   # Test Cloud Burst
│   ├── diagnose_gemini.py    # Diagnose Gemini API issues
│   ├── test_tools.py         # Test tool registry
│   ├── test_tool_prompts.py  # Test prompts that trigger tools
│   ├── test_tools_live.py    # Test tools through orchestrator
│   ├── chat.py               # Interactive chat interface
│   ├── setup.sh              # Automated setup script
│   └── check_setup.py        # Prerequisites checker
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
- ✅ **Interactive Chat**: Command-line interface for testing

## Current Status

### ✅ Implemented (Phase 1, 2 & 3)
- **Phase 1: Local Brain** - Ollama with Llama 3.2 3B for fast, private inference
- **Phase 2: Cloud Burst** - Gemini 2.0 Flash API for complex reasoning
- **Phase 3: Agentic Layer** - Tool system with 6 integrated tools:
  - ✅ Weather Tool (requires OpenWeatherMap API key)
  - ✅ Time/Date Tool
  - ✅ Wikipedia Search Tool
  - ✅ ArXiv Research Paper Search Tool
  - ✅ DuckDuckGo Web Search Tool
  - ✅ HackerNews Tech News Tool
- Smart Router (automatic local/cloud routing, routes tool queries to cloud)
- Orchestrator (seamless brain coordination with multi-turn tool execution)
- Tool Registry & Executor (MCP-like server for tool management)
- Interactive Chat Interface

### 🚧 Development Phases

#### Phase 4: RAG Pipeline (Long-term Memory) - **NEXT**
- [ ] Implement vector database (ChromaDB)
- [ ] Document ingestion and embedding
- [ ] Context retrieval system
- [ ] Long-term memory integration
- *Why later?* Deep knowledge is less urgent than basic utility.

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

#### 2. DuckDuckGo Web Search - Poor News Results

**Problem:** Web search wasn't returning good results for news queries like "latest news about Raspberry Pi 5".

**Root Cause:** General web search (`ddgs.text()`) isn't optimized for news queries. DuckDuckGo has a dedicated news search API.

**Resolution:**
- Added automatic news search detection (queries with "news", "latest", "recent", "breaking" use `ddgs.news()`)
- Increased default results from 5 to 10
- Improved query handling for news-specific searches

**Status:** ✅ Resolved. News queries now automatically use DuckDuckGo's news search API.

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

#### 4. DuckDuckGo Deprecation Warning

**Problem:** RuntimeWarning: `duckduckgo_search` package has been renamed to `ddgs`.

**Root Cause:** The `duckduckgo-search` package is being deprecated in favor of `ddgs`.

**Resolution:**
- Added code to try new package name (`ddgs`) first, fall back to old name
- Suppressed deprecation warnings when using old package
- Tool continues to work with either package name

**Status:** ✅ Resolved. Tool handles both package names gracefully.

#### 5. Weather API Key Configuration

**Problem:** Weather tool was reporting "API key missing" errors.

**Root Cause:** `OPENWEATHER_API_KEY` was not set in `.env` file.

**Resolution:**
- Added `OPENWEATHER_API_KEY` placeholder to `.env` file
- Updated README with instructions for getting free OpenWeatherMap API key
- Tool gracefully reports when API key is missing

**Status:** ✅ Resolved. API key configuration is documented and optional (tool reports when missing).

### API & Configuration Issues

#### 6. Gemini API Model Name Change

**Problem:** `404 Not Found` errors when calling Gemini API with `gemini-1.5-flash`.

**Root Cause:** Google updated the model name to `gemini-2.0-flash`.

**Resolution:**
- Created diagnostic script (`scripts/diagnose_gemini.py`) to test available models
- Updated `CloudBrain` to use `gemini-2.0-flash` as default model
- Updated all test scripts to use correct model name

**Status:** ✅ Resolved. All code now uses `gemini-2.0-flash`.

#### 7. Conversation History Format for Function Calling

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

#### 8. Router Not Routing Tool Queries to Cloud

**Problem:** Simple tool-requiring queries (e.g., "What's the weather?") were being routed to local brain, which doesn't support function calling.

**Root Cause:** Router wasn't recognizing tool-requiring queries. Local LLM (Llama 3.2 3B) doesn't support function calling, so all tool queries must go to cloud.

**Resolution:**
- Added `TOOL_KEYWORDS` to router for detecting tool-requiring queries
- Added `route_tools_to_cloud` parameter (default: `True`)
- Updated router to route all tool queries to cloud
- Added search-related keywords to ensure Wikipedia/ArXiv/Web queries route to cloud

**Status:** ✅ Resolved. All tool-requiring queries are now correctly routed to cloud.

## Testing

See `MANUAL_TEST_PROMPTS.md` for example prompts to test each tool.

## Contributing

When adding new tools or features:
1. Follow the coding standards in `.cursorrules`
2. Check hardware constraints in `.cursor/notepads/technical_specs.md`
3. Update this README with any new issues/resolutions
4. Test tools through the orchestrator, not just directly

