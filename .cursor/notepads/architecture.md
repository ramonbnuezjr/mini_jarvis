# System Architecture: Mini-JARVIS

## Core Philosophy

Hybrid Intelligence: Local speed for wake/basic tasks + Cloud power for complex reasoning/vision.

## Development Phases

### ✅ Phase 1: Local Brain (IMPLEMENTED)
- Ollama with Llama 3.2 3B for fast, private inference
- Handles simple queries and basic tasks

### ✅ Phase 2: Cloud Burst (IMPLEMENTED)
- Ollama Cloud with gpt-oss:120b-cloud for complex reasoning (hybrid pattern)
- Local Ollama gateway - single endpoint for local and cloud models
- Automatic routing based on query complexity
- Orchestrator coordinates Local and Cloud brains
- Authentication via `ollama signin` (no API keys in code)

### ✅ Phase 3: Agentic Layer (Tools & MCP Server) - **IMPLEMENTED**
- **MCP Server:** Tool Registry and Executor for managing and executing tools
- **6 Tools Integrated:**
  - Weather Tool (OpenWeatherMap API)
  - Time/Date Tool (local system time)
  - Wikipedia Search Tool
  - ArXiv Research Paper Search Tool
  - DuckDuckGo Web Search Tool (with news search support)
  - HackerNews Tech News Tool
   - **Function Calling:** Ollama Cloud (gpt-oss:120b-cloud) can invoke tools automatically with OpenAI-compatible format
- **Multi-turn Tool Execution:** Supports iterative tool use in conversations
- **Why first?** To give JARVIS real-time data (Weather, Time) immediately.
- Enables practical utility before deep knowledge

### ✅ Phase 4: RAG Pipeline (Long-term Memory) - **IMPLEMENTED**
- **RAG Server:** ChromaDB vector database for long-term memory retrieval
- **Document Ingestion:** Support for text (.txt), markdown (.md), and PDF (.pdf) files
- **Embedding System:** Local embeddings (sentence-transformers/all-MiniLM-L6-v2) with API fallback
- **Context Retrieval:** Semantic search with top-k chunk retrieval
- **Integration:** Automatic RAG context injection into queries via Orchestrator
- **Storage:** Persistent vector database on NVMe at `~/.jarvis/memory`

### ✅ Phase 4.5: RAG Memory Tiering (Refinement) - **IMPLEMENTED & UAT PASSED**
- **Tiered Storage:** Three-tier memory architecture (core/reference/ephemeral)
  - **Core:** Important, permanent documents (1.5x retrieval boost)
  - **Reference:** Standard documents (normal weight)
  - **Ephemeral:** Temporary documents (0.7x weight, TTL-based expiry)
- **Metadata Tracking:** SQLite database for version hashing, TTL, and access patterns
- **Weighted Retrieval:** Tier-based score boosting in semantic search
- **Automatic Cleanup:** TTL-based expiry for ephemeral documents
- **Backward Compatible:** Single collection mode still supported
- **Testing:** Comprehensive automated tests and UAT completed successfully

### ✅ Phase 4.6: Google Drive Sync (Cloud Integration) - **IMPLEMENTED**
- **OAuth 2.0 Authentication:** Secure authentication with Google Drive API
- **Folder-to-Tier Mapping:** Automatic mapping of Google Drive folders to RAG tiers:
  - `JARVIS-Core/` → core tier (1.5x retrieval boost, permanent)
  - `JARVIS-Reference/` → reference tier (1.0x normal weight, permanent)
  - `JARVIS-Ephemeral/` → ephemeral tier (0.7x weight, 30-day TTL)
- **Incremental Sync:** Only downloads and ingests changed files (tracks hashes and modification times)
- **Version Hash Tracking:** SHA256 hash tracking for detecting content changes
- **Google Docs Support:** Exports Google Docs, Sheets, and Slides as text
- **Recursive Scanning:** Scans subfolders recursively
- **Sync State Persistence:** Maintains sync state for efficient updates
- **Integration:** Seamlessly integrates with tiered RAG memory system

### 📋 Phase 5: Voice/Vision Integration (STT/TTS/VLM)
- **Ears:** USB Mic → VAD (Voice Activity Detection) → STT (Whisper)
- **Eyes:** Pi Camera 3 → Frame Capture → Local Object Detect (YOLO) or Cloud Vision
- **Voice:** Text-to-Speech (TTS) → Speaker

## Main Components

1. **The Brain (Orchestrator)** ✅ **IMPLEMENTED**

   - **Router:** Decides "Local vs. Cloud" based on complexity, context size, and tool requirements.

   - **Local LLM:** Ollama with Llama 3.2 3B for fast, capable chat. If Llama 3.2 3B is insufficient (e.g., complex medical analysis), burst to cloud rather than upgrading to slower local 7B+ models.

   - **Cloud Burst:** Ollama Cloud with gpt-oss:120b-cloud for deep reasoning when local model is insufficient. Uses hybrid pattern - local Ollama gateway with automatic cloud offloading. Handles complex queries, large contexts (128K), and native tool calling.

2. **Agentic Layer (Tools & MCP Server)** ✅ **IMPLEMENTED**

   - **Tool Registry:** MCP-like server for managing and executing tools
   - **Tool Executor:** Handles function calling and tool execution from LLM
   - **6 Tools:** Weather, Time, Wikipedia, ArXiv, DuckDuckGo, HackerNews
   - Real-time data access (Weather API, Time/Date, Web Search, News)
   - Multi-turn tool execution support
   - Automatic tool invocation based on user queries

3. **Memory & RAG Pipeline** ✅ **IMPLEMENTED**

   - **RAG Server:** ChromaDB vector database for long-term memory retrieval
   - **Tiered Memory:** Three-tier architecture (core/reference/ephemeral) with weighted retrieval
   - **Metadata Tracker:** SQLite-based tracking for version hashing, TTL, and access patterns
   - **Document Ingestion:** Automatic chunking and embedding of documents (text, markdown, PDF, Google Docs)
   - **Semantic Search:** Top-k retrieval with tier-based weighted scoring
   - **Context Injection:** Automatic RAG context enhancement with proper system prompt formatting
   - **Local Embeddings:** CPU-friendly sentence-transformers model (384 dimensions)
   - **Automatic Cleanup:** TTL-based expiry for ephemeral documents
   - **Google Drive Sync:** Automatic synchronization of Google Drive folders to RAG tiers with incremental updates

4. **Senses & Expression** 📋 **PHASE 5**

   - **Ears:** USB Mic → VAD (Voice Activity Detection) → STT (Whisper).
   - **Eyes:** Pi Camera 3 → Frame Capture → Local Object Detect (YOLO) or Cloud Vision.
   - **Voice:** Text-to-Speech (TTS) → Speaker.

