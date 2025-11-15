# LangChain/LangGraph Improvements for PR Agent System

This document outlines recommended improvements to modernize the PR Agent System with latest LangChain 0.1+ and LangGraph best practices.

## Current Architecture Analysis

### Strengths
- ✅ Uses LangGraph StateGraph with TypedDict state management
- ✅ Linear workflow with clear separation of concerns
- ✅ Graceful error handling with fallbacks
- ✅ Executive profile system for consistent voice
- ✅ Clean separation between agents, tools, and state

### Areas for Improvement
1. **No async implementation** - All operations are synchronous
2. **No observability** - Missing LangSmith tracing and monitoring
3. **Suboptimal model choices** - Uses hardcoded models without optimization
4. **No caching** - Repeated queries hit APIs every time
5. **Limited memory** - No conversation history or context retention
6. **No streaming** - Cannot provide real-time feedback to users
7. **Basic error handling** - Could benefit from retry logic and circuit breakers
8. **No evaluation framework** - No testing or quality metrics

## Recommended Improvements

### 1. Async Implementation (High Priority)

**Current**: Synchronous operations block execution
```python
def generate_comment(self, article_text: str, ...) -> Dict[str, Any]:
    final_state = self.workflow.invoke(initial_state)
    return final_state
```

**Improved**: Full async with concurrent operations
```python
async def generate_comment_async(
    self,
    article_text: str,
    ...
) -> Dict[str, Any]:
    """Generate PR comment with async operations."""
    # Run media and data research concurrently
    media_task = asyncio.create_task(
        self.media_researcher.research_async(media_outlet, journalist_name)
    )
    data_task = asyncio.create_task(
        self.data_researcher.research_async(topic, context)
    )

    # Await both in parallel
    media_research, supporting_data = await asyncio.gather(
        media_task, data_task, return_exceptions=True
    )

    # Invoke workflow asynchronously
    final_state = await self.workflow.ainvoke(initial_state)
    return final_state
```

**Benefits**:
- 2-3x faster execution (media + data research in parallel)
- Better resource utilization
- Non-blocking operations

**Implementation Steps**:
1. Convert all agent methods to `async def`
2. Use `ainvoke()` instead of `invoke()` for LLM calls
3. Use `asyncio.gather()` for parallel operations
4. Update EmailSender to use `aiosmtplib`
5. Make search tools async with `httpx` or `aiohttp`

### 2. LangSmith Observability (High Priority)

**Add comprehensive tracing and monitoring**:

```python
import os
from langsmith import Client

# In config.py
@dataclass
class PRAgentConfig:
    # ... existing fields ...

    # LangSmith configuration
    langsmith_api_key: Optional[str] = field(
        default_factory=lambda: os.getenv("LANGSMITH_API_KEY")
    )
    langsmith_project: str = "pr-agent-production"
    enable_tracing: bool = True

# In agent.py
def __init__(self, config: Optional[PRAgentConfig] = None):
    self.config = config or PRAgentConfig()

    # Configure LangSmith
    if self.config.langsmith_api_key and self.config.enable_tracing:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = self.config.langsmith_api_key
        os.environ["LANGCHAIN_PROJECT"] = self.config.langsmith_project

    # ... rest of initialization ...

async def generate_comment(self, ...):
    """Generate PR comment with full tracing."""
    from langsmith import traceable

    @traceable(
        name="pr_comment_generation",
        tags=["pr-agent", "production"],
        metadata={
            "executive": executive_name,
            "media_outlet": media_outlet
        }
    )
    async def _traced_generation():
        return await self.workflow.ainvoke(initial_state)

    return await _traced_generation()
```

**Benefits**:
- Debug failures with complete execution traces
- Monitor performance bottlenecks
- Track LLM costs per request
- Analyze quality metrics over time

### 3. Model Optimization (Medium Priority)

**Current**: Uses GPT-4o or hardcoded Claude model

