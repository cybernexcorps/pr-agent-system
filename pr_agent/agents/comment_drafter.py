"""
Comment drafter agent for generating professional PR comments.
"""

from typing import Dict, Any
from langchain_core.prompts import PromptTemplate
from ..prompts.templates import COMMENT_DRAFTING_PROMPT


class CommentDrafterAgent:
    """Agent specialized in drafting professional PR comments."""

    def __init__(self, llm: Any):
        """
        Initialize comment drafter agent.

        Args:
            llm: Language model instance
        """
        self.llm = llm
        self.prompt_template = PromptTemplate(
            input_variables=[
                "executive_name",
                "executive_title",
                "executive_profile",
                "article_text",
                "journalist_question",
                "media_outlet",
                "media_research",
                "supporting_data"
            ],
            template=COMMENT_DRAFTING_PROMPT
        )

    def draft_comment(
        self,
        executive_name: str,
        executive_profile: Dict[str, Any],
        article_text: str,
        journalist_question: str,
        media_outlet: str,
        media_research: Dict[str, Any],
        supporting_data: Dict[str, Any]
    ) -> str:
        """
        Draft a professional comment on behalf of the executive.

        Args:
            executive_name: Name of the executive
            executive_profile: Executive's profile and communication style
            article_text: The article text
            journalist_question: Question from the journalist
            media_outlet: Name of the media outlet
            media_research: Research about the media outlet
            supporting_data: Supporting statistics and data

        Returns:
            Drafted comment text
        """
        # Format executive profile
        profile_text = self._format_profile(executive_profile)

        # Format media research
        media_research_text = media_research.get("analysis", "No media research available")

        # Format supporting data
        supporting_data_text = supporting_data.get("curated_data", "No supporting data available")

        # Generate comment
        prompt = self.prompt_template.format(
            executive_name=executive_name,
            executive_title=executive_profile.get("title", "Executive"),
            executive_profile=profile_text,
            article_text=article_text[:2000],  # Limit article length
            journalist_question=journalist_question,
            media_outlet=media_outlet,
            media_research=media_research_text,
            supporting_data=supporting_data_text
        )

        response = self.llm.invoke(prompt)
        comment = response.content if hasattr(response, 'content') else str(response)

        return comment.strip()

    def _format_profile(self, profile: Dict[str, Any]) -> str:
        """
        Format executive profile for prompt.

        Args:
            profile: Executive profile dictionary

        Returns:
            Formatted profile text
        """
        parts = []

        if "title" in profile:
            parts.append(f"Title: {profile['title']}")

        if "expertise" in profile:
            parts.append(f"Expertise: {', '.join(profile['expertise'])}")

        if "communication_style" in profile:
            parts.append(f"Communication Style: {profile['communication_style']}")

        if "talking_points" in profile:
            points = "\n  - ".join(profile['talking_points'])
            parts.append(f"Key Talking Points:\n  - {points}")

        if "tone" in profile:
            parts.append(f"Tone: {profile['tone']}")

        if "values" in profile:
            parts.append(f"Values: {', '.join(profile['values'])}")

        return "\n".join(parts)
