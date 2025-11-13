"""
Simple example of using the PR Comment Agent.

This script demonstrates a basic usage of the PR agent system.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from pr_agent import PRCommentAgent, PRAgentConfig
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def main():
    """Run a simple example of the PR agent."""

    # Sample article and question
    article = """
    Recent research shows that brands investing in long-term brand building
    see significantly better ROI compared to those focused solely on
    short-term performance metrics.
    """

    question = """
    How should CMOs balance short-term performance demands with
    long-term brand building?
    """

    # Initialize agent
    print("Initializing PR Agent...")
    config = PRAgentConfig(enable_verbose_logging=True)
    agent = PRCommentAgent(config)

    # Generate comment
    print("\nGenerating PR comment...")
    result = agent.generate_comment(
        article_text=article,
        journalist_question=question,
        media_outlet="Marketing Week",
        executive_name="Sarah Chen",
        journalist_name="Rachel Morrison"
    )

    # Display results
    print("\n" + "=" * 80)
    print("HUMANIZED COMMENT (READY FOR REVIEW)")
    print("=" * 80)
    print(result['humanized_comment'])
    print("\n" + "=" * 80)

    # Show workflow status
    print(f"\nWorkflow Status: {result['current_step']}")
    print(f"Email Sent: {result['email_sent']}")

    if result['errors']:
        print(f"\nErrors encountered:")
        for error in result['errors']:
            print(f"  - {error}")


if __name__ == "__main__":
    main()
