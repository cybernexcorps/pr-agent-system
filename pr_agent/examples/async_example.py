"""
Example demonstrating async PR Agent usage with parallel operations.

This example shows:
1. How to use the async API
2. Parallel processing for faster execution
3. Structured logging output
4. Health checks
5. Error handling
"""

import asyncio
import os
from dotenv import load_dotenv

from pr_agent.agent import PRCommentAgent
from pr_agent.config import PRAgentConfig
from pr_agent.health import HealthChecker

# Load environment variables
load_dotenv()


async def example_async_comment_generation():
    """Example of generating a comment using the async API."""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Async Comment Generation with Parallel Research")
    print("=" * 80 + "\n")

    # Configure the agent
    config = PRAgentConfig(
        # LLM settings
        model_name="gpt-4o",
        temperature=0.7,

        # Observability
        enable_tracing=True,
        langsmith_project="pr-agent-example",

        # Logging
        log_level="INFO",
        log_format="console",  # Use "json" for production

        # Async settings
        async_enabled=True,
        max_concurrent_operations=5
    )

    # Initialize agent
    agent = PRCommentAgent(config)

    # Example article and request
    article_text = """
    TechCrunch has learned that a major tech company is planning to launch
    a new AI product next quarter. The product aims to revolutionize how
    businesses interact with their customers through advanced natural language
    processing capabilities. Industry experts are skeptical about the timeline
    and technical feasibility.
    """

    journalist_question = """
    As a technology leader, what's your perspective on the recent AI product
    announcements? Do you think companies are overpromising on AI capabilities?
    """

    try:
        # Generate comment asynchronously (runs research in parallel)
        result = await agent.generate_comment_async(
            article_text=article_text,
            journalist_question=journalist_question,
            media_outlet="TechCrunch",
            executive_name="Jane Smith",  # Make sure this profile exists
            article_url="https://techcrunch.com/example-article",
            journalist_name="John Reporter",
            pr_manager_email=os.getenv("PR_MANAGER_EMAIL")
        )

        print("\n" + "-" * 80)
        print("RESULTS")
        print("-" * 80)
        print(f"\nExecutive: {result['executive_name']}")
        print(f"Media Outlet: {result['media_outlet']}")
        print(f"Duration: {result.get('duration_seconds', 'N/A')}s")
        print(f"Email Sent: {result['email_sent']}")

        print("\n--- Humanized Comment ---")
        print(result['humanized_comment'])

        print("\n--- Drafted Comment (for reference) ---")
        print(result['drafted_comment'])

        return result

    except Exception as e:
        print(f"\nError generating comment: {e}")
        raise


async def example_health_check():
    """Example of running health checks."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Health Check System")
    print("=" * 80 + "\n")

    config = PRAgentConfig()
    checker = HealthChecker(config)

    # Check all components
    health = await checker.check_all()

    print(f"Overall Status: {health['status'].upper()}")
    print(f"Total Duration: {health['duration_ms']}ms\n")

    print("Component Health:")
    print("-" * 80)
    for check in health['checks']:
        status_emoji = {
            'healthy': '✓',
            'degraded': '⚠',
            'unhealthy': '✗'
        }.get(check['status'], '?')

        print(f"{status_emoji} {check['component']:20} | "
              f"Status: {check['status']:10} | "
              f"Latency: {check['latency_ms']:6.1f}ms | "
              f"{check['message']}")

    return health


async def example_parallel_processing():
    """Example showing speed improvement from parallel processing."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Comparing Sync vs Async Performance")
    print("=" * 80 + "\n")

    config = PRAgentConfig(
        log_level="WARNING",  # Reduce noise for timing comparison
        log_format="console"
    )

    agent = PRCommentAgent(config)

    article_text = "Example article about AI trends in 2024."
    journalist_question = "What's your take on AI trends?"

    # Time async version
    print("Running ASYNC version (with parallel research)...")
    start = asyncio.get_event_loop().time()

    try:
        async_result = await agent.generate_comment_async(
            article_text=article_text,
            journalist_question=journalist_question,
            media_outlet="TechCrunch",
            executive_name="Jane Smith"
        )
        async_duration = asyncio.get_event_loop().time() - start
        print(f"✓ Async completed in {async_duration:.2f}s\n")
    except Exception as e:
        print(f"✗ Async failed: {e}\n")
        async_duration = None

    # Time sync version
    print("Running SYNC version (sequential research)...")
    start_sync = asyncio.get_event_loop().time()

    try:
        # Note: sync version needs to be run in executor to not block
        sync_result = await asyncio.to_thread(
            agent.generate_comment,
            article_text=article_text,
            journalist_question=journalist_question,
            media_outlet="TechCrunch",
            executive_name="Jane Smith"
        )
        sync_duration = asyncio.get_event_loop().time() - start_sync
        print(f"✓ Sync completed in {sync_duration:.2f}s\n")
    except Exception as e:
        print(f"✗ Sync failed: {e}\n")
        sync_duration = None

    # Compare
    if async_duration and sync_duration:
        speedup = sync_duration / async_duration
        print("-" * 80)
        print(f"Performance Comparison:")
        print(f"  Async: {async_duration:.2f}s")
        print(f"  Sync:  {sync_duration:.2f}s")
        print(f"  Speedup: {speedup:.2f}x faster with async")
        print("-" * 80)


