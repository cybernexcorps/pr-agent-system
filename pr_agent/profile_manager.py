"""
Executive profile management for the PR agent.
"""

import json
import os
from typing import Dict, Any, Optional, List
from pathlib import Path


class ExecutiveProfileManager:
    """Manages executive profiles for PR comment generation."""

    def __init__(self, profiles_dir: str = "pr_agent/config/executive_profiles"):
        """
        Initialize profile manager.

        Args:
            profiles_dir: Directory containing executive profile JSON files
        """
        self.profiles_dir = Path(profiles_dir)
        self._profiles_cache = {}

    def load_profile(self, executive_name: str) -> Dict[str, Any]:
        """
        Load an executive's profile.

        Args:
            executive_name: Name of the executive

        Returns:
            Executive profile dictionary

        Raises:
            FileNotFoundError: If profile doesn't exist
        """
        # Check cache
        if executive_name in self._profiles_cache:
            return self._profiles_cache[executive_name]

        # Load from file
        profile_path = self.profiles_dir / f"{self._normalize_name(executive_name)}.json"

        if not profile_path.exists():
            raise FileNotFoundError(
                f"Profile not found for '{executive_name}'. "
                f"Expected file: {profile_path}"
            )

        with open(profile_path, 'r') as f:
            profile = json.load(f)

        # Validate profile
        self._validate_profile(profile, executive_name)

        # Cache and return
        self._profiles_cache[executive_name] = profile
        return profile

    def save_profile(self, executive_name: str, profile: Dict[str, Any]) -> None:
        """
        Save an executive's profile.

        Args:
            executive_name: Name of the executive
            profile: Profile dictionary to save
        """
        # Validate before saving
        self._validate_profile(profile, executive_name)

        # Ensure directory exists
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

        # Save to file
        profile_path = self.profiles_dir / f"{self._normalize_name(executive_name)}.json"

        with open(profile_path, 'w') as f:
            json.dump(profile, f, indent=2)

        # Update cache
        self._profiles_cache[executive_name] = profile

    def list_profiles(self) -> List[str]:
        """
        List all available executive profiles.

        Returns:
            List of executive names
        """
        if not self.profiles_dir.exists():
            return []

        profiles = []
        for file_path in self.profiles_dir.glob("*.json"):
            name = file_path.stem.replace('_', ' ').title()
            profiles.append(name)

        return sorted(profiles)

    def create_sample_profile(self, executive_name: str) -> Dict[str, Any]:
        """
        Create a sample profile template.

        Args:
            executive_name: Name of the executive

        Returns:
            Sample profile dictionary
        """
        return {
            "name": executive_name,
            "title": "Chief Brand Officer",
            "company": "Brand Agency Name",
            "expertise": [
                "Brand strategy",
                "Marketing effectiveness",
                "Consumer insights"
            ],
            "communication_style": "Professional yet approachable, data-driven",
            "tone": "Confident, insightful, forward-thinking",
            "personality_traits": [
                "Analytical",
                "Strategic",
                "Articulate"
            ],
            "talking_points": [
                "Importance of long-term brand building",
                "Data-driven decision making",
                "Consumer-centric approach",
                "Integration of creativity and analytics"
            ],
            "values": [
                "Authenticity",
                "Innovation",
                "Strategic thinking",
                "Measurable results"
            ],
            "speaking_patterns": "Uses concrete examples, often references data, prefers clear and direct language",
            "do_not_say": [
                "Overly promotional language",
                "Vague buzzwords without substance",
                "Unsubstantiated claims"
            ],
            "preferred_structure": "Hook with insight → Support with data → Conclude with actionable perspective"
        }

    def _normalize_name(self, name: str) -> str:
        """
        Normalize executive name for file naming.

        Args:
            name: Executive name

        Returns:
            Normalized name (lowercase, underscores)
        """
        return name.lower().replace(' ', '_').replace('-', '_')

    def _validate_profile(self, profile: Dict[str, Any], executive_name: str) -> None:
        """
        Validate that a profile has required fields.

        Args:
            profile: Profile dictionary
            executive_name: Name of the executive

        Raises:
            ValueError: If profile is missing required fields
        """
        required_fields = ["name", "title", "communication_style", "expertise"]
        missing_fields = [f for f in required_fields if f not in profile]

        if missing_fields:
            raise ValueError(
                f"Profile for '{executive_name}' is missing required fields: "
                f"{', '.join(missing_fields)}"
            )
