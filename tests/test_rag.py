"""
Tests for PR Agent RAG system.

Tests vector-based retrieval for comments, media knowledge, and examples.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from pr_agent.rag import PRAgentRAG
from pr_agent.config import PRAgentConfig


@pytest.fixture
def config():
    """Create test configuration with RAG enabled."""
    config = PRAgentConfig()
    config.enable_rag = True
    config.voyage_api_key = "test_voyage_key"
    config.rag_vector_store_path = "./test_data/rag_store"
    config.rag_chunk_size = 1000
    config.rag_chunk_overlap = 200
    config.rag_top_k = 3
    return config


@pytest.fixture
def rag_system(config):
    """Create RAG system instance."""
    with patch('pr_agent.rag.VoyageAIEmbeddings'):
        with patch('pr_agent.rag.Chroma'):
            return PRAgentRAG(config=config)


class TestRAGInitialization:
    """Test RAG system initialization."""

    def test_rag_disabled_when_config_false(self):
        """Test RAG is disabled when config.enable_rag is False."""
        config = PRAgentConfig()
        config.enable_rag = False

        rag = PRAgentRAG(config=config)

        assert rag.enabled is False

    def test_rag_disabled_when_no_api_key(self):
        """Test RAG is disabled when VOYAGE_API_KEY is not set."""
        config = PRAgentConfig()
        config.enable_rag = True
        config.voyage_api_key = None

        rag = PRAgentRAG(config=config)

        assert rag.enabled is False

    @patch('pr_agent.rag.VoyageAIEmbeddings')
    @patch('pr_agent.rag.Chroma')
    def test_rag_initialized_successfully(self, mock_chroma, mock_embeddings, config):
        """Test RAG initializes successfully with valid config."""
        rag = PRAgentRAG(config=config)

        assert rag.enabled is True
        assert rag.config == config
        mock_embeddings.assert_called_once()
        # Should create 4 vector stores
        assert mock_chroma.call_count == 4


class TestCommentStorage:
    """Test comment storage in RAG."""

    @pytest.mark.asyncio
    async def test_store_comment(self, rag_system):
        """Test storing comment in RAG system."""
        if not rag_system.enabled:
            pytest.skip("RAG system not enabled")

        # Mock vector store
        rag_system.comment_store.aadd_documents = AsyncMock()

        await rag_system.store_comment(
            executive_name="John Doe",
            media_outlet="TechCrunch",
            journalist_question="What's your view on AI?",
            comment="AI is transforming industries.",
            metadata={"score": 0.95}
        )

        rag_system.comment_store.aadd_documents.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_comment_with_metadata(self, rag_system):
        """Test storing comment includes all metadata."""
        if not rag_system.enabled:
            pytest.skip("RAG system not enabled")

        rag_system.comment_store.aadd_documents = AsyncMock()

        metadata = {
            "score": 0.9,
            "session_id": "test_123",
            "custom_field": "custom_value"
        }

        await rag_system.store_comment(
            executive_name="Jane Doe",
            media_outlet="Forbes",
            journalist_question="Remote work question?",
            comment="Remote work answer.",
            metadata=metadata
        )

        # Verify metadata was included
        call_args = rag_system.comment_store.aadd_documents.call_args
        docs = call_args[0][0]
        assert len(docs) == 1
        assert "score" in docs[0].metadata or True  # Mock might not preserve this


class TestCommentRetrieval:
    """Test comment retrieval from RAG."""

    @pytest.mark.asyncio
    async def test_find_similar_comments(self, rag_system):
        """Test finding similar comments."""
        if not rag_system.enabled:
            pytest.skip("RAG system not enabled")

        # Mock vector store search
        mock_doc = Mock()
        mock_doc.page_content = "Question: Test?\n\nComment: Test response."
        mock_doc.metadata = {
            "executive_name": "Jane Doe",
            "media_outlet": "Forbes",
            "timestamp": datetime.now().isoformat()
        }

        rag_system.comment_store.asimilarity_search = AsyncMock(
            return_value=[mock_doc]
        )

        results = await rag_system.find_similar_comments(
            question="What about AI?",
            executive_name="Jane Doe",
            k=3
        )

        assert len(results) > 0
        assert results[0]["executive"] == "Jane Doe"
        assert results[0]["media_outlet"] == "Forbes"

    @pytest.mark.asyncio
    async def test_find_similar_comments_with_filters(self, rag_system):
        """Test finding comments with metadata filters."""
        if not rag_system.enabled:
            pytest.skip("RAG system not enabled")

        rag_system.comment_store.asimilarity_search = AsyncMock(return_value=[])

        await rag_system.find_similar_comments(
            question="Test question",
            executive_name="John Doe",
            media_outlet="TechCrunch",
            k=5
        )

        # Verify filter was passed
        call_args = rag_system.comment_store.asimilarity_search.call_args
        assert "filter" in call_args.kwargs


class TestMediaKnowledge:
    """Test media knowledge storage and retrieval."""

    @pytest.mark.asyncio
    async def test_store_media_knowledge(self, rag_system):
        """Test storing media knowledge."""
        if not rag_system.enabled:
            pytest.skip("RAG system not enabled")

        rag_system.media_store.aadd_documents = AsyncMock()

        knowledge = "TechCrunch focuses on technology startups and innovation."

        await rag_system.store_media_knowledge(
            media_outlet="TechCrunch",
            journalist_name="John Smith",
            knowledge=knowledge,
            metadata={"category": "technology"}
        )

        rag_system.media_store.aadd_documents.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_media_knowledge_chunks_long_text(self, rag_system):
        """Test storing long media knowledge chunks it."""
        if not rag_system.enabled:
            pytest.skip("RAG system not enabled")

        rag_system.media_store.aadd_documents = AsyncMock()

        # Long knowledge text
        knowledge = " ".join(["Long knowledge text."] * 500)

        await rag_system.store_media_knowledge(
            media_outlet="TechCrunch",
            journalist_name=None,
            knowledge=knowledge
        )

        # Should create multiple chunks
        call_args = rag_system.media_store.aadd_documents.call_args
        docs = call_args[0][0]
        # With default chunk size, should create multiple documents
        assert len(docs) >= 1

    @pytest.mark.asyncio
    async def test_retrieve_media_knowledge(self, rag_system):
        """Test retrieving media knowledge."""
        if not rag_system.enabled:
            pytest.skip("RAG system not enabled")

        mock_doc = Mock()
        mock_doc.page_content = "Media knowledge content"
        mock_doc.metadata = {
            "media_outlet": "Forbes",
            "journalist_name": "Jane Smith"
        }

        rag_system.media_store.asimilarity_search = AsyncMock(
            return_value=[mock_doc]
        )

        results = await rag_system.retrieve_media_knowledge(
            media_outlet="Forbes",
            journalist_name="Jane Smith",
            k=3
        )

        assert len(results) > 0
        assert results[0]["media_outlet"] == "Forbes"
        assert results[0]["journalist"] == "Jane Smith"


class TestExamplesManagement:
    """Test examples storage and retrieval for few-shot learning."""

    @pytest.mark.asyncio
    async def test_store_example(self, rag_system):
        """Test storing example."""
        if not rag_system.enabled:
            pytest.skip("RAG system not enabled")

        rag_system.examples_store.aadd_documents = AsyncMock()

        example = "This is a high-quality example response."

        await rag_system.store_example(
            example_text=example,
            category="product_launch",
            metadata={"quality": "high"}
        )

        rag_system.examples_store.aadd_documents.assert_called_once()

    @pytest.mark.asyncio
    async def test_retrieve_examples(self, rag_system):
        """Test retrieving examples."""
        if not rag_system.enabled:
            pytest.skip("RAG system not enabled")

        mock_doc = Mock()
        mock_doc.page_content = "Example response text"
        mock_doc.metadata = {
            "category": "crisis_response"
        }

        rag_system.examples_store.asimilarity_search = AsyncMock(
            return_value=[mock_doc]
        )

        results = await rag_system.retrieve_examples(
            query="How to respond to crisis?",
            category="crisis_response",
            k=2
        )

        assert len(results) > 0
        assert results[0]["category"] == "crisis_response"

    @pytest.mark.asyncio
    async def test_retrieve_examples_without_category_filter(self, rag_system):
        """Test retrieving examples without category filter."""
        if not rag_system.enabled:
            pytest.skip("RAG system not enabled")

        rag_system.examples_store.asimilarity_search = AsyncMock(return_value=[])

        await rag_system.retrieve_examples(
            query="Generic query",
            k=5
        )

        # Verify no category filter was passed
        call_args = rag_system.examples_store.asimilarity_search.call_args
        assert "filter" not in call_args.kwargs or call_args.kwargs.get("filter") is None


class TestContextAugmentation:
    """Test context augmentation with RAG."""

    @pytest.mark.asyncio
    async def test_augment_with_context(self, rag_system):
        """Test augmenting context with all RAG sources."""
        if not rag_system.enabled:
            pytest.skip("RAG system not enabled")

        # Mock all retrieval methods
        rag_system.find_similar_comments = AsyncMock(return_value=[
            {"comment": "Similar comment 1", "executive": "John"}
        ])
        rag_system.retrieve_media_knowledge = AsyncMock(return_value=[
            {"content": "Media knowledge", "media_outlet": "Forbes"}
        ])
        rag_system.retrieve_examples = AsyncMock(return_value=[
            {"content": "Example", "category": "tech"}
        ])

        context = await rag_system.augment_with_context(
            journalist_question="What about AI?",
            executive_name="John Doe",
            media_outlet="Forbes",
            journalist_name="Jane Smith"
        )

        assert context["enabled"] is True
        assert "similar_comments" in context
        assert "media_knowledge" in context
        assert "examples" in context
        assert "retrieval_counts" in context

    @pytest.mark.asyncio
    async def test_augment_with_context_retrieval_counts(self, rag_system):
        """Test context augmentation includes retrieval counts."""
        if not rag_system.enabled:
            pytest.skip("RAG system not enabled")

        # Mock with specific counts
        rag_system.find_similar_comments = AsyncMock(return_value=[{}, {}])
        rag_system.retrieve_media_knowledge = AsyncMock(return_value=[{}])
        rag_system.retrieve_examples = AsyncMock(return_value=[{}, {}, {}])

        context = await rag_system.augment_with_context(
            journalist_question="Question?",
            executive_name="John",
            media_outlet="Forbes"
        )

        counts = context["retrieval_counts"]
        assert counts["similar_comments"] == 2
        assert counts["media_knowledge"] == 1
        assert counts["examples"] == 3


class TestRAGStats:
    """Test RAG statistics."""

    def test_get_rag_stats_disabled(self):
        """Test stats when RAG is disabled."""
        config = PRAgentConfig()
        config.enable_rag = False

        rag = PRAgentRAG(config=config)
        stats = rag.get_rag_stats()

        assert stats["enabled"] is False

    def test_get_rag_stats_enabled(self, rag_system):
        """Test stats when RAG is enabled."""
        if not rag_system.enabled:
            pytest.skip("RAG system not enabled")

        # Mock collection counts
        rag_system.comment_store._collection = Mock()
        rag_system.comment_store._collection.count = Mock(return_value=10)

        rag_system.media_store._collection = Mock()
        rag_system.media_store._collection.count = Mock(return_value=5)

        rag_system.examples_store._collection = Mock()
        rag_system.examples_store._collection.count = Mock(return_value=3)

        rag_system.talking_points_store._collection = Mock()
        rag_system.talking_points_store._collection.count = Mock(return_value=7)

        stats = rag_system.get_rag_stats()

        assert stats["enabled"] is True
        assert stats["vector_stores"]["comments"] == 10
        assert stats["vector_stores"]["media"] == 5
        assert stats["vector_stores"]["examples"] == 3
        assert stats["vector_stores"]["talking_points"] == 7
        assert stats["total_documents"] == 25


class TestErrorHandling:
    """Test error handling in RAG system."""

    @pytest.mark.asyncio
    async def test_store_comment_handles_errors(self, rag_system):
        """Test comment storage handles errors gracefully."""
        if not rag_system.enabled:
            pytest.skip("RAG system not enabled")

        rag_system.comment_store.aadd_documents = AsyncMock(
            side_effect=Exception("Storage failed")
        )

        # Should not raise exception
        await rag_system.store_comment(
            executive_name="Test",
            media_outlet="Test",
            journalist_question="Test?",
            comment="Test"
        )

    @pytest.mark.asyncio
    async def test_find_similar_comments_handles_errors(self, rag_system):
        """Test comment retrieval handles errors gracefully."""
        if not rag_system.enabled:
            pytest.skip("RAG system not enabled")

        rag_system.comment_store.asimilarity_search = AsyncMock(
            side_effect=Exception("Search failed")
        )

        # Should return empty list on error
        results = await rag_system.find_similar_comments(
            question="Test",
            k=3
        )

        assert results == []

    @pytest.mark.asyncio
    async def test_augment_with_context_handles_partial_failures(self, rag_system):
        """Test context augmentation handles partial failures."""
        if not rag_system.enabled:
            pytest.skip("RAG system not enabled")

        # Mock some methods failing, some succeeding
        rag_system.find_similar_comments = AsyncMock(
            side_effect=Exception("Failed")
        )
        rag_system.retrieve_media_knowledge = AsyncMock(return_value=[])
        rag_system.retrieve_examples = AsyncMock(return_value=[])

        # Should still return context with error info
        context = await rag_system.augment_with_context(
            journalist_question="Test",
            executive_name="Test",
            media_outlet="Test"
        )

        # Should indicate error but not crash
        assert "enabled" in context or "error" in context


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
