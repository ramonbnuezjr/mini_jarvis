# Migration: Gemini 2.0 Flash → Ollama Cloud (Hybrid Pattern)

## Overview

Mini-JARVIS has been migrated from Google Gemini 2.0 Flash API to Ollama Cloud using the **hybrid pattern**: local Ollama gateway with cloud model offloading.

## Why Migrate?

- **Flat-fee pricing**: More predictable costs
- **Native tool calling**: OpenAI-compatible function calling format
- **128K context window**: Better support for large RAG contexts
- **Hybrid pattern**: Single endpoint for local and cloud models
- **No API keys in code**: Authentication handled by `ollama signin`
- **Simplified architecture**: Router chooses model name, not provider

## The Hybrid Pattern

Instead of calling Ollama Cloud API directly, we use **local Ollama as the gateway**:

1. **Local Ollama Gateway**: All code talks to `http://localhost:11434`
2. **Cloud Model Access**: Pull cloud models via `ollama pull gpt-oss:120b-cloud`
3. **Automatic Offloading**: Ollama automatically offloads cloud models to Ollama Cloud infrastructure
4. **Single Authentication**: One-time `ollama signin` handles all authentication

**Benefits:**
- No API keys in code (more secure)
- Single endpoint for all models
- Same API format everywhere (OpenAI-compatible)
- Router just chooses model name, not provider

## Changes Made

### 1. Environment Configuration

**Removed:**
- `GEMINI_API_KEY`
- `OLLAMA_CLOUD_API_KEY` (no longer needed)
- `OLLAMA_CLOUD_BASE_URL` (no longer needed)

**Updated:**
- `OLLAMA_CLOUD_MODEL` - Model name (default: `gpt-oss:120b-cloud`)
- `OLLAMA_BASE_URL` - Now used for both local and cloud (default: `http://localhost:11434`)

### 2. Core Files Updated

#### `src/brain/cloud_brain.py`
- **Complete refactor** to use local Ollama gateway
- Removed API key requirement - authentication handled by `ollama signin`
- Uses same base URL as `LocalBrain` (`http://localhost:11434`)
- Uses OpenAI-compatible endpoint (`/v1/chat/completions`)
- Cloud models accessed via model name (e.g., `gpt-oss:120b-cloud`)

#### `src/brain/orchestrator.py`
- Updated to use `OLLAMA_CLOUD_MODEL` environment variable
- Converted tool schemas from Gemini format to OpenAI format
- Maintained backward compatibility with conversation history format

#### `src/brain/router.py`
- Updated comments to reflect Ollama Cloud instead of Gemini
- Router logic unchanged - still chooses local vs cloud based on complexity

### 3. Scripts Updated

- `scripts/chat.py` - Updated error messages
- `scripts/test_cloud_burst.py` - Updated test descriptions
- `scripts/test_chat_with_rag.py` - Updated error messages
- `scripts/test_query.py` - Updated error messages
- `scripts/test_tool_prompts.py` - Updated error messages
- `scripts/setup.sh` - Updated .env template
- `scripts/setup_ollama_cloud.sh` - New setup script for Ollama Cloud
- `scripts/test_hybrid_ollama.py` - New test script for hybrid pattern

### 4. Documentation Updated

- `README.md` - Updated setup instructions and architecture
- `CHANGELOG.md` - Added migration entry
- `MIGRATION_OLLAMA_CLOUD.md` - This document

## Migration Steps for Users

### 1. Update `.env` File

Remove old Gemini/Ollama Cloud API keys:
```bash
# Remove these lines:
# GEMINI_API_KEY=...
# OLLAMA_CLOUD_API_KEY=...
# OLLAMA_CLOUD_BASE_URL=...
```

Keep/update:
```bash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CLOUD_MODEL=gpt-oss:120b-cloud
```

### 2. Setup Ollama Cloud (One-Time)

1. **Sign in to Ollama Cloud**:
   ```bash
   ollama signin
   ```
   This opens a browser to authenticate. No API key needed!

2. **Pull the cloud model**:
   ```bash
   ollama pull gpt-oss:120b-cloud
   ```
   This downloads model metadata. The model runs on Ollama Cloud automatically.

### 3. Test the Migration

