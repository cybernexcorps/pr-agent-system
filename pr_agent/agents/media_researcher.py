"""
Media researcher agent for analyzing media outlets and journalists.
"""

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import PromptTemplate
from ..tools.search import MediaResearchTool
from ..prompts.templates import MEDIA_RESEARCH_PROMPT


class MediaResearcherAgent:
    """Agent specialized in researching media outlets and journalists."""

    def __init__(self, llm: Any, search_tool: MediaResearchTool):
        """
        Initialize media researcher agent.

        Args:
            llm: Language model instance
            search_tool: Media research tool
        """
        self.llm = llm
        self.search_tool = search_tool
        self.prompt_template = PromptTemplate(
            input_variables=["media_outlet", "journalist_name", "search_results"],
            template=MEDIA_RESEARCH_PROMPT
        )

    def research(self, media_outlet: str, journalist_name: str = None) -> Dict[str, Any]:
        """
        Research a media outlet and journalist.

        Args:
            media_outlet: Name of the media outlet
            journalist_name: Optional journalist name

        Returns:
            Dictionary with research findings
        """
        # Perform search
        raw_research = self.search_tool.research_media_outlet(
            media_name=media_outlet,
            journalist_name=journalist_name
        )

        # Format search results for LLM
        search_results_text = "\n".join([
            f"- {r['title']}: {r['snippet']}"
            for r in raw_research.get("search_results", [])
        ])

        # Use LLM to analyze and structure the findings
        prompt = self.prompt_template.format(
            media_outlet=media_outlet,
            journalist_name=journalist_name or "Not specified",
            search_results=search_results_text
        )

        analysis = self.llm.invoke(prompt)

        return {
            "raw_data": raw_research,
            "analysis": analysis.content if hasattr(analysis, 'content') else str(analysis),
            "media_outlet": media_outlet,
            "journalist_name": journalist_name
        }
