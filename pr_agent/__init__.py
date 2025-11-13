"""
PR Agent: AI-powered comment generation system for branding agency executives.

This module provides a multi-step LangChain agent that:
1. Analyzes articles and journalist questions
2. Researches media outlets
3. Applies executive profiles and voice
4. Researches supporting data
5. Drafts professional comments
6. Humanizes the output
7. Sends to PR managers for approval
"""

from .agent import PRCommentAgent
from .state import AgentState
from .config import PRAgentConfig

__version__ = "1.0.0"
__all__ = ["PRCommentAgent", "AgentState", "PRAgentConfig"]
