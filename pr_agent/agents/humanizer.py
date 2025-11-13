"""
Humanizer agent for making AI-generated comments sound more natural and authentic.
"""

from typing import Dict, Any
from langchain.prompts import PromptTemplate
from ..prompts.templates import HUMANIZER_PROMPT


class HumanizerAgent:
    """Agent specialized in humanizing AI-generated text."""

    def __init__(self, llm: Any):
        """
        Initialize humanizer agent.

        Args:
            llm: Language model instance (typically with higher temperature)
        """
        self.llm = llm
        self.prompt_template = PromptTemplate(
            input_variables=["drafted_comment", "executive_name", "executive_style_notes"],
            template=HUMANIZER_PROMPT
        )

    def humanize_comment(
        self,
        drafted_comment: str,
        executive_name: str,
        executive_profile: Dict[str, Any]
    ) -> str:
        """
        Humanize a drafted comment to make it sound more natural.

        Args:
            drafted_comment: The original drafted comment
            executive_name: Name of the executive
            executive_profile: Executive's profile with style notes

        Returns:
            Humanized comment text
        """
        # Extract style notes
        style_notes = self._extract_style_notes(executive_profile)

        # Generate humanized version
        prompt = self.prompt_template.format(
            drafted_comment=drafted_comment,
            executive_name=executive_name,
            executive_style_notes=style_notes
        )

        response = self.llm.invoke(prompt)
        humanized = response.content if hasattr(response, 'content') else str(response)

        return humanized.strip()

    def _extract_style_notes(self, profile: Dict[str, Any]) -> str:
        """
        Extract style-relevant notes from profile.

        Args:
            profile: Executive profile

        Returns:
            Style notes text
        """
        notes = []

        if "communication_style" in profile:
            notes.append(f"Style: {profile['communication_style']}")

        if "tone" in profile:
            notes.append(f"Tone: {profile['tone']}")

        if "personality_traits" in profile:
            notes.append(f"Personality: {', '.join(profile['personality_traits'])}")

        if "speaking_patterns" in profile:
            notes.append(f"Speaking patterns: {profile['speaking_patterns']}")

        return " | ".join(notes) if notes else "Natural, professional, conversational"
