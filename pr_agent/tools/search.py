"""
Web search tools for the PR agent.

Provides capabilities to search the internet for supporting data and media information.
"""

import os
import requests
from typing import List, Dict, Any, Optional
from langchain_core.tools import Tool
from langchain_community.utilities import GoogleSerperAPIWrapper


class WebSearchTool:
    """Tool for searching the internet for supporting data."""

    def __init__(self, api_key: Optional[str] = None, max_results: int = 5):
        """
        Initialize web search tool.

        Args:
            api_key: Serper API key (or set SERPER_API_KEY env var)
            max_results: Maximum number of search results to return
        """
        self.api_key = api_key or os.getenv("SERPER_API_KEY")
        self.max_results = max_results

        if self.api_key:
            self.search = GoogleSerperAPIWrapper(serper_api_key=self.api_key)
        else:
            self.search = None

    def search_for_data(self, query: str) -> List[Dict[str, Any]]:
        """
        Search the internet for data to support a comment.

        Args:
            query: Search query

        Returns:
            List of search results with title, link, snippet
        """
        if not self.search:
            return [{
                "title": "Search unavailable",
                "snippet": "Please configure SERPER_API_KEY to enable web search",
                "link": ""
            }]

        try:
            results = self.search.results(query)

            # Extract organic results
            organic = results.get("organic", [])[:self.max_results]

            return [{
                "title": r.get("title", ""),
                "snippet": r.get("snippet", ""),
                "link": r.get("link", ""),
                "position": r.get("position", 0)
            } for r in organic]

        except Exception as e:
            return [{
                "title": "Search error",
                "snippet": f"Error during search: {str(e)}",
                "link": ""
            }]

    def as_langchain_tool(self) -> Tool:
        """Convert to LangChain tool format."""
        return Tool(
            name="web_search",
            description="Search the internet for data, statistics, and information to support PR comments",
            func=lambda q: str(self.search_for_data(q))
        )


class MediaResearchTool:
    """Tool for researching media outlets and journalists."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize media research tool.

        Args:
            api_key: Serper API key (or set SERPER_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("SERPER_API_KEY")
        self.search = WebSearchTool(api_key=self.api_key, max_results=3)

    def research_media_outlet(self, media_name: str, journalist_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Research a media outlet and optionally a journalist.

        Args:
            media_name: Name of the media outlet
            journalist_name: Optional name of the journalist

        Returns:
            Dictionary with media research information
        """
        # Research the media outlet
        media_query = f"{media_name} media outlet focus topics audience"
        media_results = self.search.search_for_data(media_query)

        outlet_info = {
            "media_name": media_name,
            "description": "",
            "focus_areas": [],
            "audience": "",
            "tone": ""
        }

        # Extract information from search results
        if media_results:
            outlet_info["description"] = media_results[0].get("snippet", "")

        # Research journalist if provided
        journalist_info = None
        if journalist_name:
            journalist_query = f"{journalist_name} {media_name} journalist topics coverage"
            journalist_results = self.search.search_for_data(journalist_query)

            journalist_info = {
                "name": journalist_name,
                "specialization": "",
                "recent_topics": []
            }

            if journalist_results:
                journalist_info["specialization"] = journalist_results[0].get("snippet", "")

        return {
            "outlet": outlet_info,
            "journalist": journalist_info,
            "search_results": media_results
        }

    def as_langchain_tool(self) -> Tool:
        """Convert to LangChain tool format."""
        return Tool(
            name="media_research",
            description="Research media outlets and journalists to understand their focus, audience, and tone",
            func=lambda q: str(self.research_media_outlet(q))
        )
