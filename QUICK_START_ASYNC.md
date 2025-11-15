# Quick Start: Async PR Agent

## Installation

```bash
pip install -r requirements.txt
```

## Environment Setup

Create `.env` file:

```env
# Required
OPENAI_API_KEY=your_key_here
SERPER_API_KEY=your_key_here

# Optional
LANGSMITH_API_KEY=your_key_here
EMAIL_FROM=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
PR_MANAGER_EMAIL=manager@company.com
```

## Basic Async Usage

```python
import asyncio
from pr_agent import PRCommentAgent

async def generate_comment():
    agent = PRCommentAgent()

    result = await agent.generate_comment_async(
        article_text="Your article text here...",
        journalist_question="The journalist's question?",
        media_outlet="TechCrunch",
        executive_name="Jane Smith"
    )

    print(f"Duration: {result['duration_seconds']}s")
    print(f"Comment: {result['humanized_comment']}")

    return result

# Run it
asyncio.run(generate_comment())
```

## With Configuration

```python
from pr_agent import PRCommentAgent
from pr_agent.config import PRAgentConfig

config = PRAgentConfig(
    model_name="gpt-4o",
    temperature=0.7,

    # Logging (console for dev, json for prod)
    log_level="INFO",
    log_format="console",

    # Tracing
    enable_tracing=True,
    langsmith_project="my-project",

    # Async settings
    max_concurrent_operations=5
)

agent = PRCommentAgent(config)
```

## Health Checks

```python
import asyncio
from pr_agent.health import HealthChecker
from pr_agent.config import PRAgentConfig

async def check_health():
    checker = HealthChecker(PRAgentConfig())
    health = await checker.check_all()

    print(f"Status: {health['status']}")

    for check in health['checks']:
        print(f"{check['component']}: {check['status']}")

asyncio.run(check_health())
```

## Batch Processing

```python
async def process_multiple():
    agent = PRCommentAgent()

    requests = [
        {"article_text": "...", "journalist_question": "...",
         "media_outlet": "TechCrunch", "executive_name": "Jane Smith"},
        {"article_text": "...", "journalist_question": "...",
         "media_outlet": "Forbes", "executive_name": "Jane Smith"},
    ]

    # Process concurrently
    tasks = [agent.generate_comment_async(**req) for req in requests]
    results = await asyncio.gather(*tasks)

    return results
```

## Performance Comparison

```python
import time
import asyncio

async def compare_performance():
    agent = PRCommentAgent()

    # Test async
    start = time.time()
    await agent.generate_comment_async(...)
    async_time = time.time() - start

    # Test sync
    start = time.time()
    agent.generate_comment(...)
    sync_time = time.time() - start

    print(f"Async: {async_time:.2f}s")
    print(f"Sync:  {sync_time:.2f}s")
    print(f"Speedup: {sync_time/async_time:.2f}x")
```

## Error Handling

```python
async def safe_generate():
    agent = PRCommentAgent()

    try:
        result = await agent.generate_comment_async(...)
        return result
    except ValueError as e:
        print(f"Invalid input: {e}")
    except Exception as e:
        print(f"Generation failed: {e}")
        # Check logs for details
```

## Logging Examples

### Console Logging (Development)
```python
config = PRAgentConfig(
    log_level="DEBUG",
    log_format="console"
)
```

Output:
```
2024-01-15 10:30:45 [info] async_workflow_started executive=Jane Doe
2024-01-15 10:30:46 [info] starting_parallel_research
2024-01-15 10:30:50 [info] parallel_research_complete success=True
```

### JSON Logging (Production)
```python
config = PRAgentConfig(
    log_level="INFO",
    log_format="json"
)
```

Output:
```json
{"event":"async_workflow_started","executive":"Jane Doe","timestamp":"2024-01-15T10:30:45Z","level":"INFO"}
{"event":"parallel_research_complete","success":true,"timestamp":"2024-01-15T10:30:50Z","level":"INFO"}
```

## Key Features

### 🚀 Parallel Operations
Media and data research run concurrently for 2-3x speedup.

### 📊 LangSmith Tracing
Full visibility into LLM calls, token usage, and performance.

### 📝 Structured Logging
Production-ready JSON logs with rich context.

### ✅ Health Checks
Monitor system health and component status.

### 🔄 Backward Compatible
Sync API still works - migrate at your own pace.

## Common Patterns

### Pattern 1: Simple Async
```python
result = await agent.generate_comment_async(...)
```

### Pattern 2: With Timeout
```python
result = await asyncio.wait_for(
    agent.generate_comment_async(...),
    timeout=60.0  # 60 seconds
)
```

### Pattern 3: With Retry
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential())
async def generate_with_retry():
    return await agent.generate_comment_async(...)
```

### Pattern 4: Concurrent Limit
```python
from asyncio import Semaphore

semaphore = Semaphore(3)  # Max 3 concurrent

async def limited_generate(req):
    async with semaphore:
        return await agent.generate_comment_async(**req)

tasks = [limited_generate(req) for req in requests]
results = await asyncio.gather(*tasks)
```

## Troubleshooting

### "Event loop is closed" Error
```python
# Solution: Use asyncio.run()
asyncio.run(generate_comment())

# Or in Jupyter notebooks
await generate_comment()  # Direct await works
```

### "No module named 'httpx'" Error
```bash
pip install httpx aiosmtplib
```

### Slow Performance
1. Check if running async version (`generate_comment_async()`)
2. Verify parallel execution in logs
3. Check network latency to APIs
4. Review LangSmith traces for bottlenecks

### Health Check Failures
```python
# Check specific component
result = await checker.check_component("llm")
print(f"LLM Status: {result.status}")
print(f"Details: {result.details}")
```

## Migration from Sync

### Before (Sync)
```python
agent = PRCommentAgent()
result = agent.generate_comment(
    article_text="...",
    journalist_question="...",
    media_outlet="TechCrunch",
    executive_name="Jane Smith"
)
```

### After (Async)
```python
import asyncio

async def main():
    agent = PRCommentAgent()
    result = await agent.generate_comment_async(
        article_text="...",
        journalist_question="...",
        media_outlet="TechCrunch",
        executive_name="Jane Smith"
    )
    return result

result = asyncio.run(main())
```

## Best Practices

1. **Use Async in Production** - 2-3x faster with parallel operations
2. **Enable Tracing** - Essential for debugging and monitoring
3. **Use JSON Logs** - Easier to parse and analyze
4. **Monitor Health** - Run periodic health checks
5. **Handle Errors** - Wrap in try/except with proper logging
6. **Set Timeouts** - Prevent hanging operations
7. **Limit Concurrency** - Use semaphores for rate limiting

## Resources

- **Full Examples**: `pr_agent/examples/async_example.py`
- **Configuration**: `pr_agent/config.py`
- **Health Checks**: `pr_agent/health.py`
- **Summary**: `PHASE1_IMPLEMENTATION_SUMMARY.md`

## Support

For issues or questions:
1. Check logs with `log_level="DEBUG"`
2. Review LangSmith traces
3. Run health checks
4. Check environment variables

---

**Quick Start Complete!** 🎉

You're now ready to use the async PR Agent with parallel operations, structured logging, and full observability.
