# System Architecture: Mini-JARVIS

## Core Philosophy

Hybrid Intelligence: Local speed for wake/basic tasks + Cloud power for complex reasoning/vision.

## Development Phases

### ✅ Phase 1: Local Brain (IMPLEMENTED)
- Ollama with Llama 3.2 3B for fast, private inference
- Handles simple queries and basic tasks

### ✅ Phase 2: Cloud Burst (IMPLEMENTED)
- Google Gemini 2.0 Flash API for complex reasoning
- Automatic routing based on query complexity
- Orchestrator coordinates Local and Cloud brains

### ✅ Phase 3: Agentic Layer (Tools & MCP Server) - **IMPLEMENTED**
- **MCP Server:** Tool Registry and Executor for managing and executing tools
- **6 Tools Integrated:**
  - Weather Tool (OpenWeatherMap API)
  - Time/Date Tool (local system time)
  - Wikipedia Search Tool
  - ArXiv Research Paper Search Tool
  - DuckDuckGo Web Search Tool (with news search support)
  - HackerNews Tech News Tool
- **Function Calling:** Gemini 2.0 Flash can invoke tools automatically
- **Multi-turn Tool Execution:** Supports iterative tool use in conversations
- **Why first?** To give JARVIS real-time data (Weather, Time) immediately.
- Enables practical utility before deep knowledge

### 📋 Phase 4: RAG Pipeline (Long-term Memory)
- **RAG Server:** Vector DB for long-term memory retrieval
- Document ingestion and embedding
- Context-aware conversations
- **Why later?** Deep knowledge is less urgent than basic utility.

### 📋 Phase 5: Voice/Vision Integration (STT/TTS/VLM)
- **Ears:** USB Mic → VAD (Voice Activity Detection) → STT (Whisper)
- **Eyes:** Pi Camera 3 → Frame Capture → Local Object Detect (YOLO) or Cloud Vision
- **Voice:** Text-to-Speech (TTS) → Speaker

## Main Components

1. **The Brain (Orchestrator)** ✅ **IMPLEMENTED**

   - **Router:** Decides "Local vs. Cloud" based on complexity, context size, and tool requirements.

   - **Local LLM:** Ollama with Llama 3.2 3B for fast, capable chat. If Llama 3.2 3B is insufficient (e.g., complex medical analysis), burst to cloud rather than upgrading to slower local 7B+ models.

   - **Cloud Burst:** Google Gemini 2.0 Flash API for deep reasoning when local model is insufficient. Handles complex queries, large contexts, and prepares for tool-use capabilities.

2. **Agentic Layer (Tools & MCP Server)** ✅ **IMPLEMENTED**

   - **Tool Registry:** MCP-like server for managing and executing tools
   - **Tool Executor:** Handles function calling and tool execution from LLM
   - **6 Tools:** Weather, Time, Wikipedia, ArXiv, DuckDuckGo, HackerNews
   - Real-time data access (Weather API, Time/Date, Web Search, News)
   - Multi-turn tool execution support
   - Automatic tool invocation based on user queries

3. **Memory & Tools** 📋 **PHASE 4**

   - **RAG Server:** Vector DB for long-term memory retrieval.
   - Document embedding and retrieval
   - Context-aware conversations

4. **Senses & Expression** 📋 **PHASE 5**

   - **Ears:** USB Mic → VAD (Voice Activity Detection) → STT (Whisper).
   - **Eyes:** Pi Camera 3 → Frame Capture → Local Object Detect (YOLO) or Cloud Vision.
   - **Voice:** Text-to-Speech (TTS) → Speaker.