**Improved**: Use Claude Sonnet 4.5 with Voyage AI embeddings
```python
# In config.py
@dataclass
class PRAgentConfig:
    # Updated model configuration
    model_name: str = "claude-sonnet-4-5"  # Latest Claude model
    embedding_model: str = "voyage-3-large"  # Anthropic-recommended

    # Temperature tuning
    temperature: float = 0.7
    humanizer_temperature: float = 0.9

    # Token limits for cost control
    max_tokens: int = 4096
    max_input_tokens: int = 50000

# In agent.py - enhanced LLM creation
def _create_llm(self, temperature: float = 0.7):
    """Create optimized LLM instance."""
    if self.config.anthropic_api_key:
        return ChatAnthropic(
            model=self.config.model_name,  # claude-sonnet-4-5
            temperature=temperature,
            max_tokens=self.config.max_tokens,
            api_key=self.config.anthropic_api_key,
            # Add streaming support
            streaming=True,
            # Configure retries
            max_retries=3,
            timeout=60.0
        )
    # ... OpenAI fallback ...
```

**Cost Optimization**:
```python
# Add token counting and limits
from anthropic import count_tokens

def _check_token_limit(self, text: str, max_tokens: int = 50000):
    """Validate input doesn't exceed token limits."""
    token_count = count_tokens(text)
    if token_count > max_tokens:
        raise ValueError(
            f"Input exceeds token limit: {token_count} > {max_tokens}"
        )
    return token_count
```

### 4. Caching Layer (Medium Priority)

**Add Redis caching for expensive operations**:

```python
# New file: pr_agent/cache.py
import redis
import json
import hashlib
from typing import Optional, Any
from datetime import timedelta

class PRAgentCache:
    """Redis cache for PR agent responses."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url, decode_responses=True)

    def _make_key(self, prefix: str, **kwargs) -> str:
        """Create cache key from parameters."""
        data = json.dumps(kwargs, sort_keys=True)
        hash_val = hashlib.sha256(data.encode()).hexdigest()[:16]
        return f"pr_agent:{prefix}:{hash_val}"

    async def get_cached_response(
        self,
        executive_name: str,
        journalist_question: str,
        media_outlet: str
    ) -> Optional[dict]:
        """Retrieve cached comment if available."""
        key = self._make_key(
            "comment",
            executive=executive_name,
            question=journalist_question,
            outlet=media_outlet
        )
        cached = self.redis.get(key)
        return json.loads(cached) if cached else None

    async def cache_response(
        self,
        response: dict,
        ttl: int = 3600  # 1 hour
    ):
        """Cache generated comment."""
        key = self._make_key(
            "comment",
            executive=response["executive_name"],
            question=response["journalist_question"],
            outlet=response["media_outlet"]
        )
        self.redis.setex(
            key,
            ttl,
            json.dumps(response)
        )

    async def cache_search_results(
        self,
        query: str,
        results: list,
        ttl: int = 86400  # 24 hours
    ):
        """Cache search results."""
        key = self._make_key("search", query=query)
        self.redis.setex(key, ttl, json.dumps(results))

# In agent.py
async def generate_comment(self, ...):
    """Generate comment with caching."""
    # Check cache first
    cached = await self.cache.get_cached_response(
        executive_name, journalist_question, media_outlet
    )
    if cached:
        logger.info("Returning cached response")
        return cached

    # Generate new response
    result = await self.workflow.ainvoke(initial_state)

    # Cache for future requests
    await self.cache.cache_response(result, ttl=3600)

    return result
```

**Benefits**:
- 10-100x faster for repeated queries
- Significant cost savings on LLM API calls
- Reduced load on search APIs

### 5. Streaming Support (High Priority for UX)

**Add streaming for real-time feedback**:

```python
from typing import AsyncIterator
from langchain_core.messages import AIMessageChunk

async def generate_comment_stream(
    self,
    article_text: str,
    journalist_question: str,
    ...
) -> AsyncIterator[dict]:
    """
    Stream PR comment generation with progress updates.

    Yields progress events and final result.
    """
    # Yield progress events
    yield {"event": "started", "step": "loading_profile"}

    # Load profile
    profile = self.profile_manager.load_profile(executive_name)
    yield {"event": "completed", "step": "profile_loaded"}

    # Research (parallel)
    yield {"event": "started", "step": "research"}
    media_research, supporting_data = await asyncio.gather(
        self.media_researcher.research_async(...),
        self.data_researcher.research_async(...)
    )
    yield {"event": "completed", "step": "research_completed"}

    # Draft comment with streaming
    yield {"event": "started", "step": "drafting"}
    async for chunk in self.comment_drafter.draft_comment_stream(...):
        yield {"event": "streaming", "step": "drafting", "content": chunk}
    yield {"event": "completed", "step": "drafted"}

    # Humanize
    yield {"event": "started", "step": "humanizing"}
    async for chunk in self.humanizer.humanize_stream(...):
        yield {"event": "streaming", "step": "humanizing", "content": chunk}
    yield {"event": "completed", "step": "humanized"}

    # Final result
    yield {"event": "finished", "result": final_comment}
```