```bash
# Test hybrid setup
python scripts/test_hybrid_ollama.py

# Test Cloud Burst
python scripts/test_cloud_burst.py

# Test tools
python scripts/test_tools_live.py

# Test with RAG
python scripts/test_chat_with_rag.py
```

## How the Hybrid Pattern Works

### Architecture

```
┌─────────────────┐
│  Your Code      │
│  (Python)       │
└────────┬────────┘
         │
         │ HTTP requests to localhost:11434
         │
┌────────▼────────┐
│  Local Ollama   │
│  Gateway        │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌───▼──────────┐
│ Local │ │ Cloud Model  │
│ Model │ │ (gpt-oss:    │
│       │ │  120b-cloud) │
└───────┘ └───┬──────────┘
              │
              │ Auto-offloads to
              │ Ollama Cloud
              │
       ┌──────▼──────┐
       │ Ollama Cloud│
       │ Infrastructure│
       └─────────────┘
```

### Code Example

```python
# Before (Gemini):
cloud_brain = CloudBrain(api_key="...")  # Required API key

# After (Hybrid Pattern):
cloud_brain = CloudBrain()  # No API key needed!
# Uses local Ollama gateway
# Authentication handled by 'ollama signin'
```

### Router Logic

```python
# Router chooses model name, not provider
if complex_query:
    model = "gpt-oss:120b-cloud"  # Cloud model
else:
    model = "llama3.2:3b"  # Local model

# Both use same endpoint: http://localhost:11434
```

## API Format Changes

### Function Calling Format

**Before (Gemini):**
```json
{
  "functionCall": {
    "name": "get_weather",
    "args": {"location": "London"}
  }
}
```

**After (OpenAI/Ollama):**
```json
{
  "tool_calls": [{
    "id": "call_123",
    "type": "function",
    "function": {
      "name": "get_weather",
      "arguments": "{\"location\": \"London\"}"
    }
  }]
}
```

### Conversation History

The orchestrator maintains backward compatibility by converting between formats internally. The `CloudBrain` class handles conversion automatically.

## Backward Compatibility

- **Tool schemas**: Automatically converted from Gemini format to OpenAI format
- **Conversation history**: Automatically converted between formats
- **Function call parsing**: Still works with existing `ToolExecutor`
- **RAG context**: No changes needed, works as before
- **Router logic**: Unchanged - still routes based on complexity

## Testing Checklist

- [x] Cloud Brain initialization (no API key required)
- [x] Health check (local Ollama gateway)
- [x] Simple text generation
- [x] Function calling (tools)
- [x] Multi-turn conversations
- [x] RAG context injection
- [x] Router logic (local vs cloud)
- [x] Error handling
- [x] Regression tests (10/10 passed)

## Known Issues

None at this time. If you encounter issues, please check:

1. Ollama is running: `ollama serve`
2. You've signed in: `ollama signin`
3. Cloud model is pulled: `ollama pull gpt-oss:120b-cloud`
4. Model is listed: `ollama list | grep gpt-oss`

## Troubleshooting

### "401 Unauthorized" Error

**Solution:** Run `ollama signin` to authenticate with Ollama Cloud.

### "Model not found" Error

**Solution:** Run `ollama pull gpt-oss:120b-cloud` to download the model.

### "Cannot connect to Ollama" Error

**Solution:** Make sure Ollama is running: `ollama serve`

## Rollback

If you need to rollback to Gemini:

1. Restore `src/brain/cloud_brain.py` from git history
2. Restore `src/brain/orchestrator.py` from git history
3. Update `.env` to use `GEMINI_API_KEY` again
4. Restart the application

## Support

For issues or questions:
- Check the [Ollama Cloud documentation](https://docs.ollama.com/cloud)
- Review error logs in `logs/` directory
- Run diagnostic scripts: `python scripts/test_hybrid_ollama.py`
- Run regression tests: `pytest tests/test_cloud_brain_regression.py -v`

## Benefits Summary

✅ **No API keys in code** - More secure, no risk of committing secrets  
✅ **Single endpoint** - Simpler architecture, easier debugging  
✅ **Same API format** - Works with existing tools and integrations  
✅ **Automatic offloading** - Cloud models handled transparently  
✅ **Simplified router** - Just chooses model name, not provider  
✅ **Better pricing** - Flat-fee model vs per-token pricing  
