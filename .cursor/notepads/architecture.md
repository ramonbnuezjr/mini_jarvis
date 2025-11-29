# System Architecture: Mini-JARVIS

## Core Philosophy

Hybrid Intelligence: Local speed for wake/basic tasks + Cloud power for complex reasoning/vision.

## Main Components

1. **Senses (Input Loop)**

   - **Ears:** USB Mic → VAD (Voice Activity Detection) → STT (Whisper).

   - **Eyes:** Pi Camera 3 → Frame Capture → Local Object Detect (YOLO) or Cloud Vision.

2. **The Brain (Orchestrator)** ✅ **IMPLEMENTED**

   - **Router:** Decides "Local vs. Cloud" based on complexity, context size, and tool requirements.

   - **Local LLM:** Ollama with Llama 3.2 3B for fast, capable chat. If Llama 3.2 3B is insufficient (e.g., complex medical analysis), burst to cloud rather than upgrading to slower local 7B+ models.

   - **Cloud Burst:** Google Gemini 2.0 Flash API for deep reasoning when local model is insufficient. Handles complex queries, large contexts, and prepares for tool-use capabilities.

3. **Memory & Tools**

   - **RAG Server:** Vector DB for long-term memory retrieval.

   - **MCP Server:** Handles tool execution (Calendar, Weather, Home Automation).

4. **Expression (Output)**

   - **Voice:** Text-to-Speech (TTS) → Speaker.

