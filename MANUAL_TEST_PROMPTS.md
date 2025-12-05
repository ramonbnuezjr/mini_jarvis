# Manual Test Prompts for Mini-JARVIS Tools

Use these prompts to manually test each tool. Run the interactive chat script:

```bash
cd /home/ramon/ai_projects/mini_jarvis
source venv/bin/activate
python scripts/chat.py
```

## Test Prompts by Tool

### 1. Weather Tool (`get_weather`)
Test prompts that should trigger weather lookups:
- "What's the weather like in San Francisco?"
- "Tell me the temperature in New York City"
- "What's the forecast for London today?"
- "Is it raining in Seattle right now?"

**Expected behavior:** 
- Routes to Cloud (Gemini)
- Calls `get_weather` tool
- Returns weather information (or error if API key missing)

---

### 2. Time Tool (`get_time`)
Test prompts for time/date queries:
- "What time is it right now?"
- "What's the current date?"
- "What day is it today?"
- "Tell me today's date and time"

**Expected behavior:**
- Routes to Cloud (Gemini)
- Calls `get_time` tool
- Returns current date/time

---

### 3. Wikipedia Tool (`search_wikipedia`)
Test prompts for Wikipedia searches:
- "Search Wikipedia for information about Python programming"
- "Look up Albert Einstein on Wikipedia"
- "Find Wikipedia article about quantum computing"
- "What does Wikipedia say about the Raspberry Pi?"
- "Look up Mars (planet) on Wikipedia" (use specific names for planets)

**Expected behavior:**
- Routes to Cloud (Gemini)
- Calls `search_wikipedia` tool
- Returns Wikipedia article summary (default: 10 sentences, max: 20)

**Note:** For planet queries, use specific names like "Mars (planet)" to avoid disambiguation issues. Simple names like "Mars" may hit disambiguation.

---

### 4. ArXiv Tool (`search_arxiv`)
Test prompts for scientific paper searches:
- "Find recent research papers about machine learning on arXiv"
- "Search arXiv for papers on neural networks"
- "Look up papers about quantum computing on arXiv"
- "Find arXiv papers published about transformer models"

**Expected behavior:**
- Routes to Cloud (Gemini)
- Calls `search_arxiv` tool
- Returns list of research papers with abstracts

---

### 5. Web Search Tool (`search_web`)
Test prompts for web searches:
- "Search the web for the latest news about Raspberry Pi 5" (automatically uses news search)
- "Look up information about the latest Python 3.12 features"
- "Search the internet for recent developments in AI"
- "Find web results about the Raspberry Pi 5 specifications"
- "What are the breaking news about Raspberry Pi 5?" (uses news search)

**Expected behavior:**
- Routes to Cloud (Gemini)
- Calls `search_web` tool
- Automatically uses news search for queries with "news", "latest", "recent", "breaking"
- Returns web search results (default: 10 results, max: 20)
- Automatically retries on rate limits (up to 3 attempts with exponential backoff)

**Note:** If you encounter rate limit errors, wait a few minutes between searches or use the HackerNews tool for tech news.

---

### 6. Tech News Tool (`get_tech_news`)
Test prompts for tech news:
- "What are the top tech news stories today?"
- "Show me the latest tech headlines"
- "What's happening in tech news?"
- "Get me today's technology news"

**Expected behavior:**
- Routes to Cloud (Gemini)
- Calls `get_tech_news` tool
- Returns top tech news stories from HackerNews

---

## Advanced Test Scenarios

### Multi-Tool Queries
Test prompts that might use multiple tools:
- "What's the weather in San Francisco and what time is it there?"
- "Search Wikipedia for Python, then find recent papers about it on arXiv"

### Edge Cases
- "What's the weather?" (no location specified - should still work)
- "Search for something that doesn't exist" (test error handling)
- "Tell me about quantum computing" (might use Wikipedia or general knowledge)

---

## What to Look For

✅ **Success indicators:**
- Tool name appears in "🔧 Tools used: ..." output
- Response contains relevant information from the tool
- No errors in the response

⚠️ **Expected limitations:**
- Weather tool requires `OPENWEATHER_API_KEY` in `.env` (optional, tool reports when missing)
- Wikipedia disambiguation: Simple planet names may require specific queries (e.g., "Mars (planet)")
- Wikipedia/ArXiv may have rate limits
- **DuckDuckGo rate limits:** If you see "rate limit exceeded" errors, wait a few minutes between searches or use the HackerNews tool (`get_tech_news`) for tech news instead. The tool automatically retries up to 3 times with delays.

📝 **See [CHANGELOG.md](CHANGELOG.md) for detailed issue history and resolutions.**

---

## Quick Test Script

You can also test individual prompts programmatically:

```python
import asyncio
from src.brain.orchestrator import Orchestrator

async def test_prompt(prompt):
    async with Orchestrator() as orchestrator:
        response, target, tool_calls = await orchestrator.think(prompt)
        print(f"\nPrompt: {prompt}")
        print(f"Target: {target.value}")
        print(f"Tools: {[tc['tool'] for tc in tool_calls]}")
        print(f"Response: {response[:200]}...")

# Test a prompt
asyncio.run(test_prompt("What's the weather in San Francisco?"))
```

