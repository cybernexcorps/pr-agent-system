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
    model_name: str = "claude-sonnet-4-5-20250929"  # Latest Claude Sonnet 4.5 model
    temperature: float = 0.7

    # Model Performance Settings
    max_tokens: int = 4096  # Maximum output tokens
    max_input_tokens: int = 50000  # Maximum input context
    enable_streaming: bool = True  # Enable streaming for real-time feedback
    max_retries: int = 3  # Number of retries for failed LLM calls
    request_timeout: float = 60.0  # Request timeout in seconds

    # Humanizer Configuration
    humanizer_model: str = "claude-sonnet-4-5-20250929"
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
    enable_verbose_logging: bool = True

    # Cache Configuration
    redis_url: str = field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379"))
    enable_cache: bool = field(default_factory=lambda: os.getenv("ENABLE_CACHE", "true").lower() == "true")
    cache_ttl_comments: int = 3600  # 1 hour for full comment responses
    cache_ttl_search: int = 86400  # 24 hours for search results
    cache_ttl_media: int = 86400  # 24 hours for media research

    # LangSmith Observability
    langsmith_api_key: Optional[str] = field(default_factory=lambda: os.getenv("LANGSMITH_API_KEY"))
    langsmith_project: str = "pr-agent-production"
    enable_tracing: bool = True

    # Structured Logging
    log_level: str = "INFO"
    log_format: str = "json"  # "json" or "console"

    # Health Checks
    health_check_enabled: bool = True
    health_check_timeout: int = 5

    # Async Settings
    async_enabled: bool = True
    max_concurrent_operations: int = 5

    # Phase 3: Memory System Configuration
    enable_memory: bool = field(default_factory=lambda: os.getenv("ENABLE_MEMORY", "false").lower() == "true")
    memory_max_tokens: int = 2000  # Max tokens for short-term memory
    memory_vector_store_path: str = "./data/memory_store"  # Path for vector store persistence
    voyage_api_key: Optional[str] = field(default_factory=lambda: os.getenv("VOYAGE_API_KEY"))

    # Phase 3: Evaluation Framework Configuration
    enable_evaluation: bool = field(default_factory=lambda: os.getenv("ENABLE_EVALUATION", "false").lower() == "true")
    evaluation_model: str = "claude-sonnet-4-5-20250929"  # Model for evaluation

    # Phase 3: RAG Configuration
    enable_rag: bool = field(default_factory=lambda: os.getenv("ENABLE_RAG", "false").lower() == "true")
    rag_vector_store_path: str = "./data/rag_store"  # Path for RAG vector stores
    rag_chunk_size: int = 1000  # Chunk size for document splitting
    rag_chunk_overlap: int = 200  # Overlap between chunks
    rag_top_k: int = 3  # Number of relevant results to retrieve

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
