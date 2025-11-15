"""
LangSmith observability integration for PR Agent.

Provides tracing utilities and decorators for monitoring LLM calls and agent workflows.
"""

import os
import functools
from typing import Any, Callable, Optional, Dict
from contextlib import contextmanager

from langsmith import traceable
from langsmith.run_helpers import get_current_run_tree

from .logging_config import get_logger

logger = get_logger(__name__)


def configure_langsmith(
    api_key: Optional[str] = None,
    project: str = "pr-agent-production",
    enable_tracing: bool = True
) -> bool:
    """
    Configure LangSmith tracing.

    Args:
        api_key: LangSmith API key (or set LANGSMITH_API_KEY env var)
        project: Project name for organizing traces
        enable_tracing: Whether to enable tracing

    Returns:
        True if configured successfully, False otherwise

    Example:
        >>> configure_langsmith(project="pr-agent-dev")
        True
    """
    try:
        if not enable_tracing:
            os.environ["LANGCHAIN_TRACING_V2"] = "false"
            logger.info("langsmith_disabled", reason="tracing_disabled_in_config")
            return False

        # Set LangSmith API key
        if api_key:
            os.environ["LANGSMITH_API_KEY"] = api_key
        elif not os.getenv("LANGSMITH_API_KEY"):
            logger.warning(
                "langsmith_not_configured",
                reason="no_api_key",
                message="Set LANGSMITH_API_KEY to enable tracing"
            )
            os.environ["LANGCHAIN_TRACING_V2"] = "false"
            return False

        # Enable tracing
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = project

        logger.info(
            "langsmith_configured",
            project=project,
            tracing_enabled=True
        )
        return True

    except Exception as e:
        logger.error(
            "langsmith_configuration_failed",
            error=str(e),
            error_type=type(e).__name__
        )
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        return False


