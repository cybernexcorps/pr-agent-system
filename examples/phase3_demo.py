"""
Phase 3 Feature Demonstration

Demonstrates advanced features:
- Memory system (short-term and long-term)
- Evaluation framework
- RAG (Retrieval-Augmented Generation)

This script shows how to use the PR Agent with all Phase 3 features enabled.
"""

import asyncio
import os
from dotenv import load_dotenv
from pr_agent import PRCommentAgent, PRAgentConfig

# Load environment variables
load_dotenv()


async def demo_basic_phase3():
    """Demo 1: Basic usage with Phase 3 features enabled."""
    print("=" * 80)
    print("DEMO 1: Basic Phase 3 Features")
    print("=" * 80)

    # Configure with Phase 3 features enabled
    config = PRAgentConfig()
    config.enable_memory = True
    config.enable_evaluation = True
    config.enable_rag = True
    config.enable_verbose_logging = True

    print(f"\nPhase 3 Configuration:")
    print(f"  - Memory: {config.enable_memory}")
    print(f"  - Evaluation: {config.enable_evaluation}")
    print(f"  - RAG: {config.enable_rag}")

    try:
        agent = PRCommentAgent(config)
        print("\n✓ PR Agent initialized with Phase 3 features")

        # Check which features are actually enabled
        memory_enabled = agent.memory.enabled if agent.memory else False
        eval_enabled = agent.evaluator.enabled if agent.evaluator else False
        rag_enabled = agent.rag.enabled if agent.rag else False

        print(f"\nActual Feature Status:")
        print(f"  - Memory System: {'✓ Enabled' if memory_enabled else '✗ Disabled (check VOYAGE_API_KEY)'}")
        print(f"  - Evaluation: {'✓ Enabled' if eval_enabled else '✗ Disabled'}")
        print(f"  - RAG System: {'✓ Enabled' if rag_enabled else '✗ Disabled (check VOYAGE_API_KEY)'}")

        # Get Phase 3 stats
        stats = agent.get_phase3_stats()
        print(f"\nPhase 3 Statistics:")
        print(f"  Memory: {stats.get('memory', 'N/A')}")
        print(f"  RAG: {stats.get('rag', 'N/A')}")
        print(f"  Evaluator: {stats.get('evaluator', 'N/A')}")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nNote: Ensure VOYAGE_API_KEY is set for memory and RAG features")

    print("\n")


async def demo_memory_system():
    """Demo 2: Memory system with conversation tracking."""
    print("=" * 80)
    print("DEMO 2: Memory System - Conversation Tracking")
    print("=" * 80)

    config = PRAgentConfig()
    config.enable_memory = True
    config.enable_evaluation = False  # Disable for speed
    config.enable_rag = False

    try:
        agent = PRCommentAgent(config)

        if not (agent.memory and agent.memory.enabled):
            print("\n✗ Memory system not enabled. Set VOYAGE_API_KEY to enable.")
            return

        print("\n✓ Memory system enabled")

        session_id = "demo_session_001"

        # Simulate multiple interactions in the same session
        print(f"\nSession ID: {session_id}")

        questions = [
            "What's your view on remote work?",
            "How do you handle work-life balance?",
            "What about team collaboration remotely?"
        ]

        for i, question in enumerate(questions, 1):
            print(f"\n--- Interaction {i} ---")
            print(f"Question: {question}")

            result = await agent.generate_comment_with_memory_and_evaluation(
                article_text=f"Article about workplace trends discussing {question.lower()}",
                journalist_question=question,
                media_outlet="Forbes",
                executive_name="Sarah Chen",
                session_id=session_id,
                enable_evaluation=False
            )

            print(f"Comment: {result['humanized_comment'][:100]}...")

            # Show conversation history
            if i > 1:
                history = result.get('conversation_history', [])
                print(f"Conversation history length: {len(history)} messages")

        # Get memory stats
        memory_stats = agent.memory.get_memory_stats()
        print(f"\nMemory Statistics:")
        print(f"  Active sessions: {memory_stats.get('active_sessions', 0)}")
        print(f"  Long-term documents: {memory_stats.get('long_term_documents', 0)}")

    except Exception as e:
        print(f"\n✗ Error: {e}")

    print("\n")


