# Changelog

All notable changes, issues, and resolutions for Mini-JARVIS.

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

