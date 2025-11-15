"""
Retrieval-Augmented Generation (RAG) system for PR Agent.

Provides vector-based retrieval of:
- Historical successful comments
- Media outlet knowledge base
- Industry talking points
- Example responses for few-shot learning
"""

import os
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

from langchain_voyageai import VoyageAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from .config import PRAgentConfig
from .logging_config import get_logger

logger = get_logger(__name__)


class PRAgentRAG:
    """
    RAG system for PR Agent with multiple specialized vector stores.

    Stores:
    - Comment history: Past successful comments
    - Media knowledge: Information about media outlets and journalists
    - Examples: High-quality example responses for few-shot learning
    - Talking points: Industry insights and messaging
    """

    def __init__(self, config: PRAgentConfig):
        """
        Initialize RAG system.

        Args:
            config: PR Agent configuration
        """
        self.config = config
        self.enabled = config.enable_rag

        if not self.enabled:
            logger.info("rag_disabled", reason="enable_rag=False")
            return

        # Validate VoyageAI API key
        if not config.voyage_api_key:
            logger.warning(
                "rag_initialization_failed",
                reason="VOYAGE_API_KEY not set",
                fallback="rag_disabled"
            )
            self.enabled = False
            return

        try:
            # Initialize embeddings
            self.embeddings = VoyageAIEmbeddings(
                model="voyage-3-large",
                voyage_api_key=config.voyage_api_key
            )

            # Initialize text splitter for chunking
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=config.rag_chunk_size,
                chunk_overlap=config.rag_chunk_overlap,
                separators=["\n\n", "\n", ". ", " ", ""]
            )

            # Ensure RAG directory exists
            self._ensure_rag_directory()

            # Initialize vector stores
            self._initialize_vector_stores()

            logger.info(
                "rag_initialized",
                vector_store_path=config.rag_vector_store_path,
                chunk_size=config.rag_chunk_size,
                top_k=config.rag_top_k
            )

        except Exception as e:
            logger.error(
                "rag_initialization_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            self.enabled = False
            raise

    def _ensure_rag_directory(self):
        """Create RAG directory structure."""
        base_path = Path(self.config.rag_vector_store_path)
        base_path.mkdir(parents=True, exist_ok=True)

        # Create subdirectories for each vector store
        for subdir in ["comments", "media", "examples", "talking_points"]:
            (base_path / subdir).mkdir(exist_ok=True)

    def _initialize_vector_stores(self):
        """Initialize specialized vector stores."""
        base_path = self.config.rag_vector_store_path

        # 1. Comment History Store
        self.comment_store = Chroma(
            collection_name="comment_history",
            embedding_function=self.embeddings,
            persist_directory=f"{base_path}/comments"
        )

        # 2. Media Knowledge Store
        self.media_store = Chroma(
            collection_name="media_knowledge",
            embedding_function=self.embeddings,
            persist_directory=f"{base_path}/media"
        )

        # 3. Examples Store (high-quality examples for few-shot)
        self.examples_store = Chroma(
            collection_name="examples",
            embedding_function=self.embeddings,
            persist_directory=f"{base_path}/examples"
        )

        # 4. Talking Points Store (industry insights)
        self.talking_points_store = Chroma(
            collection_name="talking_points",
            embedding_function=self.embeddings,
            persist_directory=f"{base_path}/talking_points"
        )

        logger.info("vector_stores_initialized", store_count=4)

    async def store_comment(
        self,
        executive_name: str,
        media_outlet: str,
        journalist_question: str,
        comment: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Store successful comment in RAG system.

        Args:
            executive_name: Executive name
            media_outlet: Media outlet
            journalist_question: Question asked
            comment: Generated comment
            metadata: Additional metadata
        """
        if not self.enabled:
            return

        try:
            # Build metadata
            doc_metadata = {
                "executive_name": executive_name,
                "media_outlet": media_outlet,
                "question": journalist_question,
                "timestamp": datetime.now().isoformat(),
                "comment_length": len(comment),
                "type": "comment"
            }

            if metadata:
                doc_metadata.update(metadata)

            # Create document
            doc_text = f"Question: {journalist_question}\n\nComment: {comment}"

            document = Document(
                page_content=doc_text,
                metadata=doc_metadata
            )

            # Add to comment store
            await self.comment_store.aadd_documents([document])

            logger.info(
                "comment_stored",
                executive=executive_name,
                media_outlet=media_outlet,
                comment_length=len(comment)
            )

        except Exception as e:
            logger.error(
                "comment_storage_failed",
                executive=executive_name,
                error=str(e),
                error_type=type(e).__name__
            )

    async def find_similar_comments(
        self,
        question: str,
        executive_name: Optional[str] = None,
        media_outlet: Optional[str] = None,
        k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Find similar past comments.

        Args:
            question: Current question
            executive_name: Filter by executive (optional)
            media_outlet: Filter by media outlet (optional)
            k: Number of results (uses config default if not provided)

        Returns:
            List of similar comments with metadata
        """
        if not self.enabled:
            return []

        k = k or self.config.rag_top_k

        try:
            # Build filter
            metadata_filter = {}
            if executive_name:
                metadata_filter["executive_name"] = executive_name
            if media_outlet:
                metadata_filter["media_outlet"] = media_outlet

            # Search
            if metadata_filter:
                results = await self.comment_store.asimilarity_search(
                    question,
                    k=k,
                    filter=metadata_filter
                )
            else:
                results = await self.comment_store.asimilarity_search(
                    question,
                    k=k
                )

            # Format results
            similar_comments = []
            for doc in results:
                # Extract question and comment from page_content
                parts = doc.page_content.split("Comment: ", 1)
                extracted_question = parts[0].replace("Question: ", "").strip()
                extracted_comment = parts[1].strip() if len(parts) > 1 else ""

                similar_comments.append({
                    "question": extracted_question,
                    "comment": extracted_comment,
                    "executive": doc.metadata.get("executive_name", ""),
                    "media_outlet": doc.metadata.get("media_outlet", ""),
                    "timestamp": doc.metadata.get("timestamp", ""),
                    "metadata": doc.metadata
                })

            logger.info(
                "similar_comments_found",
                question_length=len(question),
                results_count=len(similar_comments),
                executive_filter=executive_name,
                media_filter=media_outlet
            )

            return similar_comments

        except Exception as e:
            logger.error(
                "similar_comments_search_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            return []

    async def store_media_knowledge(
        self,
        media_outlet: str,
        journalist_name: Optional[str],
        knowledge: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Store media outlet/journalist knowledge.

        Args:
            media_outlet: Media outlet name
            journalist_name: Journalist name (optional)
            knowledge: Knowledge text
            metadata: Additional metadata
        """
        if not self.enabled:
            return

        try:
            doc_metadata = {
                "media_outlet": media_outlet,
                "journalist_name": journalist_name or "unknown",
                "timestamp": datetime.now().isoformat(),
                "type": "media_knowledge"
            }

            if metadata:
                doc_metadata.update(metadata)

            # Chunk if necessary
            chunks = self.text_splitter.split_text(knowledge)

            documents = [
                Document(page_content=chunk, metadata=doc_metadata)
                for chunk in chunks
            ]

            await self.media_store.aadd_documents(documents)

            logger.info(
                "media_knowledge_stored",
                media_outlet=media_outlet,
                journalist=journalist_name,
                chunks_count=len(documents)
            )

        except Exception as e:
            logger.error(
                "media_knowledge_storage_failed",
                media_outlet=media_outlet,
                error=str(e),
                error_type=type(e).__name__
            )

    async def retrieve_media_knowledge(
        self,
        media_outlet: str,
        journalist_name: Optional[str] = None,
        k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve knowledge about media outlet/journalist.

        Args:
            media_outlet: Media outlet name
            journalist_name: Journalist name (optional)
            k: Number of results

        Returns:
            List of relevant knowledge chunks
        """
        if not self.enabled:
            return []

        k = k or self.config.rag_top_k

        try:
            # Build query
            query = f"{media_outlet}"
            if journalist_name:
                query += f" {journalist_name}"

            # Build filter
            metadata_filter = {"media_outlet": media_outlet}
            if journalist_name:
                metadata_filter["journalist_name"] = journalist_name

            # Search
            results = await self.media_store.asimilarity_search(
                query,
                k=k,
                filter=metadata_filter
            )

            knowledge = [
                {
                    "content": doc.page_content,
                    "media_outlet": doc.metadata.get("media_outlet", ""),
                    "journalist": doc.metadata.get("journalist_name", ""),
                    "metadata": doc.metadata
                }
                for doc in results
            ]

            logger.info(
                "media_knowledge_retrieved",
                media_outlet=media_outlet,
                journalist=journalist_name,
                results_count=len(knowledge)
            )

            return knowledge

        except Exception as e:
            logger.error(
                "media_knowledge_retrieval_failed",
                media_outlet=media_outlet,
                error=str(e),
                error_type=type(e).__name__
            )
            return []

    async def store_example(
        self,
        example_text: str,
        category: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Store high-quality example for few-shot learning.

        Args:
            example_text: Example text
            category: Example category (e.g., "product_launch", "crisis_response")
            metadata: Additional metadata
        """
        if not self.enabled:
            return

        try:
            doc_metadata = {
                "category": category,
                "timestamp": datetime.now().isoformat(),
                "type": "example"
            }

            if metadata:
                doc_metadata.update(metadata)

            document = Document(
                page_content=example_text,
                metadata=doc_metadata
            )

            await self.examples_store.aadd_documents([document])

            logger.info(
                "example_stored",
                category=category,
                example_length=len(example_text)
            )

        except Exception as e:
            logger.error(
                "example_storage_failed",
                category=category,
                error=str(e),
                error_type=type(e).__name__
            )

    async def retrieve_examples(
        self,
        query: str,
        category: Optional[str] = None,
        k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant examples for few-shot learning.

        Args:
            query: Query text
            category: Filter by category (optional)
            k: Number of results

        Returns:
            List of relevant examples
        """
        if not self.enabled:
            return []

        k = k or self.config.rag_top_k

        try:
            # Search with optional category filter
            if category:
                results = await self.examples_store.asimilarity_search(
                    query,
                    k=k,
                    filter={"category": category}
                )
            else:
                results = await self.examples_store.asimilarity_search(
                    query,
                    k=k
                )

            examples = [
                {
                    "content": doc.page_content,
                    "category": doc.metadata.get("category", ""),
                    "metadata": doc.metadata
                }
                for doc in results
            ]

            logger.info(
                "examples_retrieved",
                query_length=len(query),
                category_filter=category,
                results_count=len(examples)
            )

            return examples

        except Exception as e:
            logger.error(
                "examples_retrieval_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            return []

    async def augment_with_context(
        self,
        journalist_question: str,
        executive_name: str,
        media_outlet: str,
        journalist_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Augment context with relevant information from RAG.

        Args:
            journalist_question: Question asked
            executive_name: Executive name
            media_outlet: Media outlet
            journalist_name: Journalist name (optional)

        Returns:
            Dictionary with augmented context
        """
        if not self.enabled:
            return {"enabled": False}

        try:
            logger.info(
                "augmenting_context",
                executive=executive_name,
                media_outlet=media_outlet
            )

            # Run retrieval in parallel (conceptually - using sequential awaits)
            similar_comments = await self.find_similar_comments(
                journalist_question,
                executive_name=executive_name,
                k=3
            )

            media_knowledge = await self.retrieve_media_knowledge(
                media_outlet,
                journalist_name=journalist_name,
                k=2
            )

            examples = await self.retrieve_examples(
                journalist_question,
                k=2
            )

            augmented_context = {
                "enabled": True,
                "similar_comments": similar_comments,
                "media_knowledge": media_knowledge,
                "examples": examples,
                "retrieval_counts": {
                    "similar_comments": len(similar_comments),
                    "media_knowledge": len(media_knowledge),
                    "examples": len(examples)
                }
            }

            logger.info(
                "context_augmented",
                similar_comments=len(similar_comments),
                media_knowledge=len(media_knowledge),
                examples=len(examples)
            )

            return augmented_context

        except Exception as e:
            logger.error(
                "context_augmentation_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            return {"enabled": True, "error": str(e)}

    def get_rag_stats(self) -> Dict[str, Any]:
        """
        Get RAG system statistics.

        Returns:
            Dictionary with RAG stats
        """
        if not self.enabled:
            return {"enabled": False}

        try:
            # Count documents in each store
            comment_count = self.comment_store._collection.count()
            media_count = self.media_store._collection.count()
            examples_count = self.examples_store._collection.count()
            talking_points_count = self.talking_points_store._collection.count()

            stats = {
                "enabled": True,
                "vector_stores": {
                    "comments": comment_count,
                    "media": media_count,
                    "examples": examples_count,
                    "talking_points": talking_points_count
                },
                "total_documents": (
                    comment_count + media_count +
                    examples_count + talking_points_count
                ),
                "config": {
                    "chunk_size": self.config.rag_chunk_size,
                    "chunk_overlap": self.config.rag_chunk_overlap,
                    "top_k": self.config.rag_top_k
                }
            }

            logger.info("rag_stats_retrieved", **stats["vector_stores"])

            return stats

        except Exception as e:
            logger.error(
                "rag_stats_retrieval_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            return {"enabled": True, "error": str(e)}
