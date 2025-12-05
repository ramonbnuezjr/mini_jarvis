"""Search tools: DuckDuckGo and HackerNews for live web results."""

import logging
import httpx
import asyncio
import warnings
from typing import Dict, Any, List
from src.tools.base_tool import Tool

logger = logging.getLogger(__name__)

# Suppress deprecation warnings for duckduckgo_search
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*duckduckgo_search.*")


class DuckDuckGoTool(Tool):
    """
    Tool for searching the web using DuckDuckGo.
    
    Uses duckduckgo-search library for privacy-focused web search.
    No API key required.
    """
    
    def __init__(self):
        """Initialize DuckDuckGo tool."""
        super().__init__(
            name="search_web",
            description="Search the web using DuckDuckGo. Returns search results with titles, snippets, and URLs. For news queries, use search_news instead. Useful for finding current information, news, and general web content."
        )
        
    def _get_parameters(self) -> Dict[str, Any]:
        """Get parameter schema for DuckDuckGo tool."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default: 10, max: 20)",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 20
                },
                "search_type": {
                    "type": "string",
                    "enum": ["text", "news"],
                    "description": "Search type: 'text' for general web search (default), 'news' for news articles",
                    "default": "text"
                }
            },
            "required": ["query"]
        }
        
    async def execute(
        self,
        query: str,
        max_results: int = 10,
        search_type: str = "text"
    ) -> Dict[str, Any]:
        """
        Search the web using DuckDuckGo.
        
        Args:
            query: Search query
            max_results: Maximum number of results (1-20)
            search_type: "text" for general search, "news" for news articles
            
        Returns:
            Dict with search results
        """
        try:
            # Try new package name first, fall back to old one
            try:
                from ddgs import DDGS
            except ImportError:
                from duckduckgo_search import DDGS
            
            # Add retry logic for rate limits
            max_retries = 3
            retry_delay = 2  # seconds
            results = None
            
            for attempt in range(max_retries):
                try:
                    with DDGS() as ddgs:
                        # Use news search if requested or if query contains "news" or "latest"
                        if search_type == "news" or any(word in query.lower() for word in ["news", "latest", "recent", "breaking"]):
                            results = list(ddgs.news(
                                query,
                                max_results=max_results
                            ))
                        else:
                            results = list(ddgs.text(
                                query,
                                max_results=max_results
                            ))
                    # Success - break out of retry loop
                    break
                except Exception as e:
                    error_str = str(e)
                    # Check if it's a rate limit error
                    if "202" in error_str or "Ratelimit" in error_str or "rate limit" in error_str.lower():
                        if attempt < max_retries - 1:
                            wait_time = retry_delay * (attempt + 1)  # Exponential backoff
                            logger.warning(f"DuckDuckGo rate limit hit, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            # Last attempt failed
                            return {
                                "result": "DuckDuckGo rate limit exceeded. Please try again in a few minutes. You can also try using the HackerNews news tool instead.",
                                "error": "RATE_LIMIT"
                            }
                    else:
                        # Not a rate limit error, re-raise
                        raise
            
            # If we exhausted retries without getting results
            if results is None:
                return {
                    "result": "Failed to get search results after multiple attempts.",
                    "error": "RETRY_EXHAUSTED"
                }
            
            if not results:
                return {
                    "result": f"No results found for query '{query}'",
                    "error": "NO_RESULTS"
                }
            
            # Format results (handle both text and news result formats)
            formatted_results = []
            for r in results[:max_results]:
                # News results have different structure
                if search_type == "news" or "date" in r:
                    formatted_results.append({
                        "title": r.get("title", ""),
                        "snippet": r.get("body", "") or r.get("snippet", ""),
                        "url": r.get("url", "") or r.get("href", ""),
                        "date": r.get("date", "")
                    })
                else:
                    formatted_results.append({
                        "title": r.get("title", ""),
                        "snippet": r.get("body", ""),
                        "url": r.get("href", "")
                    })
            
            result = {
                "query": query,
                "search_type": search_type,
                "count": len(formatted_results),
                "results": formatted_results
            }
            
            return {"result": result}
            
        except ImportError:
            return {
                "result": "DuckDuckGo search library not installed. Install with: pip install duckduckgo-search",
                "error": "LIBRARY_MISSING"
            }
        except Exception as e:
            logger.error(f"DuckDuckGo tool error: {e}")
            return {
                "result": f"Error searching web: {str(e)}",
                "error": "UNKNOWN_ERROR"
            }


class NewsTool(Tool):
    """
    Tool for getting tech news headlines from HackerNews.
    
    Uses HackerNews API (no API key required).
    """
    
    def __init__(self):
        """Initialize News tool."""
        super().__init__(
            name="get_tech_news",
            description="Get top tech news headlines from HackerNews. Returns article titles, URLs, scores, and comments. Useful for staying updated on tech trends."
        )
        
    def _get_parameters(self) -> Dict[str, Any]:
        """Get parameter schema for News tool."""
        return {
            "type": "object",
            "properties": {
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of headlines to return (default: 10, max: 30)",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 30
                },
                "category": {
                    "type": "string",
                    "enum": ["top", "new", "best"],
                    "description": "Story category: 'top' (default), 'new', or 'best'",
                    "default": "top"
                }
            },
            "required": []
        }
        
    async def execute(
        self,
        max_results: int = 10,
        category: str = "top"
    ) -> Dict[str, Any]:
        """
        Get tech news from HackerNews.
        
        Args:
            max_results: Maximum number of headlines (1-30)
            category: Story category (top/new/best)
            
        Returns:
            Dict with news headlines
        """
        try:
            import httpx
            
            # HackerNews API endpoints
            category_map = {
                "top": "topstories",
                "new": "newstories",
                "best": "beststories"
            }
            endpoint = category_map.get(category, "topstories")
            
            base_url = "https://hacker-news.firebaseio.com/v0"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Get story IDs
                response = await client.get(f"{base_url}/{endpoint}.json")
                response.raise_for_status()
                story_ids = response.json()[:max_results]
                
                # Get story details
                stories = []
                for story_id in story_ids:
                    story_response = await client.get(
                        f"{base_url}/item/{story_id}.json"
                    )
                    story_response.raise_for_status()
                    story = story_response.json()
                    
                    if story and story.get("type") == "story":
                        stories.append({
                            "title": story.get("title", ""),
                            "url": story.get("url", ""),
                            "score": story.get("score", 0),
                            "comments": story.get("descendants", 0),
                            "author": story.get("by", ""),
                            "time": story.get("time", 0)  # Unix timestamp
                        })
            
            if not stories:
                return {
                    "result": "No news stories found",
                    "error": "NO_RESULTS"
                }
            
            result = {
                "category": category,
                "count": len(stories),
                "stories": stories
            }
            
            return {"result": result}
            
        except httpx.HTTPError as e:
            logger.error(f"HackerNews API error: {e}")
            return {
                "result": f"Failed to fetch news: {str(e)}",
                "error": "API_ERROR"
            }
        except Exception as e:
            logger.error(f"News tool error: {e}")
            return {
                "result": f"Error getting news: {str(e)}",
                "error": "UNKNOWN_ERROR"
            }

