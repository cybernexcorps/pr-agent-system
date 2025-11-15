# PR Agent System

**AI-powered comment generation system for branding agency executives built with LangChain and LangGraph.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![LangChain](https://img.shields.io/badge/LangChain-ready-green.svg)](https://langchain.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Overview

The PR Agent System automates the research and drafting that branding-agency executives typically perform when responding to media requests. Multiple agents collaborate to keep every response well-researched, on-brand, and human sounding.

### Why It Matters

- Respond to journalist questions quickly without sacrificing diligence
- Maintain a consistent executive voice across outlets and channels
- Reference credible research and statistics in every comment
- Tailor answers to specific journalists and publications
- Deliver polished copy that still feels authentic

---

## How It Works

```mermaid
graph TD
    A[Article + Question] --> B[Media Research Agent]
    B --> C[Executive Profile Loader]
    C --> D[Data Research Agent]
    D --> E[Comment Drafter Agent]
    E --> F[Humanizer Agent]
    F --> G[Email to PR Manager]

    style A fill:#e1f5ff,color:#000
    style B fill:#f5f5f5,color:#000
    style C fill:#f5f5f5,color:#000
    style D fill:#f5f5f5,color:#000
    style E fill:#fff3cd,color:#000
    style F fill:#fde2e4,color:#000
    style G fill:#d4edda,color:#000
```

**Workflow**

1. **Input processing** - capture the article, journalist question, executive, and outlet.
2. **Media research** - gather outlet history, journalist focus areas, and tone.
3. **Executive profile loading** - inject preferred style, voice, and redlines.
4. **Data research** - pull fresh statistics and supporting citations from the web.
5. **Comment drafting** - produce a structured response that references the research.
6. **Humanization** - polish for natural flow, varied sentence length, and brand voice.
7. **Email notification** - send the final copy to a PR manager for approval.

**Highlights**

- LangChain + LangGraph agent orchestration
- Automated media and data research
- Executive profile management
- Human-in-the-loop friendly workflow (email approvals)
- CLI entry points plus Python API
- Graceful error handling and configurable logging

---

## Quick Start

### Prerequisites

- Python 3.8 or later
- API keys:
  - LLM provider: OpenAI or Anthropic
  - Web search: Serper or Tavily
  - Email: SMTP credentials (for example a Gmail app password)

### Installation

```bash
git clone https://github.com/cybernexcorps/pr-agent-system.git
cd pr-agent-system
pip install -r requirements.txt
cp pr_agent/.env.example pr_agent/.env
# edit pr_agent/.env with your API keys
```

### Basic Usage

```python
from pr_agent import PRCommentAgent

agent = PRCommentAgent()

result = agent.generate_comment(
    article_text="Recent research shows brands investing in long-term brand building see 3x better ROI...",
    journalist_question="What advice would you give to CMOs balancing short-term performance with brand building?",
    media_outlet="Marketing Week",
    executive_name="Sarah Chen",
    journalist_name="Rachel Morrison"
)

print(result["humanized_comment"])
```

**Example output**

> This research validates what we've seen with our clients for years. The key isn't choosing between short-term performance and long-term brand building - it is integrating them carefully. We recommend a dual-measurement framework: track immediate conversions alongside brand equity metrics like aided awareness and consideration. The 60/40 split is a good starting point, but the optimal ratio depends on category maturity and competitive position. During economic uncertainty, brands with strong equity have more flexibility to optimize their performance spend because they've built pricing power and loyalty. It is not either/or - it is both/and, measured rigorously.

---

## Configuration

### Environment Variables (`pr_agent/.env`)

```ini
# LLM API Keys (at least one)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Search API Keys (at least one)
SERPER_API_KEY=...
TAVILY_API_KEY=...

# Email configuration (required)
EMAIL_FROM=pr@agency.com
EMAIL_PASSWORD=your_app_password
PR_MANAGER_EMAIL=manager@agency.com

# Optional SMTP overrides
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

### Configuration Object

```python
from pr_agent import PRCommentAgent, PRAgentConfig

config = PRAgentConfig(
    model_name="gpt-4o",
    temperature=0.7,
    humanizer_temperature=0.9,
    max_search_results=5,
    enable_verbose_logging=True
)

agent = PRCommentAgent(config)
```

---

## Phase 3: Advanced Features (NEW)

The PR Agent now includes optional advanced features for enterprise deployments:

### Memory System
- **Short-term memory**: Maintains conversation context within sessions
- **Long-term memory**: Vector-based semantic search across past comments
- **Session tracking**: Persistent conversation history
- **Smart retrieval**: Find similar past responses automatically

### Evaluation Framework
- **Automated quality assessment**: Score comments on 4 criteria
  - Tone consistency with executive profile
  - Effective use of supporting data
  - Natural, authentic language
  - Relevance to journalist question
- **Batch evaluation**: Test multiple responses
- **Quality gates**: Only save high-scoring comments to memory

### RAG (Retrieval-Augmented Generation)
- **Comment history**: Retrieve similar past responses
- **Media knowledge**: Store outlet and journalist information
- **Few-shot examples**: High-quality examples for context
- **Context augmentation**: Enhance responses with relevant knowledge

### Usage with Phase 3 Features

```python
from pr_agent import PRCommentAgent, PRAgentConfig

# Enable Phase 3 features
config = PRAgentConfig()
config.enable_memory = True
config.enable_evaluation = True
config.enable_rag = True

agent = PRCommentAgent(config)

# Generate comment with memory, RAG, and evaluation
result = await agent.generate_comment_with_memory_and_evaluation(
    article_text="...",
    journalist_question="...",
    media_outlet="TechCrunch",
    executive_name="Sarah Chen",
    session_id="session_123"
)

# Access Phase 3 data
print(f"Quality Score: {result['evaluation_scores']['overall_score']:.2f}")
print(f"Past Comments Retrieved: {len(result['past_comments'])}")
print(f"Session ID: {result['session_id']}")
```

**Requirements for Phase 3:**
```env
VOYAGE_API_KEY=your_voyage_key  # Required for memory & RAG
ENABLE_MEMORY=true
ENABLE_EVALUATION=true
ENABLE_RAG=true
```

See `examples/phase3_demo.py` for complete demonstrations and `PHASE3_IMPLEMENTATION_SUMMARY.md` for detailed documentation.

---

## Executive Profiles

Executive profiles live in `pr_agent/config/executive_profiles/` as JSON files and define tone, favorite topics, and off-limit phrases.

```json
{
  "name": "Sarah Chen",
  "title": "Chief Brand Officer",
  "company": "BrandForward Agency",
  "expertise": ["Brand strategy", "Marketing ROI", "Consumer insights"],
  "communication_style": "Professional yet approachable, data-driven",
  "tone": "Confident, insightful, forward-thinking",
  "talking_points": [
    "Importance of long-term brand building",
    "Data-driven decision making"
  ],
  "values": ["Authenticity", "Innovation", "Strategic thinking"],
  "speaking_patterns": "Uses concrete examples, references data",
  "do_not_say": ["Empty buzzwords", "Unsubstantiated claims"]
}
```

```python
from pr_agent.profile_manager import ExecutiveProfileManager

manager = ExecutiveProfileManager()
print(manager.list_profiles())

profile = manager.load_profile("Sarah Chen")
new_profile = manager.create_sample_profile("John Doe")
manager.save_profile("John Doe", new_profile)
```

---

## Advanced Usage

```python
result = agent.generate_comment(
    article_text="Long article content...",
    journalist_question="What's your take on this?",
    media_outlet="Forbes",
    executive_name="Sarah Chen",
    article_url="https://example.com/article",
    journalist_name="Jane Smith",
    pr_manager_email="manager@agency.com"
)

print(result["media_research"])
print(result["supporting_data"])
print(result["drafted_comment"])
print(result["humanized_comment"])
print(result["email_sent"])
```

---

## Command-Line Interface

```bash
# List available executive profiles
pr-agent list-profiles

# Interactive generation
pr-agent generate --executive "Sarah Chen" --outlet "TechCrunch" --interactive

# Fully scripted invocation
pr-agent generate \
  --executive "Sarah Chen" \
  --outlet "TechCrunch" \
  --article article.txt \
  --question "Your perspective?" \
  --output comment.txt

# Verify SMTP credentials
pr-agent test-email --to you@example.com
```

---

## Architecture

### Technology Stack

- LangChain for agent building blocks and LLM integration
- LangGraph for workflow orchestration with state management
- OpenAI or Anthropic for generation and rewriting
- Serper or Tavily for web research
- SMTP email (Gmail or custom server) for notifications

### Component Overview

- **PRCommentAgent** - overall LangGraph orchestrator
- **MediaResearcherAgent** - analyzes outlet trends (uses search APIs)
- **DataResearcherAgent** - finds supporting data and links
- **CommentDrafterAgent** - generates the first-pass comment via LLM
- **HumanizerAgent** - rewrites for tone and authenticity
- **EmailSender** - composes the final email to the PR manager

### Project Structure

```
pr-agent-system/
|-- pr_agent/
|   |-- __init__.py
|   |-- agent.py
|   |-- cli.py
|   |-- config.py
|   |-- state.py
|   |-- profile_manager.py
|   |-- agents/
|   |   |-- media_researcher.py
|   |   |-- data_researcher.py
|   |   |-- comment_drafter.py
|   |   `-- humanizer.py
|   |-- tools/
|   |   |-- search.py
|   |   |-- data_extractor.py
|   |   `-- email_sender.py
|   |-- prompts/
|   |   `-- templates.py
|   `-- config/
|       `-- executive_profiles/
|           `-- sarah_chen.json
|-- pr_agent/examples/
|   |-- pr_agent_demo.ipynb
|   `-- simple_example.py
|-- README.md
|-- CLAUDE.md
|-- LICENSE
|-- setup.py
|-- requirements.txt
`-- .gitignore
```

---

## Examples

1. **Simple script**

   ```python
   from pr_agent import PRCommentAgent

   agent = PRCommentAgent()
   result = agent.generate_comment(
       article_text="Article about marketing trends...",
       journalist_question="How should brands adapt?",
       media_outlet="AdWeek",
       executive_name="Sarah Chen"
   )

   print(result["humanized_comment"])
   ```

2. **Interactive notebook**

   ```bash
   jupyter lab pr_agent/examples/pr_agent_demo.ipynb
   ```

3. **Batch processing**

   ```python
   import csv
   from pr_agent import PRCommentAgent

   agent = PRCommentAgent()

   requests = [
       {
           "article": "Article 1...",
           "question": "Question 1?",
           "outlet": "Forbes",
           "executive": "Sarah Chen"
       },
       # ... add more
   ]

   results = []
   for req in requests:
       result = agent.generate_comment(
           article_text=req["article"],
           journalist_question=req["question"],
           media_outlet=req["outlet"],
           executive_name=req["executive"]
       )
       results.append({
           "outlet": req["outlet"],
           "comment": result["humanized_comment"],
           "email_sent": result["email_sent"]
       })

   with open("comments.csv", "w", newline="") as f:
       writer = csv.DictWriter(f, fieldnames=["outlet", "comment", "email_sent"])
       writer.writeheader()
       writer.writerows(results)
   ```

---

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `"No valid API key configured"` | Ensure `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` is present in `.env`. |
| `"Profile not found"` | Confirm the JSON file exists in `pr_agent/config/executive_profiles/` and that the filename matches the requested executive (lowercase with underscores). |
| `"Email sending failed"` | Double-check `EMAIL_FROM`, `EMAIL_PASSWORD`, and SMTP settings. Gmail users must use an App Password. |
| `"Search errors"` | Validate `SERPER_API_KEY` or `TAVILY_API_KEY`, confirm rate limits, and make sure networking is enabled. |
| `"Repository not authorized"` (development) | Push from an authenticated environment instead of a restricted sandbox. |

---

## Performance Benchmarks

- 30-60 seconds per comment end-to-end (varies with research depth)
- Approximately $0.10-$0.30 in API costs per comment
- Designed for concurrent requests via background tasks
- Comments usually need at most 5-10% manual edits

---

## Roadmap

- Multilingual comment generation (Spanish, French, German, Japanese)
- CRM integrations (Salesforce, HubSpot)
- Comment performance tracking dashboards
- Team workflows with role-based approvals
- Mobile-friendly approval experience
- Optional posting to Twitter and LinkedIn
- Comment variation generation and A/B testing
- Prompt tuning and optimization tools
- Template library for common journalist scenarios
- Executive reporting with ROI metrics

---

## Contributing

We welcome pull requests and issues. See `CONTRIBUTING.md` for style guides and branching strategy.

**Ideas worth exploring**

- Support for additional LLM providers (Gemini, Cohere, etc.)
- Richer entity extraction and fact grounding
- Integrations with PR management platforms
- Expanded multilingual tone customization

---

## Testing

```bash
# Full suite (when tests are implemented)
pytest tests/

# With coverage
pytest --cov=pr_agent --cov-report=html

# Component smoke tests
python -m pr_agent.agents.media_researcher
python -m pr_agent.tools.email_sender
```

---

## License

MIT License - see `LICENSE` for full text.  
Copyright (c) 2025 CyberNexCorps.

---

## Acknowledgments

- LangChain community for the agent tooling foundation
- Anthropic for Claude AI capabilities
- OpenAI for GPT models
- PyMC community for inspiration on marketing analytics approaches

---

## Support and Contact

- Report issues or request features through GitHub Issues
- Discuss implementation details in GitHub Discussions
- Follow CyberNexCorps on Twitter (`@cybernexcorps`) and LinkedIn for announcements

---

## Related Projects

- Marketing Mix Modeling Framework - measure long-term ad effectiveness
- LangChain - framework for LLM application development
- LangGraph - build stateful multi-actor applications

Star this repository if you find it useful!