async def demo_evaluation_framework():
    """Demo 3: Automated quality evaluation."""
    print("=" * 80)
    print("DEMO 3: Evaluation Framework - Quality Assessment")
    print("=" * 80)

    config = PRAgentConfig()
    config.enable_memory = False
    config.enable_evaluation = True
    config.enable_rag = False

    try:
        agent = PRCommentAgent(config)

        if not (agent.evaluator and agent.evaluator.enabled):
            print("\n✗ Evaluation system not enabled.")
            return

        print("\n✓ Evaluation system enabled")
        print(f"Evaluation model: {config.evaluation_model}")

        result = await agent.generate_comment_with_memory_and_evaluation(
            article_text="Article discussing the future of artificial intelligence in business.",
            journalist_question="What's your perspective on AI adoption in enterprise?",
            media_outlet="TechCrunch",
            executive_name="Sarah Chen",
            enable_evaluation=True
        )

        # Display evaluation results
        eval_scores = result.get('evaluation_scores', {})

        if eval_scores.get('enabled'):
            print(f"\n✓ Comment Evaluation Results:")
            print(f"  Overall Score: {eval_scores.get('overall_score', 0):.2f}/1.00")
            print(f"  Status: {'✓ PASSED' if eval_scores.get('overall_passed') else '✗ FAILED'}")

            print(f"\n  Criteria Breakdown:")
            for criterion, data in eval_scores.get('criteria_scores', {}).items():
                status = "✓" if data.get('passed') else "✗"
                score = data.get('score', 0)
                print(f"    {status} {criterion.replace('_', ' ').title()}: {score:.2f}")

            # Show evaluation summary
            summary = agent.evaluator.get_evaluation_summary(eval_scores)
            print(f"\n{summary}")

        else:
            print(f"\n✗ Evaluation not performed: {eval_scores.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"\n✗ Error: {e}")

    print("\n")


async def demo_rag_system():
    """Demo 4: RAG system for context augmentation."""
    print("=" * 80)
    print("DEMO 4: RAG System - Context Augmentation")
    print("=" * 80)

    config = PRAgentConfig()
    config.enable_memory = False
    config.enable_evaluation = False
    config.enable_rag = True

    try:
        agent = PRCommentAgent(config)

        if not (agent.rag and agent.rag.enabled):
            print("\n✗ RAG system not enabled. Set VOYAGE_API_KEY to enable.")
            return

        print("\n✓ RAG system enabled")

        # First, store some example comments
        print("\nStoring example comments in RAG...")

        await agent.rag.store_comment(
            executive_name="Sarah Chen",
            media_outlet="TechCrunch",
            journalist_question="What's driving innovation in your industry?",
            comment="Innovation is driven by customer needs and emerging technologies.",
            metadata={"quality": "high", "category": "innovation"}
        )

        await agent.rag.store_comment(
            executive_name="Sarah Chen",
            media_outlet="Forbes",
            journalist_question="How do you approach digital transformation?",
            comment="Digital transformation requires a people-first approach.",
            metadata={"quality": "high", "category": "transformation"}
        )

        print("✓ Stored 2 example comments")

        # Store media knowledge
        await agent.rag.store_media_knowledge(
            media_outlet="TechCrunch",
            journalist_name=None,
            knowledge="TechCrunch focuses on technology startups, innovation, and venture capital."
        )

        print("✓ Stored media knowledge")

        # Store examples for few-shot learning
        await agent.rag.store_example(
            example_text="Example: AI is transforming how we work, enabling productivity gains of 30-40%.",
            category="ai_technology",
            metadata={"quality": "high"}
        )

        print("✓ Stored example for few-shot learning")

        # Now generate a comment with RAG augmentation
        print("\nGenerating comment with RAG augmentation...")

        result = await agent.generate_comment_with_memory_and_evaluation(
            article_text="Article about AI transformation in enterprise software.",
            journalist_question="How is AI changing your business?",
            media_outlet="TechCrunch",
            executive_name="Sarah Chen",
            enable_evaluation=False
        )

        # Show RAG context
        rag_context = result.get('rag_context', {})

        if rag_context.get('enabled'):
            counts = rag_context.get('retrieval_counts', {})
            print(f"\n✓ RAG Context Retrieved:")
            print(f"  Similar comments: {counts.get('similar_comments', 0)}")
            print(f"  Media knowledge: {counts.get('media_knowledge', 0)}")
            print(f"  Examples: {counts.get('examples', 0)}")

        # Get RAG stats
        rag_stats = agent.rag.get_rag_stats()
        print(f"\nRAG Statistics:")
        print(f"  Total documents: {rag_stats.get('total_documents', 0)}")
        print(f"  Vector stores: {rag_stats.get('vector_stores', {})}")

    except Exception as e:
        print(f"\n✗ Error: {e}")

    print("\n")


async def demo_full_phase3_workflow():
    """Demo 5: Complete workflow with all Phase 3 features."""
    print("=" * 80)
    print("DEMO 5: Complete Phase 3 Workflow")
    print("=" * 80)
    print("Combining Memory + Evaluation + RAG")
    print("=" * 80)

    config = PRAgentConfig()
    config.enable_memory = True
    config.enable_evaluation = True
    config.enable_rag = True
    config.enable_verbose_logging = True

    try:
        agent = PRCommentAgent(config)

        # Check which features are enabled
        memory_enabled = agent.memory.enabled if agent.memory else False
        eval_enabled = agent.evaluator.enabled if agent.evaluator else False
        rag_enabled = agent.rag.enabled if agent.rag else False

        print(f"\nPhase 3 Features Status:")
        print(f"  Memory: {'✓' if memory_enabled else '✗'}")
        print(f"  Evaluation: {'✓' if eval_enabled else '✗'}")
        print(f"  RAG: {'✓' if rag_enabled else '✗'}")

        if not all([memory_enabled, eval_enabled, rag_enabled]):
            print("\n⚠ Warning: Not all Phase 3 features are enabled")
            print("Set VOYAGE_API_KEY for memory and RAG features")

        print("\nGenerating PR comment with full Phase 3 pipeline...")

        result = await agent.generate_comment_with_memory_and_evaluation(
            article_text="""
            Article: The Future of AI in Enterprise

            As artificial intelligence continues to evolve, businesses are finding new ways
            to leverage AI for productivity, innovation, and competitive advantage. Industry
            leaders are investing heavily in AI infrastructure and talent.
            """,
            journalist_question="How is your company approaching AI adoption?",
            media_outlet="TechCrunch",
            executive_name="Sarah Chen",
            session_id="full_demo_session",
            journalist_name="Alex Thompson",
            enable_evaluation=True
        )

        print(f"\n✓ Comment generated successfully!")
        print(f"\nGenerated Comment:")
        print(f"{result['humanized_comment']}")

        print(f"\nWorkflow Details:")
        print(f"  Duration: {result.get('duration_seconds', 0):.2f} seconds")
        print(f"  Session ID: {result.get('session_id')}")

        # Memory info
        past_comments = result.get('past_comments', [])
        print(f"\n  Memory:")
        print(f"    - Past comments retrieved: {len(past_comments)}")

        # RAG info
        rag_context = result.get('rag_context', {})
        if rag_context.get('enabled'):
            counts = rag_context.get('retrieval_counts', {})
            print(f"\n  RAG:")
            print(f"    - Similar comments: {counts.get('similar_comments', 0)}")
            print(f"    - Media knowledge: {counts.get('media_knowledge', 0)}")
            print(f"    - Examples: {counts.get('examples', 0)}")

        # Evaluation info
        eval_scores = result.get('evaluation_scores', {})
        if eval_scores.get('enabled'):
            print(f"\n  Evaluation:")
            print(f"    - Overall score: {eval_scores.get('overall_score', 0):.2f}")
            print(f"    - Status: {'PASSED' if eval_scores.get('overall_passed') else 'FAILED'}")

        print(f"\nPhase 3 Features Used:")
        phase3_enabled = result.get('phase3_enabled', {})
        for feature, enabled in phase3_enabled.items():
            status = '✓' if enabled else '✗'
            print(f"  {status} {feature.upper()}")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

    print("\n")


async def main():
    """Run all Phase 3 demos."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "PR Agent - Phase 3 Demonstration" + " " * 26 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\nAdvanced Features: Memory, Evaluation, and RAG")
    print("\n")

    # Check for required API keys
    print("Checking environment variables...")
    required_keys = {
        "ANTHROPIC_API_KEY": "LLM provider",
        "VOYAGE_API_KEY": "Memory & RAG (optional but recommended)",
        "SERPER_API_KEY": "Web search",
    }

    missing_keys = []
    for key, description in required_keys.items():
        if os.getenv(key):
            print(f"  ✓ {key} - {description}")
        else:
            print(f"  ✗ {key} - {description} (not set)")
            if key != "VOYAGE_API_KEY":
                missing_keys.append(key)

    if missing_keys:
        print(f"\n⚠ Warning: Missing required keys: {', '.join(missing_keys)}")
        print("Some features may not work without these keys.")
        return

    print("\n")

    # Run demos
    demos = [
        ("Basic Phase 3 Features", demo_basic_phase3),
        ("Memory System", demo_memory_system),
        ("Evaluation Framework", demo_evaluation_framework),
        ("RAG System", demo_rag_system),
        ("Complete Phase 3 Workflow", demo_full_phase3_workflow),
    ]

    for i, (name, demo_func) in enumerate(demos, 1):
        try:
            await demo_func()
        except Exception as e:
            print(f"\n✗ Demo {i} failed: {e}")
            import traceback
            traceback.print_exc()

        if i < len(demos):
            print("\n" + "-" * 80 + "\n")

    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 28 + "Demos Complete!" + " " * 34 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