async def example_batch_processing():
    """Example of processing multiple comments concurrently."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Batch Processing Multiple Comments")
    print("=" * 80 + "\n")

    config = PRAgentConfig(
        log_level="INFO",
        log_format="console",
        max_concurrent_operations=3  # Limit concurrent operations
    )

    agent = PRCommentAgent(config)

    # Multiple comment requests
    requests = [
        {
            "article_text": "Article about AI in healthcare...",
            "journalist_question": "How will AI transform healthcare?",
            "media_outlet": "Healthcare Today",
            "executive_name": "Jane Smith"
        },
        {
            "article_text": "Article about AI in finance...",
            "journalist_question": "What are the risks of AI in finance?",
            "media_outlet": "Financial Times",
            "executive_name": "Jane Smith"
        },
        {
            "article_text": "Article about AI ethics...",
            "journalist_question": "How do we ensure responsible AI?",
            "media_outlet": "Tech Ethics Magazine",
            "executive_name": "Jane Smith"
        }
    ]

    print(f"Processing {len(requests)} comment requests concurrently...\n")

    start = asyncio.get_event_loop().time()

    # Create tasks
    tasks = [
        agent.generate_comment_async(**request)
        for request in requests
    ]

    # Process with concurrency limit
    results = await asyncio.gather(*tasks, return_exceptions=True)

    duration = asyncio.get_event_loop().time() - start

    # Report results
    print("\n" + "-" * 80)
    print("BATCH RESULTS")
    print("-" * 80)

    success_count = 0
    for i, result in enumerate(results, 1):
        if isinstance(result, Exception):
            print(f"{i}. ✗ Failed: {result}")
        else:
            print(f"{i}. ✓ Success: {result['media_outlet']} - "
                  f"{len(result['humanized_comment'])} chars")
            success_count += 1

    print(f"\nTotal Duration: {duration:.2f}s")
    print(f"Success Rate: {success_count}/{len(requests)}")
    print(f"Average: {duration/len(requests):.2f}s per comment")


async def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("PR AGENT ASYNC EXAMPLES")
    print("=" * 80)

    try:
        # Example 1: Basic async usage
        await example_async_comment_generation()

        # Example 2: Health checks
        await example_health_check()

        # Example 3: Performance comparison
        # Uncomment to run (requires valid API keys and profile)
        # await example_parallel_processing()

        # Example 4: Batch processing
        # Uncomment to run (requires valid API keys and profile)
        # await example_batch_processing()

        print("\n" + "=" * 80)
        print("ALL EXAMPLES COMPLETED")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\n\nExample failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the async examples
    asyncio.run(main())
