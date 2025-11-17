# n8n Cloud Setup for PR Agent System

**Complete guide for deploying on n8n Cloud (no Docker required!)**

## Why n8n Cloud?

✅ **Zero Infrastructure**
- No servers to manage
- No Docker installation
- No SSL certificate setup

✅ **Fully Managed**
- Automatic updates
- Built-in backups
- 99.9% uptime SLA

✅ **Instant Deployment**
- Set up in 5 minutes
- Free tier available
- Scale automatically

## Quick Start (5 Minutes)

### 1. Create n8n Cloud Account

1. Go to **https://n8n.io**
2. Click **"Start for free"**
3. Sign up with email
4. Verify your email
5. Log in to your instance (e.g., `https://your-name.app.n8n.cloud`)

### 2. Import Workflow

1. Download `pr-agent-workflow.json` from this repository
2. In n8n Cloud UI:
   - Click **"Workflows"** (left sidebar)
   - Click **"Add workflow"** → **"Import from File"**
   - Select `pr-agent-workflow.json`
   - Click **"Import"**

### 3. Configure API Keys

#### Set Environment Variables

1. Click **"Settings"** (left sidebar)
2. Click **"Environments"**
3. Add these variables:

```env
# LLM Provider (choose one)
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...

# Search Provider (choose one)
SERPER_API_KEY=...
TAVILY_API_KEY=...

# Email (required)
EMAIL_FROM=your-email@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
PR_MANAGER_EMAIL=manager@company.com
```

**Get Gmail App Password:**
1. Go to https://myaccount.google.com/apppasswords
2. Create new app password for "n8n"
3. Copy the 16-character password

### 4. Configure SMTP Credentials

1. Click **"Credentials"** (left sidebar)
2. Click **"Add Credential"**
3. Search for **"SMTP"**
4. Fill in:
   - **Name**: "Gmail SMTP"
   - **User**: your-email@gmail.com
   - **Password**: [your app password]
   - **Host**: smtp.gmail.com
   - **Port**: 587
   - **SSL/TLS**: ✅ Enable
5. Click **"Save"**

### 5. Link SMTP to Workflow

1. Open the imported workflow
2. Click the **"Send Email to PR Manager"** node
3. In "Credential to connect with", select "Gmail SMTP"
4. Click **"Save"** (bottom right)

### 6. Handle Executive Profiles

Since n8n Cloud doesn't have access to local files, use one of these approaches:

#### Option A: Inline Profiles (Quick & Easy)

Edit the **"Load Executive Profile"** function node:

```javascript
// Inline executive profiles
const profiles = {
  "sarah_chen": {
    "name": "Sarah Chen",
    "title": "Chief Brand Officer",
    "company": "BrandForward Agency",
    "expertise": ["Brand strategy", "Marketing ROI", "Consumer insights"],
    "communication_style": "Professional yet approachable, data-driven",
    "tone": "Confident, insightful, forward-thinking",
    "personality_traits": ["Analytical", "Strategic", "Articulate"],
    "talking_points": [
      "Importance of long-term brand building",
      "Data-driven decision making",
      "Consumer-centric approach"
    ],
    "values": ["Authenticity", "Innovation", "Strategic thinking"],
    "speaking_patterns": "Uses concrete examples, references data, asks rhetorical questions",
    "do_not_say": ["Empty buzzwords", "Unsubstantiated claims", "Jargon without context"],
    "preferred_structure": "Hook -> Evidence -> Insight -> Action"
  },
  // Add more executives here
  "john_doe": {
    "name": "John Doe",
    "title": "CEO",
    // ... rest of profile
  }
};

const executiveName = $json.body.executive_name;
const normalizedName = executiveName.toLowerCase().replace(/\s+/g, '_');
const profile = profiles[normalizedName];

if (!profile) {
  return {
    ...$json.body,
    executive_profile: null,
    current_step: 'profile_load_failed',
    errors: [`Profile not found for: ${executiveName}`]
  };
}

return {
  ...$json.body,
  executive_profile: profile,
  current_step: 'profile_loaded',
  errors: []
};
```

#### Option B: GitHub Raw Files (Recommended for Production)

1. Upload executive profiles to a GitHub repository
2. Make it public or use a GitHub token
3. Replace the function node with **HTTP Request** node:

**HTTP Request Node Configuration:**
```json
{
  "url": "https://raw.githubusercontent.com/your-org/pr-profiles/main/profiles/{{ $json.body.executive_name.toLowerCase().replace(' ', '_') }}.json",
  "method": "GET",
  "authentication": "none",
  "options": {}
}
```

Then add a **Set** node to format the response:
```javascript
return {
  ...$items()[0].json.body,
  executive_profile: $json,
  current_step: 'profile_loaded',
  errors: []
};
```

#### Option C: AWS S3 or Cloud Storage

1. Upload profiles to S3 bucket (make public or use presigned URLs)
2. Use HTTP Request node to fetch from S3:

```
https://your-bucket.s3.amazonaws.com/profiles/sarah_chen.json
```

#### Option D: Simple Profile API

Create a simple serverless function (Vercel, Netlify, Cloudflare Workers):

```javascript
// Cloudflare Worker example
export default {
  async fetch(request) {
    const url = new URL(request.url);
    const name = url.searchParams.get('name');

    const profiles = {
      "sarah_chen": { /* profile data */ }
    };

    return new Response(JSON.stringify(profiles[name]), {
      headers: { 'Content-Type': 'application/json' }
    });
  }
}
```

### 7. Activate Workflow

