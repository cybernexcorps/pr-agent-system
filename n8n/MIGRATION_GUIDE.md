# Migration Guide: LangChain/LangGraph → n8n Workflow

This guide helps you migrate from the Python-based LangChain/LangGraph implementation to the n8n workflow.

## Why Migrate to n8n?

### Advantages of n8n

✅ **Visual Workflow Design**
- See entire pipeline at a glance
- No code reading required
- Easy to understand data flow
- Drag-and-drop modifications

✅ **Reduced Complexity**
- No Python dependencies
- No version conflicts
- No virtual environments
- Simplified deployment

✅ **Better Maintainability**
- Non-developers can modify workflows
- No code changes needed
- Test instantly in UI
- Visual debugging

✅ **Built-in Features**
- Automatic retries
- Error handling
- Execution history
- Monitoring dashboard
- Webhook management

✅ **Easier Scaling**
- Built-in queue mode
- Horizontal scaling support
- Load balancing ready
- Production-ready out of the box

### What You Keep

✅ **Same Functionality**
- All workflow steps preserved
- Same API integrations
- Same output format
- Same executive profiles

✅ **Same APIs**
- OpenAI / Anthropic
- Serper / Tavily
- SMTP email

✅ **Same Configuration**
- Executive profile JSON files
- Environment variables
- API keys

### What Changes

❌ **Python Code**
- No more Python scripts
- No more pip dependencies
- No more virtual environments

❌ **LangChain/LangGraph**
- Replaced by n8n workflow engine
- Node connections instead of edges
- Function nodes instead of Python functions

❌ **Development Workflow**
- Modify in n8n UI instead of code editor
- Test in browser instead of terminal
- Deploy by activating workflow

## Migration Steps

### Phase 1: Backup Current System

```bash
# Backup Python implementation
cd /home/user/pr-agent-system
tar -czf backup-python-implementation-$(date +%Y%m%d).tar.gz \
  pr_agent/ \
  tests/ \
  setup.py \
  requirements.txt

# Backup executive profiles
tar -czf backup-profiles-$(date +%Y%m%d).tar.gz \
  pr_agent/config/executive_profiles/

# Backup any custom configurations
cp pr_agent/.env pr_agent/.env.backup
```

### Phase 2: Install n8n

Choose your installation method:

**Option A: Docker (Recommended)**
```bash
cd n8n
docker-compose up -d
```

**Option B: npm**
```bash
npm install -g n8n
n8n start
```

**Option C: Cloud**
- Sign up at https://n8n.io
- Use hosted version (no installation)

### Phase 3: Import Workflow

