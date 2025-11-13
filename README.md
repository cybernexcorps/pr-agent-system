# PR Agent System

> AI-powered comment generation system for branding agency executives using LangChain and LangGraph

## Quick Start

\\\ash
pip install -r requirements.txt
cp pr_agent/.env.example pr_agent/.env
# Edit .env with your API keys
\\\

## Usage

\\\python
from pr_agent import PRCommentAgent

agent = PRCommentAgent()
result = agent.generate_comment(
    article_text="Article content...",
    journalist_question="Your perspective?",
    media_outlet="Marketing Week",
    executive_name="Sarah Chen"
)
print(result['humanized_comment'])
\\\

See [pr_agent/README.md](pr_agent/README.md) for full documentation.
