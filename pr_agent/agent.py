"""
Main PR Comment Agent orchestrator using LangGraph.

This module coordinates the multi-step workflow:
1. Media research
2. Executive profile loading
3. Data research
4. Comment drafting
5. Comment humanization
6. Email notification
"""

from typing import Dict, Any, Optional
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, END

from .state import AgentState
from .config import PRAgentConfig
from .profile_manager import ExecutiveProfileManager
from .agents import (
    MediaResearcherAgent,
    DataResearcherAgent,
    CommentDrafterAgent,
    HumanizerAgent
)
from .tools import WebSearchTool, MediaResearchTool, EmailSender


class PRCommentAgent:
    """
    Main PR Comment Agent that orchestrates the entire workflow.

    This agent uses LangGraph to manage a multi-step pipeline for generating
    professional PR comments on behalf of executives.
    """

    def __init__(self, config: Optional[PRAgentConfig] = None):
        """
        Initialize the PR Comment Agent.

        Args:
            config: Configuration object (uses defaults if not provided)
        """
        self.config = config or PRAgentConfig()
        self.config.validate()

        # Initialize LLMs
        self.main_llm = self._create_llm(
            temperature=self.config.temperature
        )
        self.humanizer_llm = self._create_llm(
            temperature=self.config.humanizer_temperature
        )

        # Initialize tools
        self.web_search = WebSearchTool(
            api_key=self.config.serper_api_key or self.config.tavily_api_key,
            max_results=self.config.max_search_results
        )
        self.media_research_tool = MediaResearchTool(
            api_key=self.config.serper_api_key or self.config.tavily_api_key
        )
        self.email_sender = EmailSender(
            smtp_server=self.config.smtp_server,
            smtp_port=self.config.smtp_port,
            email_from=self.config.email_from,
            email_password=self.config.email_password
        )

        # Initialize agents
        self.media_researcher = MediaResearcherAgent(
            llm=self.main_llm,
            search_tool=self.media_research_tool
        )
        self.data_researcher = DataResearcherAgent(
            llm=self.main_llm,
            search_tool=self.web_search
        )
        self.comment_drafter = CommentDrafterAgent(llm=self.main_llm)
        self.humanizer = HumanizerAgent(llm=self.humanizer_llm)

        # Initialize profile manager
        self.profile_manager = ExecutiveProfileManager(
            profiles_dir=self.config.profiles_dir
        )

        # Build workflow graph
        self.workflow = self._build_workflow()

    def _create_llm(self, temperature: float = 0.7):
        """
        Create LLM instance based on configuration.

        Args:
            temperature: Temperature setting for the LLM

        Returns:
            LLM instance
        """
        if self.config.openai_api_key:
            return ChatOpenAI(
                model=self.config.model_name,
                temperature=temperature,
                api_key=self.config.openai_api_key
            )
        elif self.config.anthropic_api_key:
            return ChatAnthropic(
                model="claude-3-5-sonnet-20241022",
                temperature=temperature,
                api_key=self.config.anthropic_api_key
            )
        else:
            raise ValueError("No valid API key configured")

    def _build_workflow(self) -> StateGraph:
        """
        Build the LangGraph workflow.

        Returns:
            Compiled workflow graph
        """
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("load_profile", self._load_profile_node)
        workflow.add_node("research_media", self._research_media_node)
        workflow.add_node("research_data", self._research_data_node)
        workflow.add_node("draft_comment", self._draft_comment_node)
        workflow.add_node("humanize_comment", self._humanize_comment_node)
        workflow.add_node("send_email", self._send_email_node)

        # Define workflow edges
        workflow.set_entry_point("load_profile")
        workflow.add_edge("load_profile", "research_media")
        workflow.add_edge("research_media", "research_data")
        workflow.add_edge("research_data", "draft_comment")
        workflow.add_edge("draft_comment", "humanize_comment")
        workflow.add_edge("humanize_comment", "send_email")
        workflow.add_edge("send_email", END)

        return workflow.compile()

    def _load_profile_node(self, state: AgentState) -> AgentState:
        """Load executive profile."""
        if self.config.enable_verbose_logging:
            print(f"📋 Loading profile for {state['executive_name']}...")

        try:
            profile = self.profile_manager.load_profile(state['executive_name'])
            state['executive_profile'] = profile
            state['current_step'] = "profile_loaded"
        except Exception as e:
            error_msg = f"Failed to load profile: {str(e)}"
            state['errors'].append(error_msg)
            print(f"❌ {error_msg}")

        return state

    def _research_media_node(self, state: AgentState) -> AgentState:
        """Research media outlet and journalist."""
        if self.config.enable_verbose_logging:
            print(f"🔍 Researching media outlet: {state['media_outlet']}...")

        try:
            research = self.media_researcher.research(
                media_outlet=state['media_outlet'],
                journalist_name=state.get('journalist_name')
            )
            state['media_research'] = research
            state['current_step'] = "media_researched"
        except Exception as e:
            error_msg = f"Media research failed: {str(e)}"
            state['errors'].append(error_msg)
            print(f"⚠️ {error_msg}")
            state['media_research'] = {"analysis": "Media research unavailable"}

        return state

    def _research_data_node(self, state: AgentState) -> AgentState:
        """Research supporting data and statistics."""
        if self.config.enable_verbose_logging:
            print("📊 Researching supporting data...")

        try:
            # Extract topic from question
            topic = state['journalist_question'][:100]

            research = self.data_researcher.research_supporting_data(
                topic=topic,
                context=state['article_text'][:500],
                executive_perspective=state['executive_profile'].get('talking_points', [''])[0]
            )
            state['supporting_data'] = research
            state['current_step'] = "data_researched"
        except Exception as e:
            error_msg = f"Data research failed: {str(e)}"
            state['errors'].append(error_msg)
            print(f"⚠️ {error_msg}")
            state['supporting_data'] = {"curated_data": "No supporting data available"}

        return state

    def _draft_comment_node(self, state: AgentState) -> AgentState:
        """Draft the PR comment."""
        if self.config.enable_verbose_logging:
            print("✍️ Drafting comment...")

        try:
            comment = self.comment_drafter.draft_comment(
                executive_name=state['executive_name'],
                executive_profile=state['executive_profile'],
                article_text=state['article_text'],
                journalist_question=state['journalist_question'],
                media_outlet=state['media_outlet'],
                media_research=state['media_research'],
                supporting_data=state['supporting_data']
            )
            state['drafted_comment'] = comment
            state['current_step'] = "comment_drafted"
        except Exception as e:
            error_msg = f"Comment drafting failed: {str(e)}"
            state['errors'].append(error_msg)
            print(f"❌ {error_msg}")

        return state

    def _humanize_comment_node(self, state: AgentState) -> AgentState:
        """Humanize the drafted comment."""
        if self.config.enable_verbose_logging:
            print("🎨 Humanizing comment...")

        try:
            humanized = self.humanizer.humanize_comment(
                drafted_comment=state['drafted_comment'],
                executive_name=state['executive_name'],
                executive_profile=state['executive_profile']
            )
            state['humanized_comment'] = humanized
            state['current_step'] = "comment_humanized"
        except Exception as e:
            error_msg = f"Humanization failed: {str(e)}"
            state['errors'].append(error_msg)
            print(f"⚠️ {error_msg}")
            # Fallback to drafted comment
            state['humanized_comment'] = state['drafted_comment']

        return state

    def _send_email_node(self, state: AgentState) -> AgentState:
        """Send email to PR manager."""
        if self.config.enable_verbose_logging:
            print("📧 Sending email to PR manager...")

        try:
            pr_email = state.get('pr_manager_email') or self.config.pr_manager_email

            if not pr_email:
                print("⚠️ No PR manager email configured. Skipping email send.")
                state['email_sent'] = False
                return state

            success = self.email_sender.send_comment_for_approval(
                pr_manager_email=pr_email,
                executive_name=state['executive_name'],
                journalist_question=state['journalist_question'],
                media_outlet=state['media_outlet'],
                drafted_comment=state['drafted_comment'],
                humanized_comment=state['humanized_comment'],
                article_url=state.get('article_url')
            )

            state['email_sent'] = success
            state['current_step'] = "email_sent"

        except Exception as e:
            error_msg = f"Email sending failed: {str(e)}"
            state['errors'].append(error_msg)
            print(f"❌ {error_msg}")
            state['email_sent'] = False

        return state

    def generate_comment(
        self,
        article_text: str,
        journalist_question: str,
        media_outlet: str,
        executive_name: str,
        article_url: Optional[str] = None,
        journalist_name: Optional[str] = None,
        pr_manager_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a PR comment using the complete workflow.

        Args:
            article_text: The article content
            journalist_question: Question from the journalist
            media_outlet: Name of the media outlet
            executive_name: Name of the executive providing the comment
            article_url: Optional URL to the article
            journalist_name: Optional name of the journalist
            pr_manager_email: Optional email override for PR manager

        Returns:
            Dictionary with results including drafted and humanized comments
        """
        # Initialize state
        initial_state: AgentState = {
            "article_text": article_text,
            "article_url": article_url,
            "journalist_question": journalist_question,
            "media_outlet": media_outlet,
            "journalist_name": journalist_name,
            "executive_name": executive_name,
            "executive_profile": None,
            "media_research": None,
            "supporting_data": None,
            "drafted_comment": None,
            "humanized_comment": None,
            "timestamp": datetime.now().isoformat(),
            "approval_status": "pending",
            "email_sent": False,
            "pr_manager_email": pr_manager_email,
            "current_step": "initializing",
            "errors": []
        }

        # Run workflow
        if self.config.enable_verbose_logging:
            print("\n🚀 Starting PR Comment Generation Workflow")
            print("=" * 60)

        final_state = self.workflow.invoke(initial_state)

        if self.config.enable_verbose_logging:
            print("=" * 60)
            print("✅ Workflow completed\n")

        return final_state
