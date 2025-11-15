"""
Integration tests for Phase 3 features.

Tests end-to-end workflows with memory, evaluation, and RAG enabled.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from pr_agent.agent import PRCommentAgent
from pr_agent.config import PRAgentConfig


@pytest.fixture
def phase3_config():
    """Create configuration with Phase 3 features enabled."""
    config = PRAgentConfig()
    config.anthropic_api_key = "test_anthropic_key"
    config.voyage_api_key = "test_voyage_key"
    config.serper_api_key = "test_serper_key"
    config.email_from = "test@example.com"
    config.email_password = "test_password"
    config.pr_manager_email = "pr@example.com"

    # Enable Phase 3 features
    config.enable_memory = True
    config.enable_evaluation = True
    config.enable_rag = True

    return config


@pytest.fixture
def phase3_agent(phase3_config):
    """Create PR Agent with Phase 3 features enabled."""
    with patch('pr_agent.agent.VoyageAIEmbeddings'):
        with patch('pr_agent.agent.Chroma'):
            with patch('pr_agent.agent.ChatAnthropic'):
                with patch('pr_agent.agent.PRAgentCache'):
                    agent = PRCommentAgent(config=phase3_config)
                    return agent


class TestPhase3Initialization:
    """Test Phase 3 components initialization."""

    def test_agent_initializes_with_phase3_features(self, phase3_agent):
        """Test agent initializes all Phase 3 components."""
        assert phase3_agent.memory is not None
        assert phase3_agent.evaluator is not None
        assert phase3_agent.rag is not None

    def test_phase3_features_can_be_disabled(self):
        """Test Phase 3 features can be individually disabled."""
        config = PRAgentConfig()
        config.anthropic_api_key = "test_key"
        config.serper_api_key = "test_key"
        config.email_from = "test@example.com"
        config.email_password = "test_password"

        # Disable all Phase 3 features
        config.enable_memory = False
        config.enable_evaluation = False
        config.enable_rag = False

        with patch('pr_agent.agent.ChatAnthropic'):
            with patch('pr_agent.agent.PRAgentCache'):
                agent = PRCommentAgent(config=config)

                # Should still initialize but features disabled
                assert agent.memory is None or not agent.memory.enabled
                assert agent.evaluator is None or not agent.evaluator.enabled
                assert agent.rag is None or not agent.rag.enabled


class TestPhase3Workflow:
    """Test end-to-end workflow with Phase 3 features."""

    @pytest.mark.asyncio
    async def test_generate_comment_with_memory_and_evaluation(self, phase3_agent):
        """Test generating comment with memory and evaluation."""
        # Mock all dependencies
        phase3_agent.profile_manager.load_profile = Mock(return_value={
            "name": "Jane Doe",
            "title": "CEO",
            "communication_style": "Direct and concise",
            "tone": "Professional",
            "talking_points": ["Innovation", "Growth"]
        })

        phase3_agent.media_researcher.research_async = AsyncMock(return_value={
            "analysis": "TechCrunch analysis"
        })

        phase3_agent.data_researcher.research_supporting_data_async = AsyncMock(return_value={
            "curated_data": "AI statistics"
        })

        phase3_agent.comment_drafter.draft_comment_async = AsyncMock(
            return_value="Drafted PR comment about AI."
        )

        phase3_agent.humanizer.humanize_comment_async = AsyncMock(
            return_value="Natural PR comment about AI."
        )

        phase3_agent.email_sender.send_comment_for_approval_async = AsyncMock(
            return_value=True
        )

        # Mock Phase 3 components
        if phase3_agent.memory and phase3_agent.memory.enabled:
            phase3_agent.memory.retrieve_similar_comments = AsyncMock(return_value=[])
            phase3_agent.memory.save_to_short_term = AsyncMock()
            phase3_agent.memory.save_to_long_term = AsyncMock()
            phase3_agent.memory.get_conversation_history = Mock(return_value=[])

        if phase3_agent.rag and phase3_agent.rag.enabled:
            phase3_agent.rag.augment_with_context = AsyncMock(return_value={
                "enabled": True,
                "similar_comments": [],
                "media_knowledge": [],
                "examples": [],
                "retrieval_counts": {
                    "similar_comments": 0,
                    "media_knowledge": 0,
                    "examples": 0
                }
            })
            phase3_agent.rag.store_comment = AsyncMock()

        if phase3_agent.evaluator and phase3_agent.evaluator.enabled:
            phase3_agent.evaluator.evaluate_comment = AsyncMock(return_value={
                "enabled": True,
                "overall_score": 0.85,
                "overall_passed": True,
                "criteria_scores": {
                    "tone_consistency": {"score": 0.9, "passed": True},
                    "data_usage": {"score": 0.8, "passed": True},
                    "authenticity": {"score": 0.85, "passed": True},
                    "relevance": {"score": 0.85, "passed": True}
                }
            })

        # Generate comment
        result = await phase3_agent.generate_comment_with_memory_and_evaluation(
            article_text="Article about AI trends in 2025.",
            journalist_question="What's your view on AI?",
            media_outlet="TechCrunch",
            executive_name="Jane Doe",
            session_id="test_session_123"
        )

        # Verify result structure
        assert result is not None
        assert result["humanized_comment"] == "Natural PR comment about AI."
        assert result["session_id"] == "test_session_123"
        assert "evaluation_scores" in result
        assert "phase3_enabled" in result

    @pytest.mark.asyncio
    async def test_workflow_without_phase3_features(self):
        """Test workflow works without Phase 3 features enabled."""
        config = PRAgentConfig()
        config.anthropic_api_key = "test_key"
        config.serper_api_key = "test_key"
        config.email_from = "test@example.com"
        config.email_password = "test_password"
        config.enable_memory = False
        config.enable_evaluation = False
        config.enable_rag = False

        with patch('pr_agent.agent.ChatAnthropic'):
            with patch('pr_agent.agent.PRAgentCache'):
                agent = PRCommentAgent(config=config)

                # Mock dependencies
                agent.profile_manager.load_profile = Mock(return_value={
                    "name": "Test",
                    "title": "CEO",
                    "communication_style": "Test",
                    "tone": "Test",
                    "talking_points": ["Test"]
                })

                agent.media_researcher.research_async = AsyncMock(return_value={})
                agent.data_researcher.research_supporting_data_async = AsyncMock(return_value={})
                agent.comment_drafter.draft_comment_async = AsyncMock(return_value="Draft")
                agent.humanizer.humanize_comment_async = AsyncMock(return_value="Final")
                agent.email_sender.send_comment_for_approval_async = AsyncMock(return_value=True)

                # Should work without Phase 3
                result = await agent.generate_comment_with_memory_and_evaluation(
                    article_text="Article",
                    journalist_question="Question?",
                    media_outlet="Forbes",
                    executive_name="Test"
                )

                assert result is not None
                assert result["humanized_comment"] == "Final"


class TestMemoryPersistence:
    """Test memory persistence across sessions."""

    @pytest.mark.asyncio
    async def test_memory_persists_across_calls(self, phase3_agent):
        """Test memory persists across multiple comment generations."""
        if not (phase3_agent.memory and phase3_agent.memory.enabled):
            pytest.skip("Memory not enabled")

        # Mock dependencies
        phase3_agent.profile_manager.load_profile = Mock(return_value={
            "name": "Test", "title": "CEO", "communication_style": "Test",
            "tone": "Test", "talking_points": ["Test"]
        })
        phase3_agent.media_researcher.research_async = AsyncMock(return_value={})
        phase3_agent.data_researcher.research_supporting_data_async = AsyncMock(return_value={})
        phase3_agent.comment_drafter.draft_comment_async = AsyncMock(return_value="Draft")
        phase3_agent.humanizer.humanize_comment_async = AsyncMock(return_value="Final")
        phase3_agent.email_sender.send_comment_for_approval_async = AsyncMock(return_value=True)

        # Mock memory methods
        phase3_agent.memory.retrieve_similar_comments = AsyncMock(return_value=[])
        phase3_agent.memory.save_to_short_term = AsyncMock()
        phase3_agent.memory.save_to_long_term = AsyncMock()
        phase3_agent.memory.get_conversation_history = Mock(return_value=[])

        # Mock RAG
        if phase3_agent.rag and phase3_agent.rag.enabled:
            phase3_agent.rag.augment_with_context = AsyncMock(return_value={
                "enabled": True, "similar_comments": [], "media_knowledge": [],
                "examples": [], "retrieval_counts": {"similar_comments": 0, "media_knowledge": 0, "examples": 0}
            })
            phase3_agent.rag.store_comment = AsyncMock()

        # Mock evaluator
        if phase3_agent.evaluator and phase3_agent.evaluator.enabled:
            phase3_agent.evaluator.evaluate_comment = AsyncMock(return_value={
                "enabled": True, "overall_score": 0.9, "overall_passed": True
            })

        session_id = "persistent_session"

        # First call
        await phase3_agent.generate_comment_with_memory_and_evaluation(
            article_text="Article 1",
            journalist_question="Question 1?",
            media_outlet="Forbes",
            executive_name="Test",
            session_id=session_id
        )

        # Second call with same session
        await phase3_agent.generate_comment_with_memory_and_evaluation(
            article_text="Article 2",
            journalist_question="Question 2?",
            media_outlet="Forbes",
            executive_name="Test",
            session_id=session_id
        )

        # Verify memory was saved
        assert phase3_agent.memory.save_to_short_term.call_count == 2


class TestEvaluationIntegration:
    """Test evaluation integration in workflow."""

    @pytest.mark.asyncio
    async def test_low_quality_comment_not_saved_to_long_term(self, phase3_agent):
        """Test low quality comments are not saved to long-term memory."""
        if not (phase3_agent.memory and phase3_agent.memory.enabled):
            pytest.skip("Memory not enabled")
        if not (phase3_agent.evaluator and phase3_agent.evaluator.enabled):
            pytest.skip("Evaluator not enabled")

        # Mock dependencies
        phase3_agent.profile_manager.load_profile = Mock(return_value={
            "name": "Test", "title": "CEO", "communication_style": "Test",
            "tone": "Test", "talking_points": ["Test"]
        })
        phase3_agent.media_researcher.research_async = AsyncMock(return_value={})
        phase3_agent.data_researcher.research_supporting_data_async = AsyncMock(return_value={})
        phase3_agent.comment_drafter.draft_comment_async = AsyncMock(return_value="Draft")
        phase3_agent.humanizer.humanize_comment_async = AsyncMock(return_value="Final")
        phase3_agent.email_sender.send_comment_for_approval_async = AsyncMock(return_value=True)

        # Mock memory
        phase3_agent.memory.retrieve_similar_comments = AsyncMock(return_value=[])
        phase3_agent.memory.save_to_short_term = AsyncMock()
        phase3_agent.memory.save_to_long_term = AsyncMock()
        phase3_agent.memory.get_conversation_history = Mock(return_value=[])

        # Mock RAG
        if phase3_agent.rag and phase3_agent.rag.enabled:
            phase3_agent.rag.augment_with_context = AsyncMock(return_value={
                "enabled": True, "similar_comments": [], "media_knowledge": [],
                "examples": [], "retrieval_counts": {"similar_comments": 0, "media_knowledge": 0, "examples": 0}
            })
            phase3_agent.rag.store_comment = AsyncMock()

        # Mock low quality evaluation
        phase3_agent.evaluator.evaluate_comment = AsyncMock(return_value={
            "enabled": True,
            "overall_score": 0.4,
            "overall_passed": False
        })

        await phase3_agent.generate_comment_with_memory_and_evaluation(
            article_text="Article",
            journalist_question="Question?",
            media_outlet="Forbes",
            executive_name="Test"
        )

        # Low quality comments should not be saved to long-term memory
        phase3_agent.memory.save_to_long_term.assert_not_called()


class TestPhase3Stats:
    """Test Phase 3 statistics retrieval."""

    def test_get_phase3_stats(self, phase3_agent):
        """Test getting Phase 3 statistics."""
        # Mock stats methods
        if phase3_agent.memory and phase3_agent.memory.enabled:
            phase3_agent.memory.get_memory_stats = Mock(return_value={
                "enabled": True,
                "active_sessions": 2,
                "long_term_documents": 10
            })

        if phase3_agent.rag and phase3_agent.rag.enabled:
            phase3_agent.rag.get_rag_stats = Mock(return_value={
                "enabled": True,
                "total_documents": 25
            })

        stats = phase3_agent.get_phase3_stats()

        assert "memory" in stats
        assert "rag" in stats
        assert "evaluator" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
