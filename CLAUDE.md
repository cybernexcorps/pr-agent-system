# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PR Agent System is an AI-powered comment generation system for branding agency executives. It automates the process of generating professional PR comments for media inquiries through a visual n8n automation workflow.

## Implementation

This project uses **n8n** - a visual workflow automation platform. All logic is defined in the n8n workflow JSON file, not in code.

### Key Files

- `n8n/pr-agent-workflow.json` - Main workflow definition (import into n8n)
- `n8n/README.md` - Complete n8n documentation
- `n8n/QUICK_START.md` - 5-minute setup guide
- `n8n/CLOUD_SETUP.md` - Cloud deployment guide
- `n8n/MIGRATION_GUIDE.md` - Migration notes
- `n8n/docker-compose.yml` - Docker deployment configuration
- `n8n/.env.example` - Environment variables template

### Executive Profiles

- `pr_agent/config/executive_profiles/` - Example profile JSON files
- Used as reference for creating profiles in n8n Cloud

## Quick Start

### For n8n Cloud (Recommended)

```bash
# No installation needed!
# 1. Sign up at https://n8n.io
# 2. Import n8n/pr-agent-workflow.json in the UI
# 3. Configure environment variables in Settings → Environments
# 4. Add SMTP credentials
# 5. Activate workflow
```

See `n8n/CLOUD_SETUP.md` for detailed instructions.

### For Self-Hosted

```bash
# Start n8n with Docker
cd n8n
docker-compose up -d

# View n8n UI
# Open http://localhost:5678

# View logs
docker logs pr-agent-n8n

# Stop n8n
docker-compose down

# Production deployment (includes PostgreSQL, Redis, nginx)
docker-compose --profile production up -d
```

See `n8n/QUICK_START.md` for detailed instructions.

## Architecture

The n8n workflow implements a multi-step PR comment generation pipeline with 14 nodes. See workflow JSON for complete implementation details.

## Configuration

Required environment variables:
- LLM Provider: OPENAI_API_KEY or ANTHROPIC_API_KEY
- Search: SERPER_API_KEY or TAVILY_API_KEY  
- Email: EMAIL_FROM, EMAIL_PASSWORD, PR_MANAGER_EMAIL

See `n8n/README.md` for complete configuration guide.

## Documentation

For detailed guides, see:
- `n8n/QUICK_START.md` - Setup guide
- `n8n/CLOUD_SETUP.md` - Cloud deployment  
- `n8n/README.md` - Complete documentation
- `N8N_IMPLEMENTATION.md` - Architecture overview

**Note:** This repository contains only the n8n workflow implementation. All logic is in the visual workflow, not in code files.
