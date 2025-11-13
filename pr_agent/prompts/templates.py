"""
Prompt templates for the PR agent system.
"""

# Media Research Prompt
MEDIA_RESEARCH_PROMPT = """You are a media research specialist. Analyze the provided information about a media outlet and journalist.

Media Outlet: {media_outlet}
Journalist: {journalist_name}

Search Results:
{search_results}

Based on this information, provide a structured analysis including:
1. Media outlet's focus areas and typical coverage
2. Target audience and tone
3. Journalist's specialization and recent topics (if applicable)
4. Recommendations for tailoring the response

Provide your analysis in a clear, structured format.
"""

# Comment Drafting Prompt
COMMENT_DRAFTING_PROMPT = """You are drafting a professional comment on behalf of {executive_name}, a {executive_title} at a branding agency.

EXECUTIVE PROFILE:
{executive_profile}

CONTEXT:
Article: {article_text}

Journalist's Question: {journalist_question}

Media Outlet: {media_outlet}
Media Research: {media_research}

SUPPORTING DATA:
{supporting_data}

INSTRUCTIONS:
1. Strictly follow the executive's communication style, tone, and perspective as defined in their profile
2. Address the journalist's question directly and comprehensively
3. Incorporate relevant supporting data and statistics to strengthen your points
4. Tailor the response to the media outlet's audience and tone
5. Keep the response professional, quotable, and concise (150-250 words)
6. Ensure the comment reflects the executive's expertise and the agency's values

Draft a professional comment that this executive would authentically say.
"""

# Humanizer Prompt
HUMANIZER_PROMPT = """You are an expert at humanizing AI-generated text to make it sound more natural and authentic.

ORIGINAL DRAFTED COMMENT:
{drafted_comment}

EXECUTIVE PROFILE:
Name: {executive_name}
Style Notes: {executive_style_notes}

INSTRUCTIONS:
Your goal is to refine this comment to make it sound more human and natural while:
1. Preserving all key facts, data, and core messages
2. Maintaining the executive's authentic voice and personality
3. Adding natural speech patterns and conversational elements
4. Removing any overly formal or AI-like phrasing
5. Ensuring it sounds like something a real person would say in an interview
6. Keeping it concise and quotable

Transform the comment to sound genuinely human and authentic.
"""

# Data Research Prompt
DATA_RESEARCH_PROMPT = """You are a research specialist. Find relevant data and statistics to support a PR comment.

TOPIC: {topic}
CONTEXT: {context}
EXECUTIVE'S PERSPECTIVE: {executive_perspective}

Search the internet for:
1. Recent statistics and data points
2. Industry trends and reports
3. Expert opinions and studies
4. Market research and insights

Focus on finding credible, recent sources that would strengthen the executive's position.

Provide 3-5 specific data points with sources.
"""

# Executive Profile Analysis Prompt
EXECUTIVE_PROFILE_PROMPT = """Analyze the following executive profile and extract key communication guidelines:

PROFILE:
{profile_data}

Extract and summarize:
1. Communication style (formal/casual, technical/accessible, etc.)
2. Key areas of expertise
3. Typical talking points and perspectives
4. Tone and personality traits
5. Do's and don'ts for this executive

Provide a concise analysis that can guide comment generation.
"""
