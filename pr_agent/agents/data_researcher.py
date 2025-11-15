"""
Data researcher agent for finding supporting statistics and information.
"""

import asyncio
from typing import Dict, Any, List
from langchain_core.prompts import PromptTemplate
from ..tools.search import WebSearchTool
from ..prompts.templates import DATA_RESEARCH_PROMPT


class DataResearcherAgent:
    """Agent specialized in finding supporting data and statistics."""

    def __init__(self, llm: Any, search_tool: WebSearchTool):
        """
        Initialize data researcher agent.

        Args:
            llm: Language model instance
            search_tool: Web search tool
        """
        self.llm = llm
        self.search_tool = search_tool
        self.prompt_template = PromptTemplate(
            input_variables=["topic", "context", "executive_perspective"],
            template=DATA_RESEARCH_PROMPT
        )

    def research_supporting_data(
        self,
        topic: str,
        context: str,
        executive_perspective: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Research supporting data for a PR comment.

        Args:
            topic: Main topic to research
            context: Context from the article and question
            executive_perspective: Executive's typical perspective

        Returns:
            List of relevant data points with sources
        """
        # Generate search queries
        search_queries = self._generate_search_queries(topic, context)

        # Perform searches
        all_results = []
        for query in search_queries[:3]:  # Limit to 3 queries
            results = self.search_tool.search_for_data(query)
            all_results.extend(results)

        # Use LLM to analyze and select best data points
        results_text = "\n".join([
            f"- {r['title']}: {r['snippet']} (Source: {r['link']})"
            for r in all_results[:10]  # Top 10 results
        ])

        prompt = self.prompt_template.format(
            topic=topic,
            context=context,
            executive_perspective=executive_perspective
        )

        analysis = self.llm.invoke(f"{prompt}\n\nAvailable Data:\n{results_text}")

        return {
            "raw_results": all_results,
            "curated_data": analysis.content if hasattr(analysis, 'content') else str(analysis),
            "search_queries": search_queries
        }

    def _generate_search_queries(self, topic: str, context: str) -> List[str]:
        """
        Generate effective search queries.

        Args:
            topic: Main topic
            context: Additional context

        Returns:
            List of search queries
        """
        # Use LLM to generate targeted search queries
        query_prompt = f"""Generate 3 specific search queries to find data and statistics about:

Topic: {topic}
Context: {context}

Format: Return only the search queries, one per line.
"""

        response = self.llm.invoke(query_prompt)
        queries_text = response.content if hasattr(response, 'content') else str(response)

        # Parse queries
        queries = [q.strip() for q in queries_text.split('\n') if q.strip() and not q.strip().startswith('#')]

        return queries[:3] or [topic]  # Fallback to topic if parsing fails

    async def research_supporting_data_async(
        self,
        topic: str,
        context: str,
        executive_perspective: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Async version: Research supporting data for a PR comment.

        Args:
            topic: Main topic to research
            context: Context from the article and question
            executive_perspective: Executive's typical perspective

        Returns:
            List of relevant data points with sources

        Example:
            >>> agent = DataResearcherAgent(llm, search_tool)
            >>> data = await agent.research_supporting_data_async("AI safety", "...")
        """
        # Generate search queries
        search_queries = await self._generate_search_queries_async(topic, context)

        # Perform searches in parallel
        search_tasks = [
            self.search_tool.search_for_data_async(query)
            for query in search_queries[:3]  # Limit to 3 queries
        ]
        search_results = await asyncio.gather(*search_tasks, return_exceptions=True)

        # Flatten results and filter out exceptions
        all_results = []
        for results in search_results:
            if not isinstance(results, Exception):
                all_results.extend(results)

        # Use LLM to analyze and select best data points
        results_text = "\n".join([
            f"- {r['title']}: {r['snippet']} (Source: {r['link']})"
            for r in all_results[:10]  # Top 10 results
        ])

        prompt = self.prompt_template.format(
            topic=topic,
            context=context,
            executive_perspective=executive_perspective
        )

        analysis = await self.llm.ainvoke(f"{prompt}\n\nAvailable Data:\n{results_text}")

        return {
            "raw_results": all_results,
            "curated_data": analysis.content if hasattr(analysis, 'content') else str(analysis),
            "search_queries": search_queries
        }

    async def _generate_search_queries_async(self, topic: str, context: str) -> List[str]:
        """
        Async version: Generate effective search queries.

        Args:
            topic: Main topic
            context: Additional context

        Returns:
            List of search queries
        """
        # Use LLM to generate targeted search queries
        query_prompt = f"""Generate 3 specific search queries to find data and statistics about:

Topic: {topic}
Context: {context}

Format: Return only the search queries, one per line.
"""

        response = await self.llm.ainvoke(query_prompt)
        queries_text = response.content if hasattr(response, 'content') else str(response)

        # Parse queries
        queries = [q.strip() for q in queries_text.split('\n') if q.strip() and not q.strip().startswith('#')]

        return queries[:3] or [topic]  # Fallback to topic if parsing fails