1. Toggle the **"Active"** switch (top right) to ON
2. Click the **"Webhook Trigger"** node
3. Copy the **Production URL**

Example: `https://your-name.app.n8n.cloud/webhook/pr-agent/generate`

### 8. Test Your Workflow

```bash
curl -X POST https://your-name.app.n8n.cloud/webhook/pr-agent/generate \
  -H "Content-Type: application/json" \
  -d '{
    "article_text": "Recent research shows brands investing in long-term brand building see 3x better ROI than those focused solely on performance marketing.",
    "journalist_question": "What advice would you give to CMOs balancing short-term performance with brand building?",
    "media_outlet": "Marketing Week",
    "executive_name": "Sarah Chen",
    "journalist_name": "Rachel Morrison"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "humanized_comment": "...",
  "drafted_comment": "...",
  "email_sent": true,
  "timestamp": "2025-01-17T...",
  "current_step": "completed"
}
```

## Monitoring & Debugging

### View Executions

1. Click **"Executions"** (left sidebar)
2. See all workflow runs with:
   - Status (success/error)
   - Duration
   - Input/output data
3. Click any execution to see detailed logs

### Common Issues

#### "Environment variable not found"

**Fix:** Add the variable in Settings → Environments

#### "SMTP authentication failed"

**Fix:**
- Use Gmail App Password, not regular password
- Enable "Less secure app access" or use 2FA + App Password

#### "Profile not found"

**Fix:**
- Check profile name matches (lowercase with underscores)
- Verify inline profile or external URL is correct

#### "LLM API error"

**Fix:**
- Verify API key is correct
- Check API key has credits
- Ensure no extra spaces in environment variable

## Production Best Practices

### 1. Use External Profile Storage

Don't hardcode profiles in function nodes. Use GitHub, S3, or API for:
- Version control
- Easy updates
- Centralized management

### 2. Set Up Monitoring

Enable n8n Cloud's built-in monitoring:
- Execution history
- Error notifications
- Performance metrics

### 3. Webhook Security

Add authentication to your webhook:

1. Add **IF** node after webhook trigger
2. Check for API key or token:

```javascript
const authHeader = $json.headers.authorization;
const expectedToken = $env.WEBHOOK_AUTH_TOKEN;

if (authHeader !== `Bearer ${expectedToken}`) {
  throw new Error('Unauthorized');
}
```

3. Add `WEBHOOK_AUTH_TOKEN` to environment variables

### 4. Rate Limiting

Add rate limiting logic:

```javascript
// Simple rate limit check
const requestKey = $json.body.executive_name;
const now = Date.now();
const rateLimitWindow = 60000; // 1 minute
const maxRequests = 10;

// Check cache or database for request count
// Throw error if exceeded
```

### 5. Error Notifications

Add Slack/Discord notification on errors:

1. Add Slack/Discord node in error workflow
2. Send notification with error details
3. Include execution ID for debugging

## Pricing

### n8n Cloud Tiers

| Tier | Price | Workflows | Executions |
|------|-------|-----------|------------|
| **Starter** | Free | 20 | 2,500/month |
| **Pro** | $20/mo | Unlimited | 10,000/month |
| **Enterprise** | Custom | Unlimited | Unlimited |

### API Costs (Separate)

- **OpenAI GPT-4o**: ~$0.03-0.10 per comment
- **Anthropic Claude**: ~$0.03-0.08 per comment
- **Serper/Tavily**: ~$0.001 per search
- **Email (SMTP)**: Free with Gmail

**Estimated total:** $0.05-0.15 per comment

## Advanced Configuration

### Custom Domain

Set up custom domain for webhook:

1. Go to Settings → Custom Domains
2. Add your domain (e.g., `api.yourcompany.com`)
3. Update DNS records
4. Use custom URL for webhook

### Multiple Environments

Create separate workflows for:
- Development
- Staging
- Production

Each with different environment variables.

### Backup & Export

Regularly export your workflow:

1. Open workflow
2. Click "..." menu → "Download"
3. Save `pr-agent-workflow.json` to version control

## Scaling

n8n Cloud automatically scales, but you can optimize:

### 1. Use Queue Mode (Pro/Enterprise)

Enable queue mode for high volume:
- Handles concurrent requests
- Prevents timeout issues
- Better resource management

### 2. Optimize Workflow

- Cache API responses when possible
- Minimize unnecessary HTTP requests
- Use parallel execution (already implemented)

### 3. Monitor Performance

Track these metrics:
- Average execution time
- API error rate
- Email delivery rate
- Cost per execution

## Support

### n8n Cloud Support

- **Documentation**: https://docs.n8n.io
- **Community**: https://community.n8n.io
- **Email**: support@n8n.io (Pro/Enterprise)

### Workflow Issues

Check:
1. Execution logs in n8n UI
2. Environment variables are set
3. API keys are valid
4. SMTP credentials are correct

## Migration from Self-Hosted

If you're moving from self-hosted to cloud:

1. Export workflow from self-hosted instance
2. Import to n8n Cloud
3. Re-configure credentials
4. Update environment variables
5. Test thoroughly
6. Update webhook URLs in your applications
7. Deactivate self-hosted workflow

## Conclusion

You now have a production-ready PR Agent System running on n8n Cloud with:

✅ Zero infrastructure management
✅ Automatic scaling and updates
✅ Built-in monitoring and error handling
✅ Professional email notifications
✅ Visual workflow you can modify anytime

**Total setup time: 5-10 minutes**
**Monthly cost: Free tier or $20/month + API costs**

🎉 **Start generating professional PR comments!**
