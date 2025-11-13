"""
Configuration management for PR Agent.

Handles API keys, model settings, and agent parameters.
"""

import os
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class PRAgentConfig:
    """Configuration for the PR Comment Agent."""

    # LLM Configuration
    openai_api_key: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    anthropic_api_key: Optional[str] = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY"))
    model_name: str = "gpt-4o"  # Main agent model
    temperature: float = 0.7

    # Humanizer Configuration
    humanizer_model: str = "gpt-4o"
    humanizer_temperature: float = 0.9  # Higher temperature for more natural language

    # Search Configuration
    serper_api_key: Optional[str] = field(default_factory=lambda: os.getenv("SERPER_API_KEY"))
    tavily_api_key: Optional[str] = field(default_factory=lambda: os.getenv("TAVILY_API_KEY"))
    max_search_results: int = 5

    # Email Configuration
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    email_from: Optional[str] = field(default_factory=lambda: os.getenv("EMAIL_FROM"))
    email_password: Optional[str] = field(default_factory=lambda: os.getenv("EMAIL_PASSWORD"))
    pr_manager_email: Optional[str] = field(default_factory=lambda: os.getenv("PR_MANAGER_EMAIL"))

    # Executive Profiles Directory
    profiles_dir: str = "pr_agent/config/executive_profiles"

    # Agent Behavior
    max_retries: int = 3
    enable_verbose_logging: bool = True

    def validate(self) -> bool:
        """Validate that required configuration is present."""
        errors = []

        if not self.openai_api_key and not self.anthropic_api_key:
            errors.append("Either OPENAI_API_KEY or ANTHROPIC_API_KEY must be set")

        if not self.serper_api_key and not self.tavily_api_key:
            errors.append("Either SERPER_API_KEY or TAVILY_API_KEY must be set for web search")

        if not self.email_from or not self.email_password:
            errors.append("EMAIL_FROM and EMAIL_PASSWORD must be set for email notifications")

        if errors:
            raise ValueError(f"Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))

        return True