def trace_agent_step(
    step_name: str,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Decorator to trace individual agent workflow steps.

    Args:
        step_name: Name of the step being traced
        metadata: Additional metadata to include in trace

    Example:
        @trace_agent_step("load_profile", metadata={"version": "v1"})
        async def load_profile(state):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        @traceable(
            name=step_name,
            metadata=metadata or {},
            tags=["agent-step", step_name]
        )
        async def async_wrapper(*args, **kwargs):
            logger.info(
                "trace_step_start",
                step=step_name,
                function=func.__name__
            )
            try:
                result = await func(*args, **kwargs)
                logger.info(
                    "trace_step_complete",
                    step=step_name,
                    function=func.__name__,
                    success=True
                )
                return result
            except Exception as e:
                logger.error(
                    "trace_step_failed",
                    step=step_name,
                    function=func.__name__,
                    error=str(e),
                    error_type=type(e).__name__
                )
                raise

        @functools.wraps(func)
        @traceable(
            name=step_name,
            metadata=metadata or {},
            tags=["agent-step", step_name]
        )
        def sync_wrapper(*args, **kwargs):
            logger.info(
                "trace_step_start",
                step=step_name,
                function=func.__name__
            )
            try:
                result = func(*args, **kwargs)
                logger.info(
                    "trace_step_complete",
                    step=step_name,
                    function=func.__name__,
                    success=True
                )
                return result
            except Exception as e:
                logger.error(
                    "trace_step_failed",
                    step=step_name,
                    function=func.__name__,
                    error=str(e),
                    error_type=type(e).__name__
                )
                raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def trace_llm_call(
    agent_name: str,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Decorator to trace LLM API calls.

    Args:
        agent_name: Name of the agent making the call
        metadata: Additional metadata to include in trace

    Example:
        @trace_llm_call("media_researcher", metadata={"model": "gpt-4o"})
        async def research_media(self, outlet):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        @traceable(
            name=f"{agent_name}_llm_call",
            metadata=metadata or {},
            tags=["llm-call", agent_name]
        )
        async def async_wrapper(*args, **kwargs):
            logger.debug(
                "llm_call_start",
                agent=agent_name,
                function=func.__name__
            )
            try:
                result = await func(*args, **kwargs)
                logger.debug(
                    "llm_call_complete",
                    agent=agent_name,
                    function=func.__name__,
                    success=True
                )
                return result
            except Exception as e:
                logger.error(
                    "llm_call_failed",
                    agent=agent_name,
                    function=func.__name__,
                    error=str(e),
                    error_type=type(e).__name__
                )
                raise

        @functools.wraps(func)
        @traceable(
            name=f"{agent_name}_llm_call",
            metadata=metadata or {},
            tags=["llm-call", agent_name]
        )
        def sync_wrapper(*args, **kwargs):
            logger.debug(
                "llm_call_start",
                agent=agent_name,
                function=func.__name__
            )
            try:
                result = func(*args, **kwargs)
                logger.debug(
                    "llm_call_complete",
                    agent=agent_name,
                    function=func.__name__,
                    success=True
                )
                return result
            except Exception as e:
                logger.error(
                    "llm_call_failed",
                    agent=agent_name,
                    function=func.__name__,
                    error=str(e),
                    error_type=type(e).__name__
                )
                raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


@contextmanager
def trace_workflow(
    workflow_name: str,
    executive: Optional[str] = None,
    media_outlet: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Context manager for tracing entire workflows.

    Args:
        workflow_name: Name of the workflow
        executive: Executive name (optional)
        media_outlet: Media outlet name (optional)
        metadata: Additional metadata

    Example:
        with trace_workflow("generate_comment", executive="John Doe", media_outlet="TechCrunch"):
            result = await agent.generate_comment_async(...)
    """
    trace_metadata = metadata or {}
    if executive:
        trace_metadata["executive"] = executive
    if media_outlet:
        trace_metadata["media_outlet"] = media_outlet

    logger.info(
        "workflow_start",
        workflow=workflow_name,
        executive=executive,
        media_outlet=media_outlet
    )

    try:
        yield
        logger.info(
            "workflow_complete",
            workflow=workflow_name,
            executive=executive,
            media_outlet=media_outlet,
            success=True
        )
    except Exception as e:
        logger.error(
            "workflow_failed",
            workflow=workflow_name,
            executive=executive,
            media_outlet=media_outlet,
            error=str(e),
            error_type=type(e).__name__
        )
        raise


def add_trace_metadata(**metadata: Any) -> None:
    """
    Add metadata to the current trace.

    Args:
        **metadata: Key-value pairs to add to the current trace

    Example:
        add_trace_metadata(executive="John Doe", media_outlet="TechCrunch")
    """
    try:
        run_tree = get_current_run_tree()
        if run_tree:
            for key, value in metadata.items():
                run_tree.add_metadata(key, value)
    except Exception as e:
        logger.warning(
            "failed_to_add_trace_metadata",
            error=str(e),
            metadata=metadata
        )


def trace_search_call(func: Callable) -> Callable:
    """
    Decorator specifically for search API calls.

    Example:
        @trace_search_call
        async def search_for_data_async(self, query):
            ...
    """
    @functools.wraps(func)
    @traceable(
        name="search_api_call",
        tags=["search", "external-api"]
    )
    async def async_wrapper(*args, **kwargs):
        # Extract query if possible
        query = kwargs.get('query') or (args[1] if len(args) > 1 else 'unknown')
        logger.debug("search_call_start", query=query)
        try:
            result = await func(*args, **kwargs)
            result_count = len(result) if isinstance(result, list) else 0
            logger.debug(
                "search_call_complete",
                query=query,
                result_count=result_count,
                success=True
            )
            return result
        except Exception as e:
            logger.error(
                "search_call_failed",
                query=query,
                error=str(e),
                error_type=type(e).__name__
            )
            raise

    @functools.wraps(func)
    @traceable(
        name="search_api_call",
        tags=["search", "external-api"]
    )
    def sync_wrapper(*args, **kwargs):
        query = kwargs.get('query') or (args[1] if len(args) > 1 else 'unknown')
        logger.debug("search_call_start", query=query)
        try:
            result = func(*args, **kwargs)
            result_count = len(result) if isinstance(result, list) else 0
            logger.debug(
                "search_call_complete",
                query=query,
                result_count=result_count,
                success=True
            )
            return result
        except Exception as e:
            logger.error(
                "search_call_failed",
                query=query,
                error=str(e),
                error_type=type(e).__name__
            )
            raise

    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper
