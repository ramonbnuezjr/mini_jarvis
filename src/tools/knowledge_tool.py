"""Knowledge tools: Wikipedia and ArXiv for information retrieval."""

import logging
from typing import Dict, Any, Optional
from src.tools.base_tool import Tool

logger = logging.getLogger(__name__)


class WikipediaTool(Tool):
    """
    Tool for searching and retrieving Wikipedia articles.
    
    Uses the wikipedia library for article summaries and content.
    """
    
    def __init__(self):
        """Initialize Wikipedia tool."""
        super().__init__(
            name="search_wikipedia",
            description="Search Wikipedia and get article summaries (default: 10 sentences, max: 20). For planet queries, use specific names like 'Mars (planet)' or 'Jupiter (planet)' to avoid disambiguation. Useful for general knowledge, historical facts, and explanations of concepts."
        )
        
    def _get_parameters(self) -> Dict[str, Any]:
        """Get parameter schema for Wikipedia tool."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query or article title to look up on Wikipedia"
                },
                "sentences": {
                    "type": "integer",
                    "description": "Number of sentences to return in summary (default: 10, max: 20). Use more sentences for detailed questions.",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 20
                }
            },
            "required": ["query"]
        }
        
    async def execute(
        self,
        query: str,
        sentences: int = 10
    ) -> Dict[str, Any]:
        """
        Search Wikipedia and get article summary.
        
        Args:
            query: Search query or article title
            sentences: Number of sentences in summary (1-20, default: 10)
            
        Returns:
            Dict with Wikipedia article information
        """
        try:
            import wikipedia
        except ImportError:
            return {
                "result": "Wikipedia library not installed. Install with: pip install wikipedia",
                "error": "LIBRARY_MISSING"
            }
        
        try:
            # Set language (optional, defaults to English)
            wikipedia.set_lang("en")
            
            # Try using summary directly first (handles disambiguation better)
            try:
                summary = wikipedia.summary(query, sentences=sentences, auto_suggest=True)
                # Get the page to get title and URL
                page = wikipedia.page(query, auto_suggest=True)
            except wikipedia.exceptions.DisambiguationError as e:
                # Handle disambiguation
                disambiguation_options = e.options
                
                # For planet queries, look for planet in options
                planet_names = ["mars", "jupiter", "saturn", "venus", "mercury", "neptune", "uranus", "earth", "pluto"]
                query_lower = query.lower().strip()
                is_planet_query = query_lower in planet_names or "planet" in query_lower
                
                if is_planet_query:
                    # Look for exact planet name match first
                    for option in disambiguation_options:
                        if option.lower() == query_lower:
                            try:
                                summary = wikipedia.summary(option, sentences=sentences, auto_suggest=False)
                                page = wikipedia.page(option, auto_suggest=False)
                                break
                            except:
                                continue
                    else:
                        # If no exact match, look for "planet" in option
                        for option in disambiguation_options:
                            if "planet" in option.lower():
                                try:
                                    summary = wikipedia.summary(option, sentences=sentences, auto_suggest=False)
                                    page = wikipedia.page(option, auto_suggest=False)
                                    break
                                except:
                                    continue
                        else:
                            # Use first option as fallback
                            if disambiguation_options:
                                summary = wikipedia.summary(disambiguation_options[0], sentences=sentences, auto_suggest=False)
                                page = wikipedia.page(disambiguation_options[0], auto_suggest=False)
                            else:
                                raise
                else:
                    # For non-planet queries, use first option
                    if disambiguation_options:
                        summary = wikipedia.summary(disambiguation_options[0], sentences=sentences, auto_suggest=False)
                        page = wikipedia.page(disambiguation_options[0], auto_suggest=False)
                    else:
                        raise
            except wikipedia.exceptions.PageError:
                # If page lookup fails, try search
                search_results = wikipedia.search(query, results=5)
                if not search_results:
                    return {
                        "result": f"No Wikipedia article found for '{query}'",
                        "error": "NOT_FOUND"
                    }
                summary = wikipedia.summary(search_results[0], sentences=sentences, auto_suggest=False)
                page = wikipedia.page(search_results[0], auto_suggest=False)
            
            result = {
                "title": page.title,
                "summary": summary,
                "url": page.url,
                "sentences_returned": sentences
            }
            
            return {"result": result}
            
        except wikipedia.exceptions.DisambiguationError as e:
            # Handle disambiguation pages that we couldn't auto-resolve
            options = e.options[:5]  # Limit to 5 options
            return {
                "result": f"Multiple articles found for '{query}'. Please be more specific. Options: {', '.join(options)}",
                "error": "DISAMBIGUATION",
                "options": options
            }
        except wikipedia.exceptions.PageError:
            return {
                "result": f"Wikipedia page '{query}' does not exist",
                "error": "PAGE_NOT_FOUND"
            }
        except Exception as e:
            logger.error(f"Wikipedia tool error: {e}")
            return {
                "result": f"Error searching Wikipedia: {str(e)}",
                "error": "UNKNOWN_ERROR"
            }


class ArxivTool(Tool):
    """
    Tool for searching and retrieving scientific papers from arXiv.
    
    Uses the arxiv library to find and retrieve paper metadata and summaries.
    """
    
    def __init__(self):
        """Initialize ArXiv tool."""
        super().__init__(
            name="search_arxiv",
            description="Search arXiv for scientific papers. Returns paper titles, authors, abstracts, and links. Useful for finding recent research on specific topics."
        )
        
    def _get_parameters(self) -> Dict[str, Any]:
        """Get parameter schema for ArXiv tool."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (keywords, author names, or paper titles)"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default: 5, max: 20)",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 20
                },
                "sort_by": {
                    "type": "string",
                    "enum": ["relevance", "lastUpdatedDate", "submittedDate"],
                    "description": "Sort order: 'relevance' (default), 'lastUpdatedDate', or 'submittedDate'",
                    "default": "relevance"
                }
            },
            "required": ["query"]
        }
        
    async def execute(
        self,
        query: str,
        max_results: int = 5,
        sort_by: str = "relevance"
    ) -> Dict[str, Any]:
        """
        Search arXiv for scientific papers.
        
        Args:
            query: Search query
            max_results: Maximum number of results (1-20)
            sort_by: Sort order
            
        Returns:
            Dict with paper information
        """
        try:
            import arxiv
            
            # Map sort_by to arxiv sort order
            sort_map = {
                "relevance": arxiv.SortCriterion.Relevance,
                "lastUpdatedDate": arxiv.SortCriterion.LastUpdatedDate,
                "submittedDate": arxiv.SortCriterion.SubmittedDate
            }
            sort_criterion = sort_map.get(sort_by, arxiv.SortCriterion.Relevance)
            
            # Search arXiv
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=sort_criterion
            )
            
            papers = []
            for paper in search.results():
                papers.append({
                    "title": paper.title,
                    "authors": [author.name for author in paper.authors],
                    "abstract": paper.summary[:500] + "..." if len(paper.summary) > 500 else paper.summary,
                    "published": paper.published.strftime("%Y-%m-%d"),
                    "arxiv_id": paper.entry_id.split("/")[-1],
                    "url": paper.entry_id,
                    "categories": paper.categories
                })
            
            if not papers:
                return {
                    "result": f"No papers found for query '{query}'",
                    "error": "NO_RESULTS"
                }
            
            result = {
                "query": query,
                "count": len(papers),
                "papers": papers
            }
            
            return {"result": result}
            
        except ImportError:
            return {
                "result": "ArXiv library not installed. Install with: pip install arxiv",
                "error": "LIBRARY_MISSING"
            }
        except Exception as e:
            logger.error(f"ArXiv tool error: {e}")
            return {
                "result": f"Error searching arXiv: {str(e)}",
                "error": "UNKNOWN_ERROR"
            }

