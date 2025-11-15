# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PR Agent System is an AI-powered comment generation system for branding agency executives using LangChain and LangGraph. It automates the process of generating professional PR comments for media inquiries through a multi-step workflow.

## Essential Commands

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Create environment file from template
cp pr_agent/.env.example pr_agent/.env
# Then edit .env with your API keys
```

### Running Examples
```bash
# Run simple example
python pr_agent/examples/simple_example.py

# Run Jupyter notebook demo
jupyter notebook pr_agent/examples/pr_agent_demo.ipynb
```

### Development
```bash
# Install in development mode
pip install -e .
```

## Architecture

### LangGraph Workflow Pipeline

The system uses LangGraph to orchestrate a linear multi-step pipeline:

```
load_profile → research_media → research_data → draft_comment → humanize_comment → send_email
```

Each node in the workflow:
1. **load_profile**: Loads executive profile from JSON (ExecutiveProfileManager)
2. **research_media**: Researches media outlet and journalist (MediaResearcherAgent)
3. **research_data**: Finds supporting statistics and insights (DataResearcherAgent)
4. **draft_comment**: Generates initial professional comment (CommentDrafterAgent)
5. **humanize_comment**: Refines comment to sound natural (HumanizerAgent)
6. **send_email**: Sends to PR manager for approval (EmailSender)

### State Management

The workflow uses `AgentState` (TypedDict) that flows through all nodes, accumulating data at each step. Key state fields:
- Input: `article_text`, `journalist_question`, `media_outlet`, `executive_name`
- Research outputs: `media_research`, `supporting_data`, `executive_profile`
- Generated content: `drafted_comment`, `humanized_comment`
- Metadata: `timestamp`, `approval_status`, `email_sent`, `current_step`, `errors`

### Core Components

**Agent Orchestrator** (`agent.py`):
- `PRCommentAgent` class manages entire workflow
- Initializes LLMs, tools, specialized agents, and profile manager
- Builds LangGraph workflow with node functions
- Main entry point: `generate_comment()` method

**Specialized Agents** (`agents/`):
- `MediaResearcherAgent`: Analyzes media outlets and journalists
- `DataResearcherAgent`: Searches web for supporting data
- `CommentDrafterAgent`: Generates initial comment draft
- `HumanizerAgent`: Makes text sound natural and authentic

**Tools** (`tools/`):
- `WebSearchTool`: Web search via Serper or Tavily APIs
- `MediaResearchTool`: Media-specific research
- `EmailSender`: SMTP email notifications to PR manager

**Configuration** (`config.py`):
- `PRAgentConfig` dataclass manages all settings
- Auto-loads from environment variables
- Validates required API keys on initialization

**Profile Management** (`profile_manager.py`):
- `ExecutiveProfileManager` loads/saves executive profiles
- Profiles stored as JSON in `pr_agent/config/executive_profiles/`
- Caches profiles in memory for performance
- Normalizes executive names (lowercase, underscores) for file lookups

### Executive Profile Structure

Profiles define communication style, expertise, and personality:
```json
{
  "name": "Executive Name",
  "title": "Chief Brand Officer",
  "company": "Agency Name",
  "expertise": ["Area 1", "Area 2"],
  "communication_style": "Description",
  "tone": "Tone characteristics",
  "personality_traits": ["Trait 1", "Trait 2"],
  "talking_points": ["Key message 1", "Key message 2"],
  "values": ["Value 1", "Value 2"],
  "speaking_patterns": "Description",
  "do_not_say": ["Things to avoid"],
  "preferred_structure": "Response structure"
}
```

Required fields: `name`, `title`, `communication_style`, `expertise`

Profile filenames must be lowercase with underscores (e.g., `sarah_chen.json`).

## Configuration Requirements

### Required API Keys

At least one LLM provider:
- `OPENAI_API_KEY` (for GPT-4o model)
- `ANTHROPIC_API_KEY` (for Claude 3.5 Sonnet)

At least one search provider:
- `SERPER_API_KEY` (Google Search via Serper)
- `TAVILY_API_KEY` (Tavily search)

Email configuration (all required):
- `EMAIL_FROM`: Sender email address
- `EMAIL_PASSWORD`: Email password or app password
- `PR_MANAGER_EMAIL`: Default PR manager email

### Optional Configuration

SMTP settings (defaults shown):
- `SMTP_SERVER`: smtp.gmail.com
- `SMTP_PORT`: 587

Model settings:
- `MODEL_NAME`: gpt-4o
- `TEMPERATURE`: 0.7
- `HUMANIZER_TEMPERATURE`: 0.9 (higher for natural language)

## Usage Patterns

### Python API
```python
from pr_agent import PRCommentAgent, PRAgentConfig

# Initialize with custom config
config = PRAgentConfig(
    model_name="gpt-4o",
    temperature=0.7,
    enable_verbose_logging=True
)
agent = PRCommentAgent(config)

# Generate comment
result = agent.generate_comment(
    article_text="Article content...",
    journalist_question="Your perspective?",
    media_outlet="Marketing Week",
    executive_name="Sarah Chen",
    article_url="https://example.com/article",  # optional
    journalist_name="John Smith",  # optional
    pr_manager_email="pr@agency.com"  # optional override
)

# Access results
print(result['humanized_comment'])
print(result['drafted_comment'])
print(result['email_sent'])
```

### Profile Management
```python
from pr_agent.profile_manager import ExecutiveProfileManager

manager = ExecutiveProfileManager()

# List available profiles
profiles = manager.list_profiles()

# Load profile
profile = manager.load_profile("Sarah Chen")

# Create and save new profile
new_profile = manager.create_sample_profile("John Doe")
manager.save_profile("John Doe", new_profile)
```

## Dependencies

Core frameworks:
- **LangChain**: Agent framework and LLM integration
- **LangGraph**: Workflow orchestration
- **OpenAI/Anthropic**: LLM providers
- **Serper/Tavily**: Web search APIs

## Error Handling

The workflow uses graceful degradation:
- Profile loading failures stop execution immediately (critical)
- Media research failures continue with fallback message
- Data research failures continue with "No supporting data available"
- Humanization failures fall back to drafted comment
- Email failures are logged but don't stop workflow

All errors are accumulated in `state['errors']` list.

## LLM Provider Selection

The system chooses LLM provider based on API key availability:
1. If `OPENAI_API_KEY` is set, uses OpenAI models (GPT-4o)
2. Else if `ANTHROPIC_API_KEY` is set, uses Anthropic models (Claude 3.5 Sonnet)
3. Else raises ValueError

Two separate LLM instances are created:
- Main LLM (temperature 0.7): For research and drafting
- Humanizer LLM (temperature 0.9): For natural language refinement
