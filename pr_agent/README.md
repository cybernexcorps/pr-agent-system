# PR Comment Agent

An AI-powered system for generating professional PR comments on behalf of branding agency executives using LangChain and LangGraph.

## Overview

The PR Comment Agent is a sophisticated multi-step AI system that automates the process of generating executive comments for media inquiries. It follows a comprehensive workflow that ensures comments are well-researched, on-brand, data-driven, and authentically human.

## Workflow

```
Article + Question → Media Research → Executive Profile → Data Research
                                                                ↓
                                         Email to PR Manager ← Humanization ← Comment Draft
```

### Step-by-Step Process

1. **Input Processing**: Receives article, journalist question, and media outlet information
2. **Media Research**: Analyzes the media outlet and journalist's focus areas
3. **Profile Loading**: Loads executive's communication style and expertise
4. **Data Research**: Searches the internet for supporting statistics and insights
5. **Comment Drafting**: Generates initial professional comment
6. **Humanization**: Refines the comment to sound natural and authentic
7. **Email Notification**: Sends to PR manager for approval

## Features

- **Multi-Agent Architecture**: Specialized agents for each workflow step
- **Executive Profile Management**: Maintains consistent voice across comments
- **Web Research Integration**: Finds relevant data to support arguments
- **AI Humanization**: Makes generated text sound natural and authentic
- **Email Notifications**: Automated approval workflow
- **LangGraph Orchestration**: Reliable multi-step pipeline management

## Installation

### Prerequisites

- Python 3.8+
- API keys for at least one LLM provider (OpenAI or Anthropic)
- API key for web search (Serper or Tavily)
- Email credentials for notifications

### Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements-pr-agent.txt
   ```

2. **Configure Environment**:
   ```bash
   cp pr_agent/.env.example pr_agent/.env
   # Edit .env with your API keys
   ```

3. **Create Executive Profiles**:
   - Add executive profiles to `pr_agent/config/executive_profiles/`
   - Use the provided `sarah_chen.json` as a template

## Usage

### Python API

```python
from pr_agent import PRCommentAgent, PRAgentConfig

# Initialize agent
config = PRAgentConfig()
agent = PRCommentAgent(config)

# Generate comment
result = agent.generate_comment(
    article_text="Article content here...",
    journalist_question="What's your perspective on this trend?",
    media_outlet="TechCrunch",
    executive_name="Sarah Chen",
    article_url="https://example.com/article",
    journalist_name="John Smith",
    pr_manager_email="pr@agency.com"
)

# Access results
print("Drafted Comment:", result['drafted_comment'])
print("Humanized Comment:", result['humanized_comment'])
print("Email Sent:", result['email_sent'])
```

### Jupyter Notebook

See `examples/pr_agent_demo.ipynb` for an interactive walkthrough.

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes* | OpenAI API key |
| `ANTHROPIC_API_KEY` | Yes* | Anthropic API key |
| `SERPER_API_KEY` | Yes** | Serper (Google Search) API key |
| `TAVILY_API_KEY` | Yes** | Tavily search API key |
| `EMAIL_FROM` | Yes | Sender email address |
| `EMAIL_PASSWORD` | Yes | Email password or app password |
| `PR_MANAGER_EMAIL` | Yes | Default PR manager email |
| `SMTP_SERVER` | No | SMTP server (default: smtp.gmail.com) |
| `SMTP_PORT` | No | SMTP port (default: 587) |

\* At least one LLM provider required
\** At least one search provider required

### Configuration Object

```python
from pr_agent import PRAgentConfig

config = PRAgentConfig(
    model_name="gpt-4o",
    temperature=0.7,
    humanizer_temperature=0.9,
    max_search_results=5,
    enable_verbose_logging=True
)
```

## Executive Profiles

Executive profiles define the communication style, expertise, and personality of the executive. Profiles are stored as JSON files in `pr_agent/config/executive_profiles/`.

### Profile Structure

```json
{
  "name": "Executive Name",
  "title": "Chief Brand Officer",
  "company": "Agency Name",
  "expertise": ["Area 1", "Area 2"],
  "communication_style": "Description of how they communicate",
  "tone": "Overall tone characteristics",
  "personality_traits": ["Trait 1", "Trait 2"],
  "talking_points": ["Key message 1", "Key message 2"],
  "values": ["Value 1", "Value 2"],
  "speaking_patterns": "Description of speech patterns",
  "do_not_say": ["Things to avoid"],
  "preferred_structure": "How to structure responses"
}
```

### Managing Profiles

```python
from pr_agent import ProfileManager

manager = ProfileManager()

# List profiles
profiles = manager.list_profiles()

# Load profile
profile = manager.load_profile("Sarah Chen")

# Create new profile
new_profile = manager.create_sample_profile("John Doe")
manager.save_profile("John Doe", new_profile)
```

## Architecture

### Components

- **`agent.py`**: Main orchestrator using LangGraph
- **`agents/`**: Specialized agents (MediaResearcher, DataResearcher, CommentDrafter, Humanizer)
- **`tools/`**: Web search, media research, email sending
- **`prompts/`**: LLM prompt templates
- **`config.py`**: Configuration management
- **`profile_manager.py`**: Executive profile handling
- **`state.py`**: Workflow state definition

### Dependencies

- **LangChain**: Agent framework and LLM integration
- **LangGraph**: Workflow orchestration
- **OpenAI/Anthropic**: LLM providers
- **Serper/Tavily**: Web search APIs

## Examples

### Basic Usage

```python
from pr_agent import PRCommentAgent

agent = PRCommentAgent()

result = agent.generate_comment(
    article_text="New study shows brands investing in long-term building see 3x ROI...",
    journalist_question="How should CMOs balance short-term performance with brand building?",
    media_outlet="Marketing Week",
    executive_name="Sarah Chen"
)
```

### Custom Configuration

```python
from pr_agent import PRCommentAgent, PRAgentConfig

config = PRAgentConfig(
    model_name="gpt-4o",
    temperature=0.7,
    enable_verbose_logging=True,
    max_search_results=10
)

agent = PRCommentAgent(config)
```

## Troubleshooting

### Common Issues

1. **"No valid API key configured"**
   - Ensure OPENAI_API_KEY or ANTHROPIC_API_KEY is set in .env

2. **"Profile not found"**
   - Check that the executive profile JSON exists in the profiles directory
   - Profile filename should be lowercase with underscores (e.g., sarah_chen.json)

3. **"Email sending failed"**
   - Verify EMAIL_FROM and EMAIL_PASSWORD are correct
   - For Gmail, use an App Password instead of your regular password
   - Ensure "Less secure app access" is enabled (if applicable)

4. **Search errors**
   - Confirm SERPER_API_KEY or TAVILY_API_KEY is valid
   - Check API rate limits and quotas

## Contributing

Contributions are welcome! Areas for enhancement:

- Additional LLM providers
- More sophisticated entity extraction
- Integration with CRM systems
- Multi-language support
- Analytics dashboard

## License

This project is part of the long-term-ad-effectiveness framework.

## Support

For issues or questions, please open an issue in the repository.
