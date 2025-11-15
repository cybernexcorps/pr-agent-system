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

import asyncio
from typing import Dict, Any, Optional, AsyncIterator
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
from .logging_config import configure_logging, get_logger, LogContext
from .observability import configure_langsmith, trace_agent_step
from .cache import PRAgentCache
from .memory import PRAgentMemory
from .evaluation import PRAgentEvaluator
from .rag import PRAgentRAG

logger = get_logger(__name__)


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

        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If required components fail to initialize
        """
        try:
            self.config = config or PRAgentConfig()
            self.config.validate()

            # Configure structured logging
            configure_logging(
                log_level=self.config.log_level,
                log_format=self.config.log_format,
                enable_verbose=self.config.enable_verbose_logging
            )

            # Configure LangSmith tracing
            if self.config.enable_tracing:
                configure_langsmith(
                    api_key=self.config.langsmith_api_key,
                    project=self.config.langsmith_project,
                    enable_tracing=True
                )

            logger.info(
                "agent_initializing",
                model=self.config.model_name,
                tracing_enabled=self.config.enable_tracing,
                async_enabled=self.config.async_enabled
            )

            # Initialize LLMs
            try:
                self.main_llm = self._create_llm(
                    temperature=self.config.temperature
                )
                self.humanizer_llm = self._create_llm(
                    temperature=self.config.humanizer_temperature
                )
            except Exception as e:
                raise RuntimeError(f"Failed to initialize LLM models: {e}")

            # Initialize tools with error handling
            try:
                self.web_search = WebSearchTool(
                    api_key=self.config.serper_api_key or self.config.tavily_api_key,
                    max_results=self.config.max_search_results
                )
                self.media_research_tool = MediaResearchTool(
                    api_key=self.config.serper_api_key or self.config.tavily_api_key
                )
            except Exception as e:
                raise RuntimeError(f"Failed to initialize search tools: {e}")

            try:
                self.email_sender = EmailSender(
                    smtp_server=self.config.smtp_server,
                    smtp_port=self.config.smtp_port,
                    email_from=self.config.email_from,
                    email_password=self.config.email_password
                )
            except Exception as e:
                raise RuntimeError(f"Failed to initialize email sender: {e}")

            # Initialize agents
            try:
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
            except Exception as e:
                raise RuntimeError(f"Failed to initialize specialized agents: {e}")

            # Initialize profile manager
            try:
                self.profile_manager = ExecutiveProfileManager(
                    profiles_dir=self.config.profiles_dir
                )
            except Exception as e:
                raise RuntimeError(f"Failed to initialize profile manager: {e}")

            # Initialize cache
            try:
                self.cache = PRAgentCache(
                    redis_url=self.config.redis_url,
                    enabled=self.config.enable_cache
                )
                logger.info(
                    "cache_initialized",
                    enabled=self.cache.enabled,
                    redis_url=self.config.redis_url
                )
            except Exception as e:
                logger.warning(f"Failed to initialize cache: {e}. Continuing without cache.")
                self.cache = PRAgentCache(enabled=False)

            # Phase 3: Initialize memory system
            try:
                self.memory = PRAgentMemory(
                    config=self.config,
                    llm=self.main_llm
                )
                logger.info(
                    "memory_system_initialized",
                    enabled=self.memory.enabled
                )
            except Exception as e:
                logger.warning(f"Failed to initialize memory system: {e}. Continuing without memory.")
                self.memory = None

            # Phase 3: Initialize evaluation framework
            try:
                self.evaluator = PRAgentEvaluator(config=self.config)
                logger.info(
                    "evaluator_initialized",
                    enabled=self.evaluator.enabled
                )
            except Exception as e:
                logger.warning(f"Failed to initialize evaluator: {e}. Continuing without evaluation.")
                self.evaluator = None

            # Phase 3: Initialize RAG system
            try:
                self.rag = PRAgentRAG(config=self.config)
                logger.info(
                    "rag_system_initialized",
                    enabled=self.rag.enabled
                )
            except Exception as e:
                logger.warning(f"Failed to initialize RAG system: {e}. Continuing without RAG.")
                self.rag = None

            # Build workflow graph
            try:
                self.workflow = self._build_workflow()
            except Exception as e:
                raise RuntimeError(f"Failed to build workflow graph: {e}")

        except ValueError as e:
            # Re-raise validation errors
            raise
        except RuntimeError as e:
            # Re-raise runtime errors
            raise
        except Exception as e:
            raise RuntimeError(f"Failed to initialize PR Comment Agent: {e}")

    def _create_llm(self, temperature: float = 0.7):
        """
        Create LLM instance based on configuration with enhanced settings.

        Args:
            temperature: Temperature setting for the LLM

        Returns:
            LLM instance with optimized configuration
        """
        if self.config.openai_api_key:
            return ChatOpenAI(
                model=self.config.model_name,
                temperature=temperature,
                api_key=self.config.openai_api_key,
                max_tokens=self.config.max_tokens,
                max_retries=self.config.max_retries,
                timeout=self.config.request_timeout,
                streaming=self.config.enable_streaming
            )
        elif self.config.anthropic_api_key:
            # Map common OpenAI model names to Anthropic equivalents
            model_map = {
                "gpt-4o": "claude-3-5-sonnet-20241022",
                "gpt-4": "claude-3-5-sonnet-20241022",
                "gpt-4-turbo": "claude-3-5-sonnet-20241022",
                "gpt-3.5-turbo": "claude-3-haiku-20240307"
            }

            # Use mapped model or user-specified model (allows direct Anthropic model names)
            anthropic_model = model_map.get(
                self.config.model_name,
                self.config.model_name  # Allow direct Anthropic model names
            )

            return ChatAnthropic(
                model=anthropic_model,
                temperature=temperature,
                api_key=self.config.anthropic_api_key,
                max_tokens=self.config.max_tokens,
                max_retries=self.config.max_retries,
                timeout=self.config.request_timeout,
                streaming=self.config.enable_streaming
            )
        else:
            raise ValueError("No valid API key configured")

    def _check_token_limit(self, text: str, max_tokens: Optional[int] = None) -> int:
        """
        Validate input doesn't exceed token limits.

        Args:
            text: Text to check
            max_tokens: Maximum tokens allowed (uses config default if not provided)

        Returns:
            Estimated token count

        Raises:
            ValueError: If text exceeds token limit
        """
        max_tokens = max_tokens or self.config.max_input_tokens

        # Rough estimation: ~4 characters per token
        estimated_tokens = len(text) // 4

        if estimated_tokens > max_tokens:
            raise ValueError(
                f"Input exceeds token limit: ~{estimated_tokens} tokens > {max_tokens} tokens. "
                f"Please reduce input size."
            )

        return estimated_tokens

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
        logger.info(
            "loading_profile",
            executive=state['executive_name'],
            step="load_profile"
        )

        try:
            profile = self.profile_manager.load_profile(state['executive_name'])
            logger.info(
                "profile_loaded",
                executive=state['executive_name'],
                success=True
            )
            return {
                **state,
                'executive_profile': profile,
                'current_step': 'profile_loaded'
            }
        except Exception as e:
            error_msg = f"Failed to load profile: {str(e)}"
            logger.error(
                "profile_load_failed",
                executive=state['executive_name'],
                error=str(e),
                error_type=type(e).__name__
            )
            return {
                **state,
                'errors': [*state['errors'], error_msg]
            }

    def _research_media_node(self, state: AgentState) -> AgentState:
        """Research media outlet and journalist."""
        logger.info(
            "researching_media",
            media_outlet=state['media_outlet'],
            journalist=state.get('journalist_name'),
            step="research_media"
        )

        try:
            research = self.media_researcher.research(
                media_outlet=state['media_outlet'],
                journalist_name=state.get('journalist_name')
            )
            logger.info(
                "media_research_complete",
                media_outlet=state['media_outlet'],
                success=True
            )
            return {
                **state,
                'media_research': research,
                'current_step': 'media_researched'
            }
        except Exception as e:
            error_msg = f"Media research failed: {str(e)}"
            logger.warning(
                "media_research_failed",
                media_outlet=state['media_outlet'],
                error=str(e),
                error_type=type(e).__name__
            )
            return {
                **state,
                'media_research': {"analysis": "Media research unavailable"},
                'errors': [*state['errors'], error_msg]
            }

    def _research_data_node(self, state: AgentState) -> AgentState:
        """Research supporting data and statistics."""
        logger.info("researching_data", step="research_data")

        try:
            # Extract topic from question
            topic = state['journalist_question'][:100]

            research = self.data_researcher.research_supporting_data(
                topic=topic,
                context=state['article_text'][:500],
                executive_perspective=state['executive_profile'].get('talking_points', [''])[0]
            )
            logger.info("data_research_complete", success=True)
            return {
                **state,
                'supporting_data': research,
                'current_step': 'data_researched'
            }
        except Exception as e:
            error_msg = f"Data research failed: {str(e)}"
            logger.warning(
                "data_research_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            return {
                **state,
                'supporting_data': {"curated_data": "No supporting data available"},
                'errors': [*state['errors'], error_msg]
            }

    def _draft_comment_node(self, state: AgentState) -> AgentState:
        """Draft the PR comment."""
        logger.info("drafting_comment", step="draft_comment")

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
            logger.info(
                "comment_drafted",
                success=True,
                comment_length=len(comment)
            )
            return {
                **state,
                'drafted_comment': comment,
                'current_step': 'comment_drafted'
            }
        except Exception as e:
            error_msg = f"Comment drafting failed: {str(e)}"
            logger.error(
                "comment_drafting_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            return {
                **state,
                'errors': [*state['errors'], error_msg]
            }

    def _humanize_comment_node(self, state: AgentState) -> AgentState:
        """Humanize the drafted comment."""
        logger.info("humanizing_comment", step="humanize_comment")

        try:
            humanized = self.humanizer.humanize_comment(
                drafted_comment=state['drafted_comment'],
                executive_name=state['executive_name'],
                executive_profile=state['executive_profile']
            )
            logger.info(
                "comment_humanized",
                success=True,
                humanized_length=len(humanized)
            )
            return {
                **state,
                'humanized_comment': humanized,
                'current_step': 'comment_humanized'
            }
        except Exception as e:
            error_msg = f"Humanization failed: {str(e)}"
            logger.warning(
                "humanization_failed",
                error=str(e),
                error_type=type(e).__name__,
                fallback="using_drafted_comment"
            )
            # Fallback to drafted comment
            return {
                **state,
                'humanized_comment': state['drafted_comment'],
                'errors': [*state['errors'], error_msg]
            }

    def _send_email_node(self, state: AgentState) -> AgentState:
        """Send email to PR manager."""
        logger.info("sending_email", step="send_email")

        try:
            pr_email = state.get('pr_manager_email') or self.config.pr_manager_email

            if not pr_email:
                logger.warning(
                    "email_skipped",
                    reason="no_pr_manager_email_configured"
                )
                return {
                    **state,
                    'email_sent': False
                }

            success = self.email_sender.send_comment_for_approval(
                pr_manager_email=pr_email,
                executive_name=state['executive_name'],
                journalist_question=state['journalist_question'],
                media_outlet=state['media_outlet'],
                drafted_comment=state['drafted_comment'],
                humanized_comment=state['humanized_comment'],
                article_url=state.get('article_url')
            )

            logger.info(
                "email_sent",
                success=success,
                recipient=pr_email
            )

            return {
                **state,
                'email_sent': success,
                'current_step': 'email_sent'
            }

        except Exception as e:
            error_msg = f"Email sending failed: {str(e)}"
            logger.error(
                "email_send_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            return {
                **state,
                'email_sent': False,
                'errors': [*state['errors'], error_msg]
            }

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

        Raises:
            ValueError: If required inputs are invalid
        """
        # Validate required inputs
        if not article_text or not article_text.strip():
            raise ValueError("article_text cannot be empty")
        if not journalist_question or not journalist_question.strip():
            raise ValueError("journalist_question cannot be empty")
        if not media_outlet or not media_outlet.strip():
            raise ValueError("media_outlet cannot be empty")
        if not executive_name or not executive_name.strip():
            raise ValueError("executive_name cannot be empty")

        # Validate lengths to prevent excessive LLM costs
        if len(article_text) > 50000:
            raise ValueError("article_text exceeds maximum length of 50,000 characters")
        if len(journalist_question) > 1000:
            raise ValueError("journalist_question exceeds maximum length of 1,000 characters")

        # Validate URL format if provided
        if article_url:
            from urllib.parse import urlparse
            try:
                result = urlparse(article_url)
                if not all([result.scheme, result.netloc]):
                    raise ValueError("article_url must be a valid URL")
            except Exception:
                raise ValueError("article_url is not a valid URL")

        # Validate email format if provided
        if pr_manager_email:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, pr_manager_email):
                raise ValueError("pr_manager_email is not a valid email address")
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

        # Check cache first
        cached_response = self.cache.get_cached_response(
            executive_name=executive_name,
            journalist_question=journalist_question,
            media_outlet=media_outlet
        )

        if cached_response:
            logger.info(
                "returning_cached_response",
                executive=executive_name,
                media_outlet=media_outlet,
                cache_hit=True
            )
            return cached_response

        # Run workflow
        logger.info(
            "workflow_started",
            executive=executive_name,
            media_outlet=media_outlet,
            workflow="generate_comment",
            cache_hit=False
        )

        final_state = self.workflow.invoke(initial_state)

        logger.info(
            "workflow_completed",
            executive=executive_name,
            media_outlet=media_outlet,
            email_sent=final_state.get('email_sent', False),
            errors_count=len(final_state.get('errors', []))
        )

        # Cache the successful response
        if final_state.get('humanized_comment'):
            self.cache.cache_response(
                response=final_state,
                ttl=self.config.cache_ttl_comments
            )

        return final_state

    async def generate_comment_async(
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
        Async version: Generate a PR comment using the complete workflow with parallel operations.

        This async implementation runs media and data research in parallel for 2-3x speedup.

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

        Raises:
            ValueError: If required inputs are invalid

        Example:
            >>> agent = PRCommentAgent()
            >>> result = await agent.generate_comment_async(
            ...     article_text="...",
            ...     journalist_question="...",
            ...     media_outlet="TechCrunch",
            ...     executive_name="Jane Doe"
            ... )
        """
        # Validate inputs (same as sync version)
        if not article_text or not article_text.strip():
            raise ValueError("article_text cannot be empty")
        if not journalist_question or not journalist_question.strip():
            raise ValueError("journalist_question cannot be empty")
        if not media_outlet or not media_outlet.strip():
            raise ValueError("media_outlet cannot be empty")
        if not executive_name or not executive_name.strip():
            raise ValueError("executive_name cannot be empty")

        if len(article_text) > 50000:
            raise ValueError("article_text exceeds maximum length of 50,000 characters")
        if len(journalist_question) > 1000:
            raise ValueError("journalist_question exceeds maximum length of 1,000 characters")

        if article_url:
            from urllib.parse import urlparse
            try:
                result = urlparse(article_url)
                if not all([result.scheme, result.netloc]):
                    raise ValueError("article_url must be a valid URL")
            except Exception:
                raise ValueError("article_url is not a valid URL")

        if pr_manager_email:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, pr_manager_email):
                raise ValueError("pr_manager_email is not a valid email address")

        logger.info(
            "async_workflow_started",
            executive=executive_name,
            media_outlet=media_outlet,
            workflow="generate_comment_async"
        )

        start_time = asyncio.get_event_loop().time()

        try:
            # Step 1: Load profile
            logger.info("loading_profile", executive=executive_name)
            executive_profile = self.profile_manager.load_profile(executive_name)
            logger.info("profile_loaded", executive=executive_name, success=True)

            # Step 2 & 3: Run media and data research IN PARALLEL
            logger.info("starting_parallel_research", executive=executive_name)

            topic = journalist_question[:100]
            perspective = executive_profile.get('talking_points', [''])[0]

            # Create parallel tasks
            media_task = self.media_researcher.research_async(
                media_outlet=media_outlet,
                journalist_name=journalist_name
            )
            data_task = self.data_researcher.research_supporting_data_async(
                topic=topic,
                context=article_text[:500],
                executive_perspective=perspective
            )

            # Run in parallel
            media_research, supporting_data = await asyncio.gather(
                media_task,
                data_task,
                return_exceptions=True
            )

            # Handle exceptions from parallel tasks
            if isinstance(media_research, Exception):
                logger.warning(
                    "media_research_failed",
                    error=str(media_research),
                    fallback="using_default"
                )
                media_research = {"analysis": "Media research unavailable"}

            if isinstance(supporting_data, Exception):
                logger.warning(
                    "data_research_failed",
                    error=str(supporting_data),
                    fallback="using_default"
                )
                supporting_data = {"curated_data": "No supporting data available"}

            logger.info(
                "parallel_research_complete",
                executive=executive_name,
                success=True
            )

            # Step 4: Draft comment
            logger.info("drafting_comment", executive=executive_name)
            drafted_comment = await self.comment_drafter.draft_comment_async(
                executive_name=executive_name,
                executive_profile=executive_profile,
                article_text=article_text,
                journalist_question=journalist_question,
                media_outlet=media_outlet,
                media_research=media_research,
                supporting_data=supporting_data
            )
            logger.info(
                "comment_drafted",
                executive=executive_name,
                comment_length=len(drafted_comment)
            )

            # Step 5: Humanize comment
            logger.info("humanizing_comment", executive=executive_name)
            try:
                humanized_comment = await self.humanizer.humanize_comment_async(
                    drafted_comment=drafted_comment,
                    executive_name=executive_name,
                    executive_profile=executive_profile
                )
                logger.info(
                    "comment_humanized",
                    executive=executive_name,
                    humanized_length=len(humanized_comment)
                )
            except Exception as e:
                logger.warning(
                    "humanization_failed",
                    error=str(e),
                    fallback="using_drafted_comment"
                )
                humanized_comment = drafted_comment

            # Step 6: Send email
            email_sent = False
            pr_email = pr_manager_email or self.config.pr_manager_email

            if pr_email:
                logger.info("sending_email", recipient=pr_email)
                try:
                    email_sent = await self.email_sender.send_comment_for_approval_async(
                        pr_manager_email=pr_email,
                        executive_name=executive_name,
                        journalist_question=journalist_question,
                        media_outlet=media_outlet,
                        drafted_comment=drafted_comment,
                        humanized_comment=humanized_comment,
                        article_url=article_url
                    )
                    logger.info("email_sent", success=email_sent, recipient=pr_email)
                except Exception as e:
                    logger.error(
                        "email_send_failed",
                        error=str(e),
                        error_type=type(e).__name__
                    )
            else:
                logger.warning("email_skipped", reason="no_pr_manager_email")

            # Calculate duration
            duration = asyncio.get_event_loop().time() - start_time

            logger.info(
                "async_workflow_completed",
                executive=executive_name,
                media_outlet=media_outlet,
                duration_seconds=round(duration, 2),
                email_sent=email_sent,
                success=True
            )

            # Return result in same format as sync version
            return {
                "article_text": article_text,
                "article_url": article_url,
                "journalist_question": journalist_question,
                "media_outlet": media_outlet,
                "journalist_name": journalist_name,
                "executive_name": executive_name,
                "executive_profile": executive_profile,
                "media_research": media_research,
                "supporting_data": supporting_data,
                "drafted_comment": drafted_comment,
                "humanized_comment": humanized_comment,
                "timestamp": datetime.now().isoformat(),
                "approval_status": "pending",
                "email_sent": email_sent,
                "pr_manager_email": pr_email,
                "current_step": "completed",
                "errors": [],
                "duration_seconds": round(duration, 2)
            }

        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            logger.error(
                "async_workflow_failed",
                executive=executive_name,
                media_outlet=media_outlet,
                duration_seconds=round(duration, 2),
                error=str(e),
                error_type=type(e).__name__
            )
            raise

    async def generate_comment_stream(
        self,
        article_text: str,
        journalist_question: str,
        media_outlet: str,
        executive_name: str,
        article_url: Optional[str] = None,
        journalist_name: Optional[str] = None,
        pr_manager_email: Optional[str] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream PR comment generation with real-time progress updates and token streaming.

        This method provides real-time feedback as each step completes and streams
        the actual comment text as it's being generated, enabling better UX.

        Args:
            article_text: The article content
            journalist_question: Question from the journalist
            media_outlet: Name of the media outlet
            executive_name: Name of the executive providing the comment
            article_url: Optional URL to the article
            journalist_name: Optional name of the journalist
            pr_manager_email: Optional email override for PR manager

        Yields:
            Progress events in the format:
            {
                "event": "started|streaming|completed|finished",
                "step": "profile|research|drafting|humanizing|email",
                "content": "...",  # For streaming events
                "data": {...}      # For completed/finished events
            }

        Example:
            >>> agent = PRCommentAgent()
            >>> async for event in agent.generate_comment_stream(...):
            ...     if event["event"] == "streaming":
            ...         print(event["content"], end='', flush=True)
            ...     else:
            ...         print(f"\\nStep {event['step']}: {event['event']}")
        """
        # Validate inputs (same as other methods)
        if not article_text or not article_text.strip():
            raise ValueError("article_text cannot be empty")
        if not journalist_question or not journalist_question.strip():
            raise ValueError("journalist_question cannot be empty")
        if not media_outlet or not media_outlet.strip():
            raise ValueError("media_outlet cannot be empty")
        if not executive_name or not executive_name.strip():
            raise ValueError("executive_name cannot be empty")

        if len(article_text) > 50000:
            raise ValueError("article_text exceeds maximum length of 50,000 characters")
        if len(journalist_question) > 1000:
            raise ValueError("journalist_question exceeds maximum length of 1,000 characters")

        logger.info(
            "streaming_workflow_started",
            executive=executive_name,
            media_outlet=media_outlet
        )

        start_time = asyncio.get_event_loop().time()

        try:
            # Step 1: Load profile
            yield {"event": "started", "step": "profile"}
            logger.info("loading_profile_stream", executive=executive_name)

            executive_profile = self.profile_manager.load_profile(executive_name)

            yield {
                "event": "completed",
                "step": "profile",
                "data": {"executive_name": executive_name}
            }

            # Step 2: Research (parallel)
            yield {"event": "started", "step": "research"}
            logger.info("starting_research_stream", executive=executive_name)

            topic = journalist_question[:100]
            perspective = executive_profile.get('talking_points', [''])[0]

            # Run research in parallel
            media_task = self.media_researcher.research_async(
                media_outlet=media_outlet,
                journalist_name=journalist_name
            )
            data_task = self.data_researcher.research_supporting_data_async(
                topic=topic,
                context=article_text[:500],
                executive_perspective=perspective
            )

            media_research, supporting_data = await asyncio.gather(
                media_task,
                data_task,
                return_exceptions=True
            )

            # Handle exceptions
            if isinstance(media_research, Exception):
                logger.warning("media_research_failed_stream", error=str(media_research))
                media_research = {"analysis": "Media research unavailable"}

            if isinstance(supporting_data, Exception):
                logger.warning("data_research_failed_stream", error=str(supporting_data))
                supporting_data = {"curated_data": "No supporting data available"}

            yield {"event": "completed", "step": "research"}

            # Step 3: Draft comment with streaming
            yield {"event": "started", "step": "drafting"}
            logger.info("drafting_comment_stream", executive=executive_name)

            drafted_comment_chunks = []
            async for chunk in self.comment_drafter.draft_comment_stream(
                executive_name=executive_name,
                executive_profile=executive_profile,
                article_text=article_text,
                journalist_question=journalist_question,
                media_outlet=media_outlet,
                media_research=media_research,
                supporting_data=supporting_data
            ):
                drafted_comment_chunks.append(chunk)
                yield {
                    "event": "streaming",
                    "step": "drafting",
                    "content": chunk
                }

            drafted_comment = "".join(drafted_comment_chunks).strip()
            yield {
                "event": "completed",
                "step": "drafting",
                "data": {"drafted_comment": drafted_comment}
            }

            # Step 4: Humanize comment with streaming
            yield {"event": "started", "step": "humanizing"}
            logger.info("humanizing_comment_stream", executive=executive_name)

            humanized_comment_chunks = []
            try:
                async for chunk in self.humanizer.humanize_comment_stream(
                    drafted_comment=drafted_comment,
                    executive_name=executive_name,
                    executive_profile=executive_profile
                ):
                    humanized_comment_chunks.append(chunk)
                    yield {
                        "event": "streaming",
                        "step": "humanizing",
                        "content": chunk
                    }

                humanized_comment = "".join(humanized_comment_chunks).strip()
            except Exception as e:
                logger.warning("humanization_failed_stream", error=str(e))
                humanized_comment = drafted_comment

            yield {
                "event": "completed",
                "step": "humanizing",
                "data": {"humanized_comment": humanized_comment}
            }

            # Step 5: Send email
            email_sent = False
            pr_email = pr_manager_email or self.config.pr_manager_email

            if pr_email:
                yield {"event": "started", "step": "email"}
                logger.info("sending_email_stream", recipient=pr_email)

                try:
                    email_sent = await self.email_sender.send_comment_for_approval_async(
                        pr_manager_email=pr_email,
                        executive_name=executive_name,
                        journalist_question=journalist_question,
                        media_outlet=media_outlet,
                        drafted_comment=drafted_comment,
                        humanized_comment=humanized_comment,
                        article_url=article_url
                    )
                    yield {
                        "event": "completed",
                        "step": "email",
                        "data": {"email_sent": email_sent}
                    }
                except Exception as e:
                    logger.error("email_send_failed_stream", error=str(e))
                    yield {
                        "event": "completed",
                        "step": "email",
                        "data": {"email_sent": False, "error": str(e)}
                    }

            # Final result
            duration = asyncio.get_event_loop().time() - start_time

            final_result = {
                "article_text": article_text,
                "article_url": article_url,
                "journalist_question": journalist_question,
                "media_outlet": media_outlet,
                "journalist_name": journalist_name,
                "executive_name": executive_name,
                "executive_profile": executive_profile,
                "media_research": media_research,
                "supporting_data": supporting_data,
                "drafted_comment": drafted_comment,
                "humanized_comment": humanized_comment,
                "timestamp": datetime.now().isoformat(),
                "approval_status": "pending",
                "email_sent": email_sent,
                "pr_manager_email": pr_email,
                "current_step": "completed",
                "errors": [],
                "duration_seconds": round(duration, 2)
            }

            yield {
                "event": "finished",
                "step": "complete",
                "data": final_result
            }

            logger.info(
                "streaming_workflow_completed",
                executive=executive_name,
                media_outlet=media_outlet,
                duration_seconds=round(duration, 2)
            )

        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            logger.error(
                "streaming_workflow_failed",
                executive=executive_name,
                media_outlet=media_outlet,
                duration_seconds=round(duration, 2),
                error=str(e),
                error_type=type(e).__name__
            )
            raise

    async def generate_comment_with_memory_and_evaluation(
        self,
        article_text: str,
        journalist_question: str,
        media_outlet: str,
        executive_name: str,
        session_id: Optional[str] = None,
        article_url: Optional[str] = None,
        journalist_name: Optional[str] = None,
        pr_manager_email: Optional[str] = None,
        enable_evaluation: bool = True
    ) -> Dict[str, Any]:
        """
        Generate PR comment with Phase 3 features: memory, RAG, and evaluation.

        This method integrates:
        - Memory: Retrieves similar past comments and maintains conversation history
        - RAG: Augments context with relevant examples and media knowledge
        - Evaluation: Automatically evaluates comment quality

        Args:
            article_text: The article content
            journalist_question: Question from the journalist
            media_outlet: Name of the media outlet
            executive_name: Name of the executive providing the comment
            session_id: Session ID for conversation tracking (optional)
            article_url: Optional URL to the article
            journalist_name: Optional name of the journalist
            pr_manager_email: Optional email override for PR manager
            enable_evaluation: Whether to run evaluation (default: True)

        Returns:
            Dictionary with results including memory, RAG, and evaluation data

        Example:
            >>> agent = PRCommentAgent()
            >>> result = await agent.generate_comment_with_memory_and_evaluation(
            ...     article_text="...",
            ...     journalist_question="...",
            ...     media_outlet="TechCrunch",
            ...     executive_name="Jane Doe",
            ...     session_id="session_123"
            ... )
            >>> print(result['humanized_comment'])
            >>> print(result['evaluation_scores'])
        """
        # Validate inputs (reuse existing validation logic)
        if not article_text or not article_text.strip():
            raise ValueError("article_text cannot be empty")
        if not journalist_question or not journalist_question.strip():
            raise ValueError("journalist_question cannot be empty")
        if not media_outlet or not media_outlet.strip():
            raise ValueError("media_outlet cannot be empty")
        if not executive_name or not executive_name.strip():
            raise ValueError("executive_name cannot be empty")

        if len(article_text) > 50000:
            raise ValueError("article_text exceeds maximum length of 50,000 characters")
        if len(journalist_question) > 1000:
            raise ValueError("journalist_question exceeds maximum length of 1,000 characters")

        # Generate session ID if not provided
        if not session_id:
            import uuid
            session_id = f"session_{uuid.uuid4().hex[:8]}"

        logger.info(
            "phase3_workflow_started",
            executive=executive_name,
            media_outlet=media_outlet,
            session_id=session_id,
            memory_enabled=self.memory.enabled if self.memory else False,
            rag_enabled=self.rag.enabled if self.rag else False,
            evaluation_enabled=enable_evaluation and (self.evaluator.enabled if self.evaluator else False)
        )

        start_time = asyncio.get_event_loop().time()

        try:
            # Phase 3 Step 1: Retrieve similar comments from memory
            past_comments = []
            if self.memory and self.memory.enabled:
                logger.info("retrieving_memory", session_id=session_id)
                past_comments = await self.memory.retrieve_similar_comments(
                    question=journalist_question,
                    executive_name=executive_name,
                    media_outlet=media_outlet,
                    k=3
                )
                logger.info(
                    "memory_retrieved",
                    past_comments_count=len(past_comments)
                )

            # Phase 3 Step 2: Augment context with RAG
            rag_context = {"enabled": False}
            if self.rag and self.rag.enabled:
                logger.info("augmenting_with_rag", executive=executive_name)
                rag_context = await self.rag.augment_with_context(
                    journalist_question=journalist_question,
                    executive_name=executive_name,
                    media_outlet=media_outlet,
                    journalist_name=journalist_name
                )
                logger.info(
                    "rag_context_augmented",
                    similar_comments=rag_context.get("retrieval_counts", {}).get("similar_comments", 0),
                    media_knowledge=rag_context.get("retrieval_counts", {}).get("media_knowledge", 0),
                    examples=rag_context.get("retrieval_counts", {}).get("examples", 0)
                )

            # Step 3: Load profile
            logger.info("loading_profile", executive=executive_name)
            executive_profile = self.profile_manager.load_profile(executive_name)

            # Step 4 & 5: Run research in parallel
            logger.info("starting_parallel_research")

            topic = journalist_question[:100]
            perspective = executive_profile.get('talking_points', [''])[0]

            media_task = self.media_researcher.research_async(
                media_outlet=media_outlet,
                journalist_name=journalist_name
            )
            data_task = self.data_researcher.research_supporting_data_async(
                topic=topic,
                context=article_text[:500],
                executive_perspective=perspective
            )

            media_research, supporting_data = await asyncio.gather(
                media_task,
                data_task,
                return_exceptions=True
            )

            # Handle exceptions
            if isinstance(media_research, Exception):
                logger.warning("media_research_failed", error=str(media_research))
                media_research = {"analysis": "Media research unavailable"}

            if isinstance(supporting_data, Exception):
                logger.warning("data_research_failed", error=str(supporting_data))
                supporting_data = {"curated_data": "No supporting data available"}

            # Step 6: Draft comment
            logger.info("drafting_comment")
            drafted_comment = await self.comment_drafter.draft_comment_async(
                executive_name=executive_name,
                executive_profile=executive_profile,
                article_text=article_text,
                journalist_question=journalist_question,
                media_outlet=media_outlet,
                media_research=media_research,
                supporting_data=supporting_data
            )

            # Step 7: Humanize comment
            logger.info("humanizing_comment")
            try:
                humanized_comment = await self.humanizer.humanize_comment_async(
                    drafted_comment=drafted_comment,
                    executive_name=executive_name,
                    executive_profile=executive_profile
                )
            except Exception as e:
                logger.warning("humanization_failed", error=str(e))
                humanized_comment = drafted_comment

            # Phase 3 Step 8: Evaluate comment quality
            evaluation_results = {"enabled": False}
            if enable_evaluation and self.evaluator and self.evaluator.enabled:
                logger.info("evaluating_comment")
                try:
                    evaluation_results = await self.evaluator.evaluate_comment(
                        comment=humanized_comment,
                        journalist_question=journalist_question,
                        executive_profile=executive_profile,
                        supporting_data=supporting_data,
                        article_text=article_text
                    )
                    logger.info(
                        "evaluation_complete",
                        overall_score=evaluation_results.get("overall_score", 0.0),
                        passed=evaluation_results.get("overall_passed", False)
                    )
                except Exception as e:
                    logger.error("evaluation_failed", error=str(e))
                    evaluation_results = {"enabled": True, "error": str(e)}

            # Phase 3 Step 9: Save to memory
            if self.memory and self.memory.enabled:
                logger.info("saving_to_memory", session_id=session_id)
                try:
                    # Save to short-term memory
                    await self.memory.save_to_short_term(
                        session_id=session_id,
                        question=journalist_question,
                        comment=humanized_comment
                    )

                    # Save successful comments to long-term memory
                    if evaluation_results.get("overall_passed", True):
                        await self.memory.save_to_long_term(
                            executive_name=executive_name,
                            media_outlet=media_outlet,
                            journalist_question=journalist_question,
                            comment=humanized_comment,
                            metadata={
                                "evaluation_score": evaluation_results.get("overall_score", 0.0),
                                "session_id": session_id
                            }
                        )
                    logger.info("memory_saved")
                except Exception as e:
                    logger.error("memory_save_failed", error=str(e))

            # Phase 3 Step 10: Save to RAG
            if self.rag and self.rag.enabled and evaluation_results.get("overall_passed", True):
                logger.info("saving_to_rag")
                try:
                    await self.rag.store_comment(
                        executive_name=executive_name,
                        media_outlet=media_outlet,
                        journalist_question=journalist_question,
                        comment=humanized_comment,
                        metadata={
                            "evaluation_score": evaluation_results.get("overall_score", 0.0),
                            "session_id": session_id
                        }
                    )
                    logger.info("rag_saved")
                except Exception as e:
                    logger.error("rag_save_failed", error=str(e))

            # Step 11: Send email
            email_sent = False
            pr_email = pr_manager_email or self.config.pr_manager_email

            if pr_email:
                logger.info("sending_email", recipient=pr_email)
                try:
                    email_sent = await self.email_sender.send_comment_for_approval_async(
                        pr_manager_email=pr_email,
                        executive_name=executive_name,
                        journalist_question=journalist_question,
                        media_outlet=media_outlet,
                        drafted_comment=drafted_comment,
                        humanized_comment=humanized_comment,
                        article_url=article_url
                    )
                    logger.info("email_sent", success=email_sent)
                except Exception as e:
                    logger.error("email_send_failed", error=str(e))

            # Get conversation history
            conversation_history = []
            if self.memory and self.memory.enabled:
                conversation_history = self.memory.get_conversation_history(session_id)

            # Calculate duration
            duration = asyncio.get_event_loop().time() - start_time

            # Build comprehensive result
            result = {
                "article_text": article_text,
                "article_url": article_url,
                "journalist_question": journalist_question,
                "media_outlet": media_outlet,
                "journalist_name": journalist_name,
                "executive_name": executive_name,
                "executive_profile": executive_profile,
                "media_research": media_research,
                "supporting_data": supporting_data,
                "drafted_comment": drafted_comment,
                "humanized_comment": humanized_comment,
                "timestamp": datetime.now().isoformat(),
                "approval_status": "pending",
                "email_sent": email_sent,
                "pr_manager_email": pr_email,
                "current_step": "completed",
                "errors": [],
                "duration_seconds": round(duration, 2),
                # Phase 3 additions
                "session_id": session_id,
                "past_comments": past_comments,
                "rag_context": rag_context,
                "conversation_history": conversation_history,
                "evaluation_scores": evaluation_results,
                "phase3_enabled": {
                    "memory": self.memory.enabled if self.memory else False,
                    "rag": self.rag.enabled if self.rag else False,
                    "evaluation": evaluation_results.get("enabled", False)
                }
            }

            logger.info(
                "phase3_workflow_completed",
                executive=executive_name,
                media_outlet=media_outlet,
                session_id=session_id,
                duration_seconds=round(duration, 2),
                evaluation_score=evaluation_results.get("overall_score", 0.0),
                email_sent=email_sent
            )

            return result

        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            logger.error(
                "phase3_workflow_failed",
                executive=executive_name,
                media_outlet=media_outlet,
                session_id=session_id,
                duration_seconds=round(duration, 2),
                error=str(e),
                error_type=type(e).__name__
            )
            raise

    def get_phase3_stats(self) -> Dict[str, Any]:
        """
        Get statistics for Phase 3 features.

        Returns:
            Dictionary with memory, RAG, and evaluation stats
        """
        stats = {
            "memory": None,
            "rag": None,
            "evaluator": None
        }

        try:
            if self.memory:
                stats["memory"] = self.memory.get_memory_stats()

            if self.rag:
                stats["rag"] = self.rag.get_rag_stats()

            if self.evaluator:
                stats["evaluator"] = {
                    "enabled": self.evaluator.enabled,
                    "model": self.config.evaluation_model if self.evaluator.enabled else None
                }

            logger.info("phase3_stats_retrieved")

            return stats

        except Exception as e:
            logger.error(
                "phase3_stats_retrieval_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            return {"error": str(e)}
