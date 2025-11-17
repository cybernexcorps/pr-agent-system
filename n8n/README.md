# PR Agent System - n8n Workflow Implementation

This directory contains the complete n8n workflow implementation of the PR Agent System, replacing the LangChain/LangGraph Python implementation with a visual automation workflow.

## Overview

The PR Agent System has been fully reworked as an n8n workflow, providing:
- **Visual workflow design** - See and modify the entire pipeline graphically
- **No-code/low-code** - Reduce maintenance burden
- **Native integrations** - Built-in support for HTTP, email, webhooks
- **Scalability** - n8n handles execution, retries, and scaling
- **Real-time monitoring** - Track executions in the n8n UI

## Architecture

The n8n workflow replicates the original LangChain/LangGraph pipeline:

```
Webhook Trigger
    ↓
Load Executive Profile (Function)
    ↓
┌───────────────┴───────────────┐
│                               │
Media Research (HTTP)    Data Research (HTTP)
│                               │
└───────────────┬───────────────┘
    ↓
Merge Research Results (Function)
    ↓
Draft Comment - LLM (HTTP)
    ↓
Extract Drafted Comment (Function)
    ↓
Humanize Comment - LLM (HTTP)
    ↓
Extract Humanized Comment (Function)
    ↓
Send Email to PR Manager (Email)
    ↓
Prepare Response (Function)
    ↓
Webhook Response
```

### Node Breakdown

| Node | Type | Purpose |
|------|------|---------|
| **Webhook Trigger** | Webhook | Receives POST requests with article data |
| **Load Executive Profile** | Function | Loads executive profile from JSON file |
| **Media Research** | HTTP Request | Calls Serper/Tavily API for media research |
| **Data Research** | HTTP Request | Calls Serper/Tavily API for supporting data |
| **Merge Research Results** | Function | Combines parallel research results |
| **Draft Comment (LLM)** | HTTP Request | Calls OpenAI/Anthropic API to draft comment |
| **Extract Drafted Comment** | Function | Extracts comment from LLM response |
| **Humanize Comment (LLM)** | HTTP Request | Calls OpenAI/Anthropic API to humanize |
| **Extract Humanized Comment** | Function | Extracts final comment from LLM response |
| **Send Email to PR Manager** | Email | Sends approval email via SMTP |
| **Prepare Response** | Function | Formats final JSON response |
| **Webhook Response** | Respond to Webhook | Returns result to caller |
| **Check for Errors** | If | Error handling branch |
| **Error Response** | Function | Formats error response |

## Prerequisites

### 1. n8n Installation

Choose your deployment method:

**Option A: n8n Cloud (Recommended - No Installation!) ☁️**

- Sign up at https://n8n.io
- Free tier available
- No infrastructure management
- Automatic updates and SSL
- **No Docker required!**