**FastAPI endpoint for streaming**:
```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

@app.post("/agent/stream")
async def stream_comment(request: CommentRequest):
    """Stream PR comment generation."""
    async def event_stream():
        async for event in agent.generate_comment_stream(
            article_text=request.article_text,
            journalist_question=request.question,
            ...
        ):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream"
    )
```

### 6. Enhanced Memory System (Low Priority)

**Add conversation memory for interactive refinement**:

```python
from langchain.memory import ConversationTokenBufferMemory
from langchain_voyageai import VoyageAIEmbeddings
from langchain.memory import VectorStoreRetrieverMemory

class PRAgentWithMemory:
    """PR Agent with conversation memory."""

    def __init__(self, config: PRAgentConfig):
        # Token-based memory for recent context
        self.short_term_memory = ConversationTokenBufferMemory(
            llm=self.main_llm,
            max_token_limit=2000,
            return_messages=True
        )

        # Vector memory for semantic search across past comments
        embeddings = VoyageAIEmbeddings(model="voyage-3-large")
        self.long_term_memory = VectorStoreRetrieverMemory(
            retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
            input_key="question",
            output_key="comment"
        )

    async def generate_comment_with_memory(
        self,
        article_text: str,
        session_id: str,
        ...
    ):
        """Generate comment with conversation history."""
        # Load relevant past comments
        past_comments = await self.long_term_memory.load_memory_variables({
            "question": journalist_question
        })

        # Add to state for context
        initial_state["past_comments"] = past_comments
        initial_state["session_id"] = session_id

        # Generate with memory
        result = await self.workflow.ainvoke(
            initial_state,
            config={"configurable": {"thread_id": session_id}}
        )

        # Save to memory
        await self.short_term_memory.save_context(
            {"question": journalist_question},
            {"comment": result["humanized_comment"]}
        )

        return result
```

### 7. Structured Logging (Medium Priority)

**Replace print statements with structured logging**:

```python
# New file: pr_agent/logging_config.py
import logging
import structlog
from typing import Any

def configure_logging(enable_json: bool = True, level: str = "INFO"):
    """Configure structured logging for PR agent."""
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if enable_json:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        level=level,
    )

# In agent.py
import structlog

logger = structlog.get_logger(__name__)

async def _load_profile_node(self, state: AgentState) -> AgentState:
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
            profile_fields=list(profile.keys())
        )
        return {**state, 'executive_profile': profile}
    except Exception as e:
        logger.error(
            "profile_load_failed",
            executive=state['executive_name'],
            error=str(e),
            exc_info=True
        )
        return {**state, 'errors': [*state['errors'], str(e)]}
```

### 8. Evaluation Framework (Medium Priority)

**Add automated evaluation**:

