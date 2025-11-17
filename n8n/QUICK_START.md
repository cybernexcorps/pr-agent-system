# PR Agent n8n Workflow - Quick Start Guide

Get the PR Agent System running with n8n in under 10 minutes!

## Choose Your Setup

### Option A: n8n Cloud (Recommended - No Docker!) ☁️

**Best for:** Production use, no infrastructure management

**Advantages:**
- No Docker or server setup needed
- Automatic updates and scaling
- Built-in SSL/HTTPS
- Managed backups

**Prerequisites:**
- ✅ n8n Cloud account (free tier available at https://n8n.io)
- ✅ OpenAI API key OR Anthropic API key
- ✅ Serper API key OR Tavily API key
- ✅ Gmail account with App Password (or other SMTP credentials)
- ✅ At least one executive profile JSON file

👉 **[Skip to Cloud Setup Instructions](#cloud-setup-5-minutes)**

---

### Option B: Self-Hosted with Docker 🐳

**Best for:** Local development, custom infrastructure

**Prerequisites:**
- ✅ Docker and Docker Compose installed
- ✅ OpenAI API key OR Anthropic API key
- ✅ Serper API key OR Tavily API key
- ✅ Gmail account with App Password (or other SMTP credentials)
- ✅ At least one executive profile JSON file

👉 **[Skip to Self-Hosted Setup Instructions](#self-hosted-setup-10-minutes)**

---

## Cloud Setup (5 minutes)

### Step 1: Sign Up for n8n Cloud (1 minute)

1. Go to https://n8n.io
2. Click **"Start for free"**
3. Create account (email + password)
4. Verify email
5. Log in to your n8n Cloud instance

### Step 2: Import Workflow (1 minute)

1. In n8n Cloud UI, click **"Workflows"** → **"Add workflow"** → **"Import from File"**
2. Download `pr-agent-workflow.json` from this repository
3. Select the file and click **"Import"**

### Step 3: Configure Environment Variables (1 minute)

1. In your n8n Cloud instance, go to **"Settings"** → **"Environments"**
2. Add these variables:

```env
OPENAI_API_KEY=sk-...           # OR
ANTHROPIC_API_KEY=sk-ant-...

SERPER_API_KEY=...              # OR
TAVILY_API_KEY=...

EMAIL_FROM=your-email@gmail.com
EMAIL_PASSWORD=your_app_password
PR_MANAGER_EMAIL=manager@agency.com
```

**Gmail App Password:** Generate at https://myaccount.google.com/apppasswords

### Step 4: Configure SMTP Credentials (1 minute)

1. Click **"Credentials"** → **"Add Credential"**
2. Search for **"SMTP"** and select it
3. Fill in:
   - **User**: Your email address
   - **Password**: Your app password
   - **Host**: `smtp.gmail.com`
   - **Port**: `587`
   - **SSL/TLS**: ✅ Enable
4. Click **"Save"**

### Step 5: Link SMTP to Workflow (30 seconds)

1. Open the **"PR Agent System - Complete Workflow"**
2. Click the **"Send Email to PR Manager"** node
3. Select your SMTP credential from dropdown
4. Click **"Save"**

### Step 6: Handle Executive Profiles (1 minute)

Since executive profiles are local files, you have two options:

**Option A: Inline Profiles (Quick)**

Edit the "Load Executive Profile" function node to use inline JSON:

```javascript
// Inline profile data
const profiles = {
  "sarah_chen": {
    "name": "Sarah Chen",
    "title": "Chief Brand Officer",
    "company": "BrandForward Agency",
    // ... rest of profile
  }
};

const executiveName = $json.body.executive_name;
const normalizedName = executiveName.toLowerCase().replace(/\s+/g, '_');

return {
  ...$json.body,
  executive_profile: profiles[normalizedName],
  current_step: 'profile_loaded',
  errors: []
};
```

**Option B: External API (Production)**

1. Host profiles in a simple API or cloud storage (S3, GitHub)
2. Replace the function node with an HTTP Request node
3. Fetch profiles from your API

### Step 7: Activate and Test (1 minute)

1. Toggle **"Active"** switch to ON
2. Copy the **Production URL** from Webhook Trigger node
3. Test with curl:

```bash
curl -X POST https://your-instance.app.n8n.cloud/webhook/pr-agent/generate \
  -H "Content-Type: application/json" \
  -d '{
    "article_text": "Test article...",
    "journalist_question": "Test question?",
    "media_outlet": "Test Outlet",
    "executive_name": "Sarah Chen"
  }'
```

🎉 **Done! You're running on n8n Cloud with zero infrastructure!**

---

## Self-Hosted Setup (10 minutes)

### Step 1: Configure Environment (2 minutes)

```bash
cd n8n
cp .env.example .env
```

Edit `.env` and fill in:

```env
# Choose ONE LLM provider
OPENAI_API_KEY=sk-...           # OR
ANTHROPIC_API_KEY=sk-ant-...

# Choose ONE search provider
SERPER_API_KEY=...              # OR
TAVILY_API_KEY=...

# Email (required)
EMAIL_FROM=your-email@gmail.com
EMAIL_PASSWORD=your_app_password
PR_MANAGER_EMAIL=manager@agency.com
```

**Gmail App Password:** Generate at https://myaccount.google.com/apppasswords

## Step 2: Start n8n (1 minute)

```bash
docker-compose up -d
```

Wait 30 seconds for n8n to start, then open:
```
http://localhost:5678
```

## Step 3: Create n8n Account (1 minute)

1. Open http://localhost:5678
2. Create your n8n account (email + password)
3. Click **"Get Started"**

## Step 4: Import Workflow (2 minutes)

1. Click **"Workflows"** in left sidebar
2. Click **"Import from File"** button
3. Select `pr-agent-workflow.json`
4. Click **"Import"**

## Step 5: Configure SMTP Credentials (2 minutes)

1. Click **"Credentials"** in left sidebar
2. Click **"Add Credential"**
3. Search for **"SMTP"** and select it
4. Fill in:
   - **User**: Your email address (e.g., `your-email@gmail.com`)
   - **Password**: Your app password from Step 1
   - **Host**: `smtp.gmail.com`
   - **Port**: `587`
   - **SSL/TLS**: ✅ Enable
5. Click **"Save"**

## Step 6: Link SMTP to Workflow (1 minute)

1. Open the **"PR Agent System - Complete Workflow"**
2. Click the **"Send Email to PR Manager"** node
3. In **"Credential to connect with"** dropdown, select your SMTP credential
4. Click **"Save"** (bottom right)

## Step 7: Activate Workflow (1 minute)

1. Toggle **"Active"** switch (top right) to ON
2. Click the **"Webhook Trigger"** node
3. Copy the **Production URL** (looks like: `http://localhost:5678/webhook/pr-agent/generate`)

## Step 8: Test It! (2 minutes)

### Option A: Using cURL

```bash
curl -X POST http://localhost:5678/webhook/pr-agent/generate \
  -H "Content-Type: application/json" \
  -d '{
    "article_text": "Recent research shows brands investing in long-term brand building see 3x better ROI than those focused solely on performance marketing. A study of 500 brands over 5 years found that companies maintaining consistent brand investment during economic downturns recovered faster and gained market share.",
    "journalist_question": "What advice would you give to CMOs balancing short-term performance with brand building?",
    "media_outlet": "Marketing Week",
    "executive_name": "Sarah Chen"
  }'
```

### Option B: Using Python

```python
import requests
import json

url = "http://localhost:5678/webhook/pr-agent/generate"

payload = {
    "article_text": "Recent research shows brands investing in long-term brand building see 3x better ROI...",
    "journalist_question": "What advice would you give to CMOs balancing short-term performance with brand building?",
    "media_outlet": "Marketing Week",
    "executive_name": "Sarah Chen"
}

response = requests.post(url, json=payload)
result = response.json()

print("Humanized Comment:")
print(result["humanized_comment"])
print("\n✅ Email sent:", result["email_sent"])
```

### Option C: Using Postman

1. Open Postman
2. Create new POST request
3. URL: `http://localhost:5678/webhook/pr-agent/generate`
4. Headers: `Content-Type: application/json`
5. Body (raw JSON):
```json
{
  "article_text": "Recent research shows brands investing in long-term brand building see 3x better ROI...",
  "journalist_question": "What advice would you give to CMOs balancing short-term performance with brand building?",
  "media_outlet": "Marketing Week",
  "executive_name": "Sarah Chen"
}
```
6. Click **"Send"**

## Expected Result

You should receive a JSON response like:

```json
{
  "success": true,
  "humanized_comment": "This research validates what we've seen with our clients for years. The key isn't choosing between short-term performance and long-term brand building - it's integrating them carefully...",
  "drafted_comment": "...",
  "email_sent": true,
  "timestamp": "2025-01-17T12:34:56.789Z",
  "current_step": "completed"
}
```

And you'll receive an email at `PR_MANAGER_EMAIL` with the full comment for approval!

## Troubleshooting

### "Cannot connect to n8n"
```bash
# Check if n8n is running
docker ps | grep pr-agent-n8n

# View logs
docker logs pr-agent-n8n

# Restart
docker-compose restart
```

### "Profile not found"
- Verify profile exists: `ls ../pr_agent/config/executive_profiles/`
- Check filename format: `sarah_chen.json` (lowercase, underscores)
- Ensure Docker has access to mounted volume

### "LLM API Error"
- Check API key is valid
- Verify API key has credits
- Check environment variables: `docker exec pr-agent-n8n env | grep API_KEY`

### "Email failed to send"
- Verify App Password is correct (not your regular Gmail password)
- Check SMTP credentials in n8n UI
- Test SMTP manually:
```bash
docker exec -it pr-agent-n8n sh
telnet smtp.gmail.com 587
```

### "Webhook returns 404"
- Ensure workflow is **Active** (toggle in top right)
- Copy exact URL from Webhook Trigger node
- Check n8n is running on port 5678

## Next Steps

### ✅ You're Ready!

Your PR Agent System is now running on n8n!

**What to do next:**

1. **Create more executive profiles**
   - Copy `pr_agent/config/executive_profiles/sarah_chen.json`
   - Customize for each executive
   - Save as `firstname_lastname.json`

2. **Integrate with your application**
   - Call the webhook from your web app
   - Build a simple UI for PR managers
   - Set up Slack notifications

3. **Monitor executions**
   - Open n8n UI → **"Executions"**
   - View timing and success rate
   - Debug failed executions

4. **Customize the workflow**
   - Adjust LLM temperature
   - Modify prompts
   - Add more research steps
   - Integrate with CRM

5. **Add production features**
   - Enable PostgreSQL database
   - Add Redis caching
   - Set up SSL with nginx
   - Configure monitoring

## Production Deployment

For production, use:

```bash
# Start with PostgreSQL and Redis
docker-compose --profile production up -d

# Or just Redis caching
docker-compose --profile caching up -d
```

See `README.md` for detailed production setup.

## Support

- **n8n Issues**: https://community.n8n.io
- **Workflow Issues**: Check execution logs in n8n UI
- **API Issues**: Test APIs with cURL first

## Congratulations! 🎉

You've successfully deployed the PR Agent System on n8n!

The system is now:
- ✅ Accepting webhook requests
- ✅ Loading executive profiles
- ✅ Researching media and data
- ✅ Generating PR comments
- ✅ Sending approval emails

**Time to generate some amazing PR comments!** 🚀
