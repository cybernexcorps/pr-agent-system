# Executive Profile Examples

This directory contains example executive profile JSON files for the PR Agent System n8n workflow.

## What Are Executive Profiles?

Executive profiles define the communication style, expertise, and personality of executives for whom the system generates PR comments. Each profile ensures consistent voice and messaging across all media interactions.

## Profile Structure

```json
{
  "name": "Executive Name",
  "title": "Chief Brand Officer",
  "company": "Company Name",
  "expertise": ["Area 1", "Area 2", "Area 3"],
  "communication_style": "Professional yet approachable, data-driven",
  "tone": "Confident, insightful, forward-thinking",
  "personality_traits": ["Analytical", "Strategic", "Articulate"],
  "talking_points": [
    "Key message 1",
    "Key message 2"
  ],
  "values": ["Value 1", "Value 2"],
  "speaking_patterns": "Uses concrete examples, references data",
  "do_not_say": ["Phrase to avoid", "Another phrase to avoid"],
  "preferred_structure": "Hook -> Evidence -> Insight -> Action"
}
```

## Required Fields

- `name` - Executive's full name
- `title` - Executive's job title
- `communication_style` - Overall communication approach
- `expertise` - Array of expertise areas

## How to Use in n8n Cloud

Since n8n Cloud doesn't have access to local files, you have several options:

### Option 1: Inline Profiles (Quick Start)

Copy the profile JSON and paste it directly into the "Load Executive Profile" function node:

```javascript
const profiles = {
  "sarah_chen": {
    "name": "Sarah Chen",
    "title": "Chief Brand Officer",
    // ... rest of profile from sarah_chen.json
  }
};
```

### Option 2: GitHub (Recommended for Production)

1. Upload profiles to a GitHub repository
2. Make the repo public or use a token
3. Replace the function node with HTTP Request node:
   ```
   https://raw.githubusercontent.com/your-org/profiles/main/sarah_chen.json
   ```

### Option 3: Cloud Storage (S3, Google Cloud Storage)

1. Upload profiles to cloud storage
2. Make them publicly accessible or use presigned URLs
3. Fetch via HTTP Request node

### Option 4: API Endpoint

Create a simple serverless function (Vercel, Netlify, Cloudflare Workers) that serves profiles.

## Example Profile

See `sarah_chen.json` for a complete example profile.

## Creating New Profiles

1. Copy `sarah_chen.json` as a template
2. Customize all fields for the new executive
3. Test thoroughly with sample questions
4. Deploy using one of the methods above

## File Naming Convention

While n8n Cloud doesn't require specific filenames, if hosting externally:
- Use lowercase
- Replace spaces with underscores
- Use `.json` extension
- Example: `john_doe.json` for John Doe

## Tips for Good Profiles

- **Be specific**: Vague descriptions lead to generic comments
- **Include examples**: Reference actual speaking patterns and phrases
- **Define boundaries**: Use `do_not_say` to avoid unwanted phrases
- **Test extensively**: Generate multiple comments to validate consistency
- **Update regularly**: Keep profiles current with executive's evolving expertise

## Support

For questions about profile structure or best practices, see the main documentation:
- `n8n/QUICK_START.md` - Quick setup guide
- `n8n/CLOUD_SETUP.md` - Cloud deployment guide
- `n8n/README.md` - Complete n8n documentation