```python
# New file: pr_agent/evaluation.py
from langsmith.evaluation import evaluate, LangChainStringEvaluator
from langchain_anthropic import ChatAnthropic

class PRAgentEvaluator:
    """Evaluate PR comment quality."""

    def __init__(self):
        self.eval_llm = ChatAnthropic(model="claude-sonnet-4-5")

        # Custom evaluators
        self.evaluators = [
            # Tone consistency with profile
            LangChainStringEvaluator(
                "criteria",
                config={
                    "criteria": {
                        "tone_match": "Does the comment match the executive's tone and style?"
                    }
                },
                llm=self.eval_llm
            ),
            # Data incorporation
            LangChainStringEvaluator(
                "criteria",
                config={
                    "criteria": {
                        "data_usage": "Does the comment effectively use supporting data?"
                    }
                },
                llm=self.eval_llm
            ),
            # Authenticity
            LangChainStringEvaluator(
                "criteria",
                config={
                    "criteria": {
                        "authenticity": "Does the comment sound natural and human?"
                    }
                },
                llm=self.eval_llm
            )
        ]

    async def evaluate_comment(
        self,
        input_data: dict,
        output_comment: str,
        executive_profile: dict
    ) -> dict:
        """Evaluate a single PR comment."""
        results = await evaluate(
            lambda x: output_comment,
            data=[input_data],
            evaluators=self.evaluators
        )
        return results

# Usage in testing
async def test_comment_quality():
    evaluator = PRAgentEvaluator()
    agent = PRCommentAgent()

    result = await agent.generate_comment(...)

    eval_results = await evaluator.evaluate_comment(
        input_data={
            "article": article_text,
            "question": question
        },
        output_comment=result["humanized_comment"],
        executive_profile=result["executive_profile"]
    )

    print(f"Quality scores: {eval_results}")
```

### 9. Health Checks & Monitoring (High Priority for Production)

```python
# New file: pr_agent/health.py
from typing import Dict, Any
import asyncio

class HealthChecker:
    """Health checks for PR agent system."""

    def __init__(self, agent: PRCommentAgent):
        self.agent = agent

    async def check_llm_health(self) -> Dict[str, Any]:
        """Check if LLM is responding."""
        try:
            response = await self.agent.main_llm.ainvoke("test")
            return {"status": "healthy", "latency_ms": 0}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def check_search_health(self) -> Dict[str, Any]:
        """Check if search API is responding."""
        try:
            results = await self.agent.web_search.search_for_data("test")
            return {"status": "healthy" if results else "degraded"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def check_email_health(self) -> Dict[str, Any]:
        """Check if email service is configured."""
        if not self.agent.email_sender.email_from:
            return {"status": "not_configured"}
        return {"status": "healthy"}

    async def check_profiles_health(self) -> Dict[str, Any]:
        """Check if profile directory is accessible."""
        try:
            profiles = self.agent.profile_manager.list_profiles()
            return {
                "status": "healthy",
                "profile_count": len(profiles)
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def full_health_check(self) -> Dict[str, Any]:
        """Run all health checks."""
        checks = await asyncio.gather(
            self.check_llm_health(),
            self.check_search_health(),
            self.check_email_health(),
            self.check_profiles_health(),
            return_exceptions=True
        )

        return {
            "llm": checks[0],
            "search": checks[1],
            "email": checks[2],
            "profiles": checks[3],
            "overall": "healthy" if all(
                c.get("status") == "healthy" for c in checks
            ) else "degraded"
        }

# FastAPI endpoint
@app.get("/health")
async def health_check():
    """System health check endpoint."""
    health = HealthChecker(agent)
    return await health.full_health_check()
```

## Implementation Priority

### Phase 1 (Immediate - Production Readiness)
1. ✅ Security fixes (COMPLETED)
2. Async implementation
3. LangSmith observability
4. Structured logging
5. Health checks

### Phase 2 (Performance & UX)
6. Caching layer
7. Streaming support
8. Model optimization

### Phase 3 (Advanced Features)
9. Memory system
10. Evaluation framework
11. Advanced RAG patterns

## Migration Path

1. **Backward Compatibility**: Keep sync methods while adding async versions
2. **Gradual Rollout**: Implement features in separate branches
3. **Testing**: Add comprehensive tests for each new feature
4. **Documentation**: Update docs as features are added
5. **Monitoring**: Measure impact of each optimization

## Expected Benefits

- **Performance**: 2-3x faster with async + caching
- **Cost**: 50-70% reduction with caching and token limits
- **Reliability**: Better error handling and retries
- **Observability**: Full visibility into agent operations
- **User Experience**: Real-time streaming feedback
- **Quality**: Evaluation-driven improvements

## Next Steps

1. Review and prioritize improvements
2. Set up development environment with async support
3. Implement Phase 1 features
4. Add comprehensive tests
5. Deploy with monitoring
6. Measure and optimize based on metrics