👉 See [Cloud Setup Guide](#cloud-setup) below

**Option B: Docker (Self-Hosted)**
```bash
cd n8n
docker-compose up -d
```

**Option C: npm (Self-Hosted)**
```bash
npm install -g n8n
n8n start
```

**Option D: Custom Deployment**
Follow the [n8n installation guide](https://docs.n8n.io/hosting/)

### 2. API Keys Required

You need the same API keys as the Python implementation:

- **LLM Provider** (choose one):
  - `OPENAI_API_KEY` for GPT-4o
  - `ANTHROPIC_API_KEY` for Claude Sonnet 4.5

- **Search Provider** (choose one):
  - `SERPER_API_KEY` for Google Search via Serper
  - `TAVILY_API_KEY` for Tavily search

- **Email (SMTP)**:
  - `EMAIL_FROM` - Sender email address
  - `EMAIL_PASSWORD` - Email password or app password
  - `PR_MANAGER_EMAIL` - Default PR manager email

### 3. Executive Profiles

The workflow expects executive profiles in:
```
/home/user/pr-agent-system/pr_agent/config/executive_profiles/
```

Profile files must be named: `firstname_lastname.json` (lowercase with underscores)

Example: `sarah_chen.json`

## Setup Instructions

### Cloud Setup

#### Step 1: Sign Up for n8n Cloud

1. Go to https://n8n.io
2. Click **"Start for free"**
3. Create your account
4. Log in to your n8n Cloud instance

#### Step 2: Import Workflow

1. In n8n Cloud UI, click **"Workflows"** → **"Add workflow"** → **"Import from File"**
2. Download `pr-agent-workflow.json` from this repository
3. Select the file and click **"Import"**

#### Step 3: Configure Environment Variables

In n8n Cloud, go to **Settings** → **Environments** and add:

```env
OPENAI_API_KEY=sk-...
SERPER_API_KEY=...
EMAIL_FROM=your-email@gmail.com
EMAIL_PASSWORD=your_app_password
PR_MANAGER_EMAIL=manager@agency.com
```

#### Step 4: Handle Executive Profiles

Since n8n Cloud doesn't have access to local files, choose one of these options:

**Option 1: Inline Profiles**
- Edit the "Load Executive Profile" function node
- Add profile JSON directly in the code
- See [QUICK_START.md](QUICK_START.md#step-6-handle-executive-profiles-1-minute) for example

**Option 2: External API**
- Host profiles in cloud storage (S3, GitHub, etc.)
- Replace function node with HTTP Request node
- Fetch profiles from your API

#### Step 5: Configure SMTP & Activate

1. Add SMTP credentials in **Credentials** menu
2. Link SMTP credential to "Send Email" node
3. Toggle **Active** switch
4. Copy webhook URL and test!

**Done! No Docker needed!** 🎉

---

### Self-Hosted Setup

#### Step 1: Import Workflow

1. Open n8n UI (default: http://localhost:5678)
2. Click **"Workflows"** → **"Import from File"**
3. Select `n8n/pr-agent-workflow.json`
4. Click **"Import"**

### Step 2: Configure Environment Variables

In n8n, set environment variables:

**Method A: Docker**
```bash
docker run -d --name n8n \
  -p 5678:5678 \
  -e OPENAI_API_KEY="sk-..." \
  -e SERPER_API_KEY="..." \
  -e EMAIL_FROM="pr@agency.com" \
  -e EMAIL_PASSWORD="your_app_password" \
  -e PR_MANAGER_EMAIL="manager@agency.com" \
  -v ~/.n8n:/home/node/.n8n \
  -v /home/user/pr-agent-system:/data \
  n8nio/n8n
```

**Method B: .env file**
Create `~/.n8n/.env`:
```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
SERPER_API_KEY=...
TAVILY_API_KEY=...
EMAIL_FROM=pr@agency.com
EMAIL_PASSWORD=your_app_password
PR_MANAGER_EMAIL=manager@agency.com
```

### Step 3: Configure SMTP Credentials

1. In n8n UI, go to **Credentials** → **New Credential**
2. Select **"SMTP"**
3. Enter:
   - **User**: Your email address
   - **Password**: Your email password/app password
   - **Host**: `smtp.gmail.com` (or your SMTP server)
   - **Port**: `587`
   - **SSL/TLS**: Enable
4. Save credential
5. Open the workflow and select this credential in the **"Send Email to PR Manager"** node

### Step 4: Activate Workflow

1. Open the imported workflow
2. Click **"Active"** toggle in top-right
3. Copy the webhook URL (shown in the Webhook Trigger node)

## Usage

### API Endpoint

Once activated, the workflow exposes a webhook endpoint:

```
POST https://your-n8n-instance.com/webhook/pr-agent/generate
```

### Request Format

```json
{
  "article_text": "Recent research shows brands investing in long-term brand building see 3x better ROI...",
  "journalist_question": "What advice would you give to CMOs balancing short-term performance with brand building?",
  "media_outlet": "Marketing Week",
  "executive_name": "Sarah Chen",
  "journalist_name": "Rachel Morrison",
  "article_url": "https://example.com/article",
  "pr_manager_email": "manager@agency.com"
}
```

**Required fields:**
- `article_text`
- `journalist_question`
- `media_outlet`
- `executive_name`

**Optional fields:**
- `journalist_name`
- `article_url`
- `pr_manager_email` (overrides default)

### Response Format

```json
{
  "success": true,
  "article_text": "...",
  "article_url": "https://example.com/article",
  "journalist_question": "...",
  "media_outlet": "Marketing Week",
  "journalist_name": "Rachel Morrison",
  "executive_name": "Sarah Chen",
  "executive_profile": { ... },
  "media_research": { ... },
  "supporting_data": { ... },
  "drafted_comment": "...",
  "humanized_comment": "...",
  "timestamp": "2025-01-17T12:00:00.000Z",
  "approval_status": "pending",
  "email_sent": true,
  "pr_manager_email": "manager@agency.com",
  "current_step": "completed",
  "errors": []
}
```

### Example with cURL

```bash
curl -X POST https://your-n8n-instance.com/webhook/pr-agent/generate \
  -H "Content-Type: application/json" \
  -d '{
    "article_text": "Recent research shows brands investing in long-term brand building see 3x better ROI...",
    "journalist_question": "What advice would you give to CMOs balancing short-term performance with brand building?",
    "media_outlet": "Marketing Week",
    "executive_name": "Sarah Chen"
  }'
```

### Example with Python

```python
import requests

url = "https://your-n8n-instance.com/webhook/pr-agent/generate"

payload = {
    "article_text": "Recent research shows brands investing in long-term brand building see 3x better ROI...",
    "journalist_question": "What advice would you give to CMOs balancing short-term performance with brand building?",
    "media_outlet": "Marketing Week",
    "executive_name": "Sarah Chen",
    "journalist_name": "Rachel Morrison"
}

response = requests.post(url, json=payload)
result = response.json()

print(result["humanized_comment"])
```

## Configuration

### Customizing LLM Models

To change the LLM model used:

1. Open the workflow in n8n
2. Click on **"Draft Comment (LLM)"** node
3. Modify the `model` field in the JSON body:
   - For OpenAI: `"gpt-4o"`, `"gpt-4-turbo"`, `"gpt-3.5-turbo"`
   - For Anthropic: `"claude-sonnet-4-5-20250929"`, `"claude-3-5-sonnet-20241022"`
4. Repeat for **"Humanize Comment (LLM)"** node
5. Save workflow

### Customizing Temperature

- **Draft Comment**: Default `0.7` (more factual)
- **Humanize Comment**: Default `0.9` (more creative)

Modify in the JSON body of each LLM node.

### Customizing Search Results

Modify the `num` parameter in the search nodes:
- **Media Research** node: Change `"num": "5"` to desired count
- **Data Research** node: Change `"num": "5"` to desired count

### Error Handling

The workflow includes error handling:
- Profile load failures → Return error response
- API failures → Graceful degradation with fallback values
- Email failures → Logged but workflow continues

## Monitoring and Debugging

### Execution History

1. Open n8n UI
2. Click **"Executions"** in left sidebar
3. View all workflow runs with status and timing
4. Click any execution to see detailed logs

### Testing Individual Nodes

1. Open workflow editor
2. Click **"Execute Workflow"** button
3. Provide test data in the webhook trigger
4. View output of each node in real-time

### Logs

Check n8n logs for errors:

**Docker:**
```bash
docker logs n8n
```

**npm:**
```bash
# Logs are in ~/.n8n/logs/
tail -f ~/.n8n/logs/n8n.log
```

## Advantages Over LangChain/LangGraph

### Visual Design
- See entire workflow at a glance
- No need to read Python code
- Easy to understand data flow

### No Code Changes
- Modify workflow in UI
- No redeployment needed
- Test changes instantly

### Built-in Features
- Automatic retries
- Error handling
- Execution history
- Monitoring dashboard

### Easier Maintenance
- No Python dependencies
- No version conflicts
- Update nodes via UI

### Better Collaboration
- Non-developers can modify
- Visual debugging
- Share workflows as JSON

## Migration from Python Implementation

### What's Different

1. **No Python code required** - All logic in n8n nodes
2. **Function nodes replace Python functions** - JavaScript in function nodes
3. **HTTP nodes replace LangChain LLM calls** - Direct API calls
4. **Email node replaces SMTP tool** - Native email support
5. **Webhook replaces Python API** - HTTP endpoint

### What's the Same

1. **Executive profiles** - Same JSON files in same location
2. **API keys** - Same APIs (OpenAI, Anthropic, Serper, Tavily)
3. **Workflow logic** - Same sequence of steps
4. **Output format** - Same JSON response structure
5. **Email templates** - Similar HTML email format

### Python Libraries No Longer Needed

The following Python dependencies are replaced by n8n:
- ✅ `langchain` → n8n workflow engine
- ✅ `langgraph` → n8n node connections
- ✅ `langchain-openai` → HTTP Request nodes
- ✅ `langchain-anthropic` → HTTP Request nodes
- ✅ `chromadb` → (Can be added via n8n-nodes-chromadb if needed)
- ✅ SMTP libraries → Email Send node

## Performance

### Expected Performance

- **First execution**: 10-30 seconds (parallel research)
- **Subsequent executions**: 10-30 seconds (no caching by default)
- **Concurrent executions**: Limited by n8n instance resources

### Adding Caching

To add Redis caching in n8n:

1. Install n8n-nodes-redis community node
2. Add cache check nodes before expensive operations
3. Store results in Redis with TTL
4. Check cache before making API calls

## Troubleshooting

### Workflow Not Activating

**Issue**: Can't activate workflow
**Fix**:
- Check all required credentials are configured
- Ensure webhook path is unique
- Check n8n logs for errors

### Profile Not Loading

**Issue**: "Failed to load profile" error
**Fix**:
- Verify profile file exists in correct directory
- Check filename format: `firstname_lastname.json`
- Ensure n8n has read access to profile directory
- Use absolute path in function node

### LLM API Errors

**Issue**: HTTP 401 or 403 from LLM API
**Fix**:
- Verify API key is set correctly
- Check API key has sufficient credits
- Ensure correct API endpoint URL
- Check header format (Bearer vs x-api-key)

### Email Not Sending

**Issue**: Email node fails
**Fix**:
- Verify SMTP credentials
- Check email password (use App Password for Gmail)
- Ensure port 587 is open
- Test SMTP connection manually

### Search API Errors

**Issue**: Serper/Tavily API fails
**Fix**:
- Check API key validity
- Verify rate limits not exceeded
- Check API endpoint URL
- Test API key with curl

## Advanced Features

### Adding Parallel Processing

The workflow already runs Media Research and Data Research in parallel. To add more parallel nodes:

1. Connect multiple nodes to the same predecessor
2. Add a merge/join node to combine results

### Adding Retry Logic

1. Click on any HTTP node
2. Go to **Settings** → **Retry On Fail**
3. Set **Max Retries** (e.g., 3)
4. Set **Wait Between Tries** (e.g., 1000ms)

### Adding Webhooks for Async Processing

1. Add a second webhook for status updates
2. Store execution ID in database/cache
3. Poll for completion or use webhooks

### Adding Authentication

1. Add **Basic Auth** node after webhook trigger
2. Or use **API Key** verification in function node
3. Or use n8n's built-in webhook authentication

## Production Deployment

### Security

1. **Use HTTPS**: Deploy n8n behind reverse proxy with SSL
2. **Secure webhook URLs**: Use authentication
3. **Environment variables**: Never hardcode API keys
4. **Network security**: Restrict access to n8n UI

### Scaling

1. **Horizontal scaling**: Deploy multiple n8n instances
2. **Queue mode**: Use Redis for queue-based execution
3. **Load balancing**: Use nginx/HAProxy
4. **Database**: Use PostgreSQL instead of SQLite

### Monitoring

1. **LangSmith**: Add HTTP nodes to send traces to LangSmith
2. **Prometheus**: Export n8n metrics
3. **Alerting**: Set up alerts for failed executions
4. **Logging**: Centralize logs with ELK/Loki

### Backup

```bash
# Backup n8n data directory
tar -czf n8n-backup-$(date +%Y%m%d).tar.gz ~/.n8n

# Backup workflow as JSON
# Export from n8n UI or use CLI
```

## Support

For issues specific to:
- **n8n setup**: See [n8n documentation](https://docs.n8n.io)
- **Workflow logic**: Review this README and node configurations
- **API integration**: Check respective API documentation (OpenAI, Anthropic, Serper)

## Next Steps

1. ✅ Import workflow
2. ✅ Configure credentials
3. ✅ Test with sample data
4. ✅ Monitor first executions
5. ✅ Integrate with your applications
6. 📈 Add monitoring and alerting
7. 🚀 Deploy to production

## License

MIT License - Same as the original PR Agent System

---

**Made with ❤️ by CyberNexCorps**
