"""
Executive profile management for the PR agent.
"""

import json
import os
import re
from typing import Dict, Any, Optional, List
from pathlib import Path


class ExecutiveProfileManager:
    """Manages executive profiles for PR comment generation."""

    def __init__(self, profiles_dir: str = None):
        """
        Initialize profile manager.

        Args:
            profiles_dir: Directory containing executive profile JSON files.
                         If None, uses default location relative to package root.
        """
        if profiles_dir is None:
            # Resolve path relative to this file's location
            # __file__ is at pr_agent/profile_manager.py
            # We want pr_agent/config/executive_profiles
            package_dir = Path(__file__).parent  # pr_agent/
            self.profiles_dir = package_dir / "config" / "executive_profiles"
        else:
            profiles_path = Path(profiles_dir)
            # If relative path, try to resolve relative to package root first
            if not profiles_path.is_absolute():
                package_dir = Path(__file__).parent  # pr_agent/
                potential_path = package_dir / profiles_dir
                if potential_path.exists():
                    self.profiles_dir = potential_path
                else:
                    # Try as-is (might be relative to current working directory)
                    self.profiles_dir = profiles_path
            else:
                self.profiles_dir = profiles_path
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
            ValueError: If path traversal attempt detected
        """
        # Check cache
        if executive_name in self._profiles_cache:
            return self._profiles_cache[executive_name]

        # Normalize and build path
        normalized = self._normalize_name(executive_name)
        profile_path = self.profiles_dir / f"{normalized}.json"

        # SECURITY: Ensure path is within profiles_dir (prevent path traversal)
        try:
            profile_path = profile_path.resolve()
            profiles_dir_resolved = self.profiles_dir.resolve()

            # Check if profile_path is under profiles_dir
            profile_path.relative_to(profiles_dir_resolved)
        except (ValueError, RuntimeError):
            raise ValueError(
                f"Invalid executive name '{executive_name}' - path traversal attempt detected"
            )

        if not profile_path.exists():
            raise FileNotFoundError(
                f"Profile not found for '{executive_name}'. "
                f"Expected file: {profile_path}"
            )

        with open(profile_path, 'r', encoding='utf-8') as f:
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

        Raises:
            ValueError: If path traversal attempt detected or profile validation fails
        """
        # Validate before saving
        self._validate_profile(profile, executive_name)

        # Ensure directory exists
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

        # Normalize and build path
        normalized = self._normalize_name(executive_name)
        profile_path = self.profiles_dir / f"{normalized}.json"

        # SECURITY: Ensure path is within profiles_dir (prevent path traversal)
        try:
            profile_path = profile_path.resolve()
            profiles_dir_resolved = self.profiles_dir.resolve()

            # Check if profile_path is under profiles_dir
            profile_path.relative_to(profiles_dir_resolved)
        except (ValueError, RuntimeError):
            raise ValueError(
                f"Invalid executive name '{executive_name}' - path traversal attempt detected"
            )

        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)

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

        Removes dangerous characters and prevents path traversal attacks.

        Args:
            name: Executive name

        Returns:
            Normalized name (lowercase, underscores, alphanumeric only)
        """
        # Remove any characters that aren't alphanumeric, spaces, or hyphens
        sanitized = re.sub(r'[^a-zA-Z0-9\s\-]', '', name)
        # Convert to lowercase and replace spaces/hyphens with underscores
        return sanitized.lower().replace(' ', '_').replace('-', '_')

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
