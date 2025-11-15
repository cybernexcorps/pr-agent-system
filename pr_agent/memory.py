"""
Memory management for PR Agent.

Provides short-term conversation memory and long-term semantic memory
for retrieving relevant past comments and maintaining conversation context.
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from langchain.memory import ConversationTokenBufferMemory
from langchain_core.messages import HumanMessage, AIMessage
from langchain_voyageai import VoyageAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from .config import PRAgentConfig
from .logging_config import get_logger

logger = get_logger(__name__)


class PRAgentMemory:
    """
    Memory system for PR Agent with short-term and long-term memory.

    Features:
    - Short-term: Token-based conversation buffer for recent context
    - Long-term: Vector-based semantic search for past comments
    - Session management: Track conversations by session ID
    - Persistence: Save/load memory state
    """

    def __init__(self, config: PRAgentConfig, llm):
        """
        Initialize memory system.

        Args:
            config: PR Agent configuration
            llm: Language model for token counting
        """
        self.config = config
        self.llm = llm
        self.enabled = config.enable_memory

        if not self.enabled:
            logger.info("memory_disabled", reason="enable_memory=False")
            return

        # Validate VoyageAI API key
        if not config.voyage_api_key:
            logger.warning(
                "memory_initialization_failed",
                reason="VOYAGE_API_KEY not set",
                fallback="memory_disabled"
            )
            self.enabled = False
            return

        try:
            # Initialize short-term memory (conversation buffer)
            self.short_term_sessions: Dict[str, ConversationTokenBufferMemory] = {}

            # Initialize embeddings for long-term memory
            self.embeddings = VoyageAIEmbeddings(
                model="voyage-3-large",
                voyage_api_key=config.voyage_api_key
            )

            # Initialize vector store for long-term memory
            self._ensure_memory_directory()

            self.vector_store = Chroma(
                collection_name="pr_agent_comments",
                embedding_function=self.embeddings,
                persist_directory=config.memory_vector_store_path
            )

            logger.info(
                "memory_initialized",
                short_term_max_tokens=config.memory_max_tokens,
                vector_store_path=config.memory_vector_store_path
            )

        except Exception as e:
            logger.error(
                "memory_initialization_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            self.enabled = False
            raise

    def _ensure_memory_directory(self):
        """Create memory directory if it doesn't exist."""
        Path(self.config.memory_vector_store_path).mkdir(parents=True, exist_ok=True)

    def get_short_term_memory(self, session_id: str) -> ConversationTokenBufferMemory:
        """
        Get or create short-term memory for a session.

        Args:
            session_id: Session identifier

        Returns:
            Conversation memory for the session
        """
        if not self.enabled:
            return None

        if session_id not in self.short_term_sessions:
            self.short_term_sessions[session_id] = ConversationTokenBufferMemory(
                llm=self.llm,
                max_token_limit=self.config.memory_max_tokens,
                return_messages=True,
                memory_key="conversation_history"
            )
            logger.info("session_created", session_id=session_id)

        return self.short_term_sessions[session_id]

    async def save_to_short_term(
        self,
        session_id: str,
        question: str,
        comment: str
    ) -> None:
        """
        Save interaction to short-term memory.

        Args:
            session_id: Session identifier
            question: Journalist question
            comment: Generated comment
        """
        if not self.enabled:
            return

        try:
            memory = self.get_short_term_memory(session_id)

            await memory.asave_context(
                {"input": question},
                {"output": comment}
            )

            logger.info(
                "short_term_memory_saved",
                session_id=session_id,
                question_length=len(question),
                comment_length=len(comment)
            )

        except Exception as e:
            logger.error(
                "short_term_memory_save_failed",
                session_id=session_id,
                error=str(e),
                error_type=type(e).__name__
            )

    async def save_to_long_term(
        self,
        executive_name: str,
        media_outlet: str,
        journalist_question: str,
        comment: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Save successful comment to long-term memory (vector store).

        Args:
            executive_name: Executive name
            media_outlet: Media outlet name
            journalist_question: Question asked
            comment: Generated comment
            metadata: Additional metadata to store
        """
        if not self.enabled:
            return

        try:
            # Create document with rich metadata
            doc_metadata = {
                "executive_name": executive_name,
                "media_outlet": media_outlet,
                "question": journalist_question,
                "timestamp": datetime.now().isoformat(),
                "comment_length": len(comment)
            }

            if metadata:
                doc_metadata.update(metadata)

            # Create document combining question and comment
            doc_text = f"Question: {journalist_question}\n\nComment: {comment}"

            document = Document(
                page_content=doc_text,
                metadata=doc_metadata
            )

            # Add to vector store
            await self.vector_store.aadd_documents([document])

            logger.info(
                "long_term_memory_saved",
                executive=executive_name,
                media_outlet=media_outlet,
                question_length=len(journalist_question),
                comment_length=len(comment)
            )

        except Exception as e:
            logger.error(
                "long_term_memory_save_failed",
                executive=executive_name,
                error=str(e),
                error_type=type(e).__name__
            )

    async def retrieve_similar_comments(
        self,
        question: str,
        executive_name: Optional[str] = None,
        media_outlet: Optional[str] = None,
        k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Retrieve similar past comments from long-term memory.

        Args:
            question: Current journalist question
            executive_name: Filter by executive name (optional)
            media_outlet: Filter by media outlet (optional)
            k: Number of results to retrieve

        Returns:
            List of similar past comments with metadata
        """
        if not self.enabled:
            return []

        try:
            # Build filter for metadata search
            metadata_filter = {}
            if executive_name:
                metadata_filter["executive_name"] = executive_name
            if media_outlet:
                metadata_filter["media_outlet"] = media_outlet

            # Search vector store
            if metadata_filter:
                results = await self.vector_store.asimilarity_search(
                    question,
                    k=k,
                    filter=metadata_filter
                )
            else:
                results = await self.vector_store.asimilarity_search(
                    question,
                    k=k
                )

            # Format results
            similar_comments = []
            for doc in results:
                similar_comments.append({
                    "question": doc.metadata.get("question", ""),
                    "comment": doc.page_content.split("Comment: ")[-1],
                    "executive": doc.metadata.get("executive_name", ""),
                    "media_outlet": doc.metadata.get("media_outlet", ""),
                    "timestamp": doc.metadata.get("timestamp", ""),
                    "comment_length": doc.metadata.get("comment_length", 0)
                })

            logger.info(
                "similar_comments_retrieved",
                question_length=len(question),
                results_count=len(similar_comments),
                executive_filter=executive_name,
                media_filter=media_outlet
            )

            return similar_comments

        except Exception as e:
            logger.error(
                "similar_comments_retrieval_failed",
                question=question[:100],
                error=str(e),
                error_type=type(e).__name__
            )
            return []

    def get_conversation_history(self, session_id: str) -> List[Dict[str, str]]:
        """
        Get conversation history for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of conversation messages
        """
        if not self.enabled:
            return []

        try:
            memory = self.get_short_term_memory(session_id)

            # Load memory variables
            memory_vars = memory.load_memory_variables({})
            messages = memory_vars.get("conversation_history", [])

            # Convert to simple dict format
            history = []
            for msg in messages:
                if isinstance(msg, HumanMessage):
                    history.append({"role": "human", "content": msg.content})
                elif isinstance(msg, AIMessage):
                    history.append({"role": "ai", "content": msg.content})

            logger.info(
                "conversation_history_retrieved",
                session_id=session_id,
                message_count=len(history)
            )

            return history

        except Exception as e:
            logger.error(
                "conversation_history_retrieval_failed",
                session_id=session_id,
                error=str(e),
                error_type=type(e).__name__
            )
            return []

    def clear_session(self, session_id: str) -> None:
        """
        Clear short-term memory for a session.

        Args:
            session_id: Session identifier
        """
        if not self.enabled:
            return

        if session_id in self.short_term_sessions:
            del self.short_term_sessions[session_id]
            logger.info("session_cleared", session_id=session_id)

    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get memory system statistics.

        Returns:
            Dictionary with memory stats
        """
        if not self.enabled:
            return {"enabled": False}

        try:
            # Count documents in vector store
            collection = self.vector_store._collection
            doc_count = collection.count()

            stats = {
                "enabled": True,
                "active_sessions": len(self.short_term_sessions),
                "long_term_documents": doc_count,
                "vector_store_path": self.config.memory_vector_store_path,
                "max_tokens_per_session": self.config.memory_max_tokens
            }

            logger.info("memory_stats_retrieved", **stats)

            return stats

        except Exception as e:
            logger.error(
                "memory_stats_retrieval_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            return {"enabled": True, "error": str(e)}
