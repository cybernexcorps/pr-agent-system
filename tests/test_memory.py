"""
Tests for PR Agent memory system.

Tests short-term conversation memory and long-term vector memory.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from pr_agent.memory import PRAgentMemory
from pr_agent.config import PRAgentConfig


@pytest.fixture
def config():
    """Create test configuration with memory enabled."""
    config = PRAgentConfig()
    config.enable_memory = True
    config.voyage_api_key = "test_voyage_key"
    config.memory_vector_store_path = "./test_data/memory_store"
    config.memory_max_tokens = 2000
    return config


@pytest.fixture
def mock_llm():
    """Create mock LLM for token counting."""
    llm = Mock()
    llm.get_num_tokens = Mock(return_value=100)
    return llm


@pytest.fixture
def memory_system(config, mock_llm):
    """Create memory system instance."""
    with patch('pr_agent.memory.VoyageAIEmbeddings'):
        with patch('pr_agent.memory.Chroma'):
            return PRAgentMemory(config=config, llm=mock_llm)


class TestMemoryInitialization:
    """Test memory system initialization."""

    def test_memory_disabled_when_config_false(self, mock_llm):
        """Test memory is disabled when config.enable_memory is False."""
        config = PRAgentConfig()
        config.enable_memory = False

        memory = PRAgentMemory(config=config, llm=mock_llm)

        assert memory.enabled is False

    def test_memory_disabled_when_no_api_key(self, mock_llm):
        """Test memory is disabled when VOYAGE_API_KEY is not set."""
        config = PRAgentConfig()
        config.enable_memory = True
        config.voyage_api_key = None

        memory = PRAgentMemory(config=config, llm=mock_llm)

        assert memory.enabled is False

    @patch('pr_agent.memory.VoyageAIEmbeddings')
    @patch('pr_agent.memory.Chroma')
    def test_memory_initialized_successfully(self, mock_chroma, mock_embeddings, config, mock_llm):
        """Test memory initializes successfully with valid config."""
        memory = PRAgentMemory(config=config, llm=mock_llm)

        assert memory.enabled is True
        assert memory.config == config
        assert memory.llm == mock_llm
        mock_embeddings.assert_called_once()
        mock_chroma.assert_called_once()


class TestShortTermMemory:
    """Test short-term conversation memory."""

    def test_get_short_term_memory_creates_session(self, memory_system):
        """Test creating new session creates short-term memory."""
        if not memory_system.enabled:
            pytest.skip("Memory system not enabled")

        session_id = "test_session_1"

        memory = memory_system.get_short_term_memory(session_id)

        assert session_id in memory_system.short_term_sessions
        assert memory is not None

    def test_get_short_term_memory_returns_existing(self, memory_system):
        """Test getting existing session returns same memory instance."""
        if not memory_system.enabled:
            pytest.skip("Memory system not enabled")

        session_id = "test_session_2"

        memory1 = memory_system.get_short_term_memory(session_id)
        memory2 = memory_system.get_short_term_memory(session_id)

        assert memory1 is memory2

    @pytest.mark.asyncio
    async def test_save_to_short_term(self, memory_system):
        """Test saving interaction to short-term memory."""
        if not memory_system.enabled:
            pytest.skip("Memory system not enabled")

        session_id = "test_session_3"
        question = "What are your thoughts on AI?"
        comment = "AI is transforming how we work and live."

        # Mock the save_context method
        memory = memory_system.get_short_term_memory(session_id)
        memory.asave_context = AsyncMock()

        await memory_system.save_to_short_term(
            session_id=session_id,
            question=question,
            comment=comment
        )

        memory.asave_context.assert_called_once()

    def test_clear_session(self, memory_system):
        """Test clearing session memory."""
        if not memory_system.enabled:
            pytest.skip("Memory system not enabled")

        session_id = "test_session_4"

        # Create session
        memory_system.get_short_term_memory(session_id)
        assert session_id in memory_system.short_term_sessions

        # Clear session
        memory_system.clear_session(session_id)
        assert session_id not in memory_system.short_term_sessions


class TestLongTermMemory:
    """Test long-term vector memory."""

    @pytest.mark.asyncio
    async def test_save_to_long_term(self, memory_system):
        """Test saving comment to long-term memory."""
        if not memory_system.enabled:
            pytest.skip("Memory system not enabled")

        # Mock vector store
        memory_system.vector_store.aadd_documents = AsyncMock()

        await memory_system.save_to_long_term(
            executive_name="John Doe",
            media_outlet="TechCrunch",
            journalist_question="What's your view on remote work?",
            comment="Remote work offers flexibility and productivity gains.",
            metadata={"score": 0.9}
        )

        memory_system.vector_store.aadd_documents.assert_called_once()

    @pytest.mark.asyncio
    async def test_retrieve_similar_comments(self, memory_system):
        """Test retrieving similar comments from long-term memory."""
        if not memory_system.enabled:
            pytest.skip("Memory system not enabled")

        # Mock vector store search
        mock_doc = Mock()
        mock_doc.page_content = "Question: Test?\n\nComment: Test response."
        mock_doc.metadata = {
            "executive_name": "Jane Doe",
            "media_outlet": "Forbes",
            "question": "Test?",
            "timestamp": datetime.now().isoformat(),
            "comment_length": 13
        }

        memory_system.vector_store.asimilarity_search = AsyncMock(
            return_value=[mock_doc]
        )

        results = await memory_system.retrieve_similar_comments(
            question="What about remote work?",
            executive_name="Jane Doe",
            k=3
        )

        assert len(results) > 0
        assert results[0]["executive"] == "Jane Doe"
        assert results[0]["media_outlet"] == "Forbes"

    @pytest.mark.asyncio
    async def test_retrieve_similar_comments_with_filters(self, memory_system):
        """Test retrieving comments with metadata filters."""
        if not memory_system.enabled:
            pytest.skip("Memory system not enabled")

        memory_system.vector_store.asimilarity_search = AsyncMock(return_value=[])

        await memory_system.retrieve_similar_comments(
            question="Test question",
            executive_name="John Doe",
            media_outlet="TechCrunch",
            k=5
        )

        # Verify filter was passed
        call_args = memory_system.vector_store.asimilarity_search.call_args
        assert "filter" in call_args.kwargs


class TestMemoryStats:
    """Test memory statistics."""

    def test_get_memory_stats_disabled(self, mock_llm):
        """Test stats when memory is disabled."""
        config = PRAgentConfig()
        config.enable_memory = False

        memory = PRAgentMemory(config=config, llm=mock_llm)
        stats = memory.get_memory_stats()

        assert stats["enabled"] is False

    def test_get_memory_stats_enabled(self, memory_system):
        """Test stats when memory is enabled."""
        if not memory_system.enabled:
            pytest.skip("Memory system not enabled")

        # Mock collection count
        memory_system.vector_store._collection = Mock()
        memory_system.vector_store._collection.count = Mock(return_value=42)

        # Create some sessions
        memory_system.get_short_term_memory("session_1")
        memory_system.get_short_term_memory("session_2")

        stats = memory_system.get_memory_stats()

        assert stats["enabled"] is True
        assert stats["active_sessions"] == 2
        assert stats["long_term_documents"] == 42


class TestErrorHandling:
    """Test error handling in memory system."""

    @pytest.mark.asyncio
    async def test_save_to_short_term_handles_errors(self, memory_system):
        """Test save to short-term handles errors gracefully."""
        if not memory_system.enabled:
            pytest.skip("Memory system not enabled")

        session_id = "error_session"
        memory = memory_system.get_short_term_memory(session_id)
        memory.asave_context = AsyncMock(side_effect=Exception("Save failed"))

        # Should not raise exception
        await memory_system.save_to_short_term(
            session_id=session_id,
            question="Test",
            comment="Test"
        )

    @pytest.mark.asyncio
    async def test_retrieve_similar_comments_handles_errors(self, memory_system):
        """Test retrieval handles errors gracefully."""
        if not memory_system.enabled:
            pytest.skip("Memory system not enabled")

        memory_system.vector_store.asimilarity_search = AsyncMock(
            side_effect=Exception("Search failed")
        )

        # Should return empty list on error
        results = await memory_system.retrieve_similar_comments(
            question="Test",
            k=3
        )

        assert results == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