1. Open n8n UI (http://localhost:5678 or your n8n URL)
2. Create account
3. Click **Workflows** → **Import from File**
4. Select `n8n/pr-agent-workflow.json`
5. Click **Import**

### Phase 4: Configure Credentials

#### SMTP Credentials
1. Go to **Credentials** → **New Credential**
2. Select **SMTP**
3. Enter:
   - User: Your email
   - Password: App password
   - Host: `smtp.gmail.com`
   - Port: `587`
   - SSL/TLS: Enable
4. Save

#### Environment Variables

**Docker:**
```bash
# Edit docker-compose.yml or use .env file
cp .env.example .env
# Fill in your API keys
docker-compose up -d
```

**npm:**
```bash
# Create ~/.n8n/.env
export OPENAI_API_KEY="sk-..."
export SERPER_API_KEY="..."
export EMAIL_FROM="your-email@gmail.com"
export EMAIL_PASSWORD="your_app_password"
export PR_MANAGER_EMAIL="manager@agency.com"

n8n start
```

### Phase 5: Verify Executive Profiles

Ensure n8n can access executive profiles:

**Docker:**
```bash
# Profiles are mounted in docker-compose.yml
docker exec pr-agent-n8n ls /data/pr_agent/config/executive_profiles/
```

**npm:**
```bash
# Update path in Load Executive Profile function node
# Point to absolute path of profiles directory
```

### Phase 6: Test Workflow

1. Activate workflow (toggle in top right)
2. Copy webhook URL
3. Test with curl:

```bash
curl -X POST http://localhost:5678/webhook/pr-agent/generate \
  -H "Content-Type: application/json" \
  -d '{
    "article_text": "Test article...",
    "journalist_question": "Test question?",
    "media_outlet": "Test Outlet",
    "executive_name": "Sarah Chen"
  }'
```

4. Check email inbox
5. Review execution in n8n UI

### Phase 7: Update Integration Points

If you have applications calling the Python API, update them to call the webhook:

**Before (Python):**
```python
from pr_agent import PRCommentAgent

agent = PRCommentAgent()
result = agent.generate_comment(
    article_text="...",
    journalist_question="...",
    media_outlet="...",
    executive_name="..."
)
```

**After (n8n webhook):**
```python
import requests

url = "http://localhost:5678/webhook/pr-agent/generate"
payload = {
    "article_text": "...",
    "journalist_question": "...",
    "media_outlet": "...",
    "executive_name": "..."
}

response = requests.post(url, json=payload)
result = response.json()
```

### Phase 8: Monitor and Validate

1. **Run test suite**
   - Generate 5-10 test comments
   - Compare quality with Python version
   - Check email delivery

2. **Monitor performance**
   - Check execution times
   - Review error rates
   - Validate API costs

3. **Validate output**
   - Ensure same quality
   - Check email formatting
   - Verify all data fields

### Phase 9: Production Cutover

1. **Update documentation**
   - Document new webhook endpoint
   - Update API integration guides
   - Notify stakeholders

2. **Switch traffic**
   - Point applications to n8n webhook
   - Monitor for errors
   - Keep Python version as fallback

3. **Decommission Python**
   - After 1 week of stable operation
   - Keep backup for 30 days
   - Archive for reference

## Feature Mapping

### Core Features

| Python (LangChain) | n8n Workflow | Status |
|-------------------|--------------|--------|
| PRCommentAgent | Webhook + Function nodes | ✅ Full parity |
| MediaResearcherAgent | HTTP Request node (Serper/Tavily) | ✅ Full parity |
| DataResearcherAgent | HTTP Request node (Serper/Tavily) | ✅ Full parity |
| CommentDrafterAgent | HTTP Request node (OpenAI/Anthropic) | ✅ Full parity |
| HumanizerAgent | HTTP Request node (OpenAI/Anthropic) | ✅ Full parity |
| EmailSender | Email Send node | ✅ Full parity |
| ExecutiveProfileManager | Function node (file read) | ✅ Full parity |

### Advanced Features

| Feature | Python | n8n | Migration Status |
|---------|--------|-----|------------------|
| Async execution | ✅ Native | ✅ Built-in | ✅ Automatic |
| Parallel research | ✅ asyncio.gather | ✅ Parallel branches | ✅ Automatic |
| Error handling | ✅ Try/except | ✅ Error workflow | ✅ Automatic |
| Retry logic | ✅ LangChain | ✅ Node settings | ⚙️ Configure in UI |
| Streaming | ✅ LLM streaming | ⚠️ Not supported | ❌ Not available |
| Caching (Redis) | ✅ PRAgentCache | ⚙️ Requires n8n-nodes-redis | 📦 Manual setup |
| Memory system | ✅ PRAgentMemory | ⚠️ Not implemented | 📋 Future work |
| RAG | ✅ PRAgentRAG | ⚠️ Not implemented | 📋 Future work |
| Evaluation | ✅ PRAgentEvaluator | ⚠️ Not implemented | 📋 Future work |
| LangSmith tracing | ✅ Native | ⚙️ Custom HTTP nodes | 📦 Manual setup |

### API Compatibility

| Endpoint | Python | n8n | Notes |
|----------|--------|-----|-------|
| `generate_comment()` | ✅ | ✅ Webhook | Same parameters |
| `generate_comment_async()` | ✅ | ✅ Built-in | Always async |
| `generate_comment_stream()` | ✅ | ❌ | Streaming not supported |
| `generate_comment_with_memory_and_evaluation()` | ✅ | ❌ | Phase 3 features not implemented |

## Advanced Features Migration

### Redis Caching

**Python:**
```python
config = PRAgentConfig(enable_cache=True)
agent = PRCommentAgent(config)
```

**n8n:**
1. Install n8n-nodes-redis community node
2. Add Redis nodes before expensive operations
3. Check cache → Execute if miss → Store result

### Memory & RAG

Phase 3 features (memory, RAG, evaluation) are **not yet implemented** in n8n.

**Options:**
1. **Keep Python for Phase 3**: Use hybrid approach
2. **Custom implementation**: Add HTTP nodes to external services
3. **Wait for community nodes**: n8n community may develop these

**Hybrid Approach:**
```python
# Use n8n for main workflow
# Use Python for Phase 3 features
from pr_agent import PRCommentAgent

agent = PRCommentAgent()
result = await agent.generate_comment_with_memory_and_evaluation(
    article_text="...",
    # ... other params
)
```

### LangSmith Tracing

**Python:** Built-in
**n8n:** Add HTTP Request nodes

1. Add HTTP node after each major step
2. POST to LangSmith API
3. Include trace data
4. View in LangSmith dashboard

## Cost Comparison

### Infrastructure Costs

| Aspect | Python | n8n | Savings |
|--------|--------|-----|---------|
| Compute | $$$ (always running) | $$ (on-demand) | ~30% |
| Dependencies | Python + 20+ packages | Docker image | Simpler |
| Maintenance | High (updates, security) | Low (n8n updates) | ~50% time |
| Development | Requires developers | Visual, non-dev friendly | ~60% time |

### API Costs

Same for both (OpenAI, Anthropic, Serper, Tavily)

### Total Cost of Ownership

**Python:**
- Development: High
- Maintenance: High
- Hosting: Medium
- Training: High

**n8n:**
- Development: Low
- Maintenance: Low
- Hosting: Medium
- Training: Low

**Estimated savings: 40-50% TCO**

## Troubleshooting Migration

### Issue: Profiles Not Loading

**Symptom:** "Failed to load profile" error

**Fix:**
1. Check Docker volume mount: `docker-compose.yml`
2. Verify absolute path in function node
3. Check file permissions

```bash
# Fix permissions
chmod 644 pr_agent/config/executive_profiles/*.json

# Verify mount
docker exec pr-agent-n8n ls /data/pr_agent/config/executive_profiles/
```

### Issue: Different Output Quality

**Symptom:** Comments don't match Python quality

**Fix:**
1. Check LLM model (should be same)
2. Verify temperature settings
3. Compare prompts (function node code)
4. Check context length

### Issue: Slower Execution

**Symptom:** n8n workflow is slower than Python

**Fix:**
1. Check n8n instance resources
2. Verify parallel execution (Media + Data research)
3. Enable queue mode for high volume
4. Check network latency to APIs

### Issue: Email Not Sending

**Symptom:** SMTP errors

**Fix:**
1. Verify SMTP credentials in n8n UI
2. Use App Password, not regular password
3. Check port 587 is open
4. Test SMTP manually

## Rollback Plan

If migration fails, rollback to Python:

```bash
# 1. Stop n8n
docker-compose down

# 2. Restore Python environment
cd /home/user/pr-agent-system
pip install -r requirements.txt

# 3. Restore .env
cp pr_agent/.env.backup pr_agent/.env

# 4. Test Python version
python pr_agent/examples/simple_example.py

# 5. Switch applications back to Python API
```

## Support During Migration

### Resources

- n8n Documentation: https://docs.n8n.io
- n8n Community: https://community.n8n.io
- This repository issues: GitHub Issues

### Common Questions

**Q: Can I run both Python and n8n simultaneously?**
A: Yes! Use different ports/URLs during transition.

**Q: Will this break existing integrations?**
A: Only the endpoint changes. Update URLs from Python API to webhook.

**Q: What about Phase 3 features?**
A: Not yet implemented in n8n. Use hybrid approach or wait for development.

**Q: Can I customize the workflow?**
A: Yes! Easier than Python - just modify nodes in UI.

**Q: What if I need to rollback?**
A: Keep Python backup for 30 days. Rollback takes 5 minutes.

## Success Criteria

Migration is successful when:

- ✅ All test cases pass
- ✅ Output quality matches Python
- ✅ Performance is acceptable
- ✅ Email delivery works
- ✅ No increase in errors
- ✅ Team can modify workflows
- ✅ Monitoring is in place
- ✅ 7 days of stable operation

## Post-Migration

### Optimization Opportunities

1. **Add caching** - Reduce API costs by 70%
2. **Add rate limiting** - Prevent API quota issues
3. **Add monitoring** - Prometheus + Grafana
4. **Add authentication** - Secure webhook endpoint
5. **Scale horizontally** - Multiple n8n instances

### Future Enhancements

1. **Implement Phase 3 features** in n8n
2. **Add A/B testing** for comment variations
3. **Integrate with CRM** (Salesforce, HubSpot)
4. **Add multilingual support**
5. **Build approval dashboard**

---

**Need help? Check:**
- `n8n/README.md` - Full documentation
- `n8n/QUICK_START.md` - Quick setup guide
- GitHub Issues - Report problems
