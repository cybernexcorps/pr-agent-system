"""
State management for the PR agent workflow.

Defines the state that flows through the LangGraph agent pipeline.
"""

from typing import TypedDict, Optional, List, Dict, Any
from datetime import datetime


class AgentState(TypedDict):
    """State object that flows through the PR agent pipeline."""

    # Input data
    article_text: str
    article_url: Optional[str]
    journalist_question: str
    media_outlet: str
    journalist_name: Optional[str]

    # Executive profile
    executive_name: str
    executive_profile: Optional[Dict[str, Any]]

    # Research outputs
    media_research: Optional[Dict[str, Any]]
    supporting_data: Optional[List[Dict[str, Any]]]

    # Comment generation
    drafted_comment: Optional[str]
    humanized_comment: Optional[str]

    # Metadata
    timestamp: str
    approval_status: str  # "pending", "approved", "rejected"

    # Email tracking
    email_sent: bool
    pr_manager_email: Optional[str]

    # Workflow tracking
    current_step: str
    errors: List[str]
