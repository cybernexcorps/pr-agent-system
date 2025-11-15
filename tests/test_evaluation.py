"""
Tests for PR Agent evaluation framework.

Tests automated quality assessment of PR comments.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from pr_agent.evaluation import PRAgentEvaluator
from pr_agent.config import PRAgentConfig


@pytest.fixture
def config():
    """Create test configuration with evaluation enabled."""
    config = PRAgentConfig()
    config.enable_evaluation = True
    config.anthropic_api_key = "test_anthropic_key"
    config.evaluation_model = "claude-sonnet-4-5-20250929"
    return config


@pytest.fixture
def evaluator(config):
    """Create evaluator instance."""
    with patch('pr_agent.evaluation.ChatAnthropic'):
        with patch('pr_agent.evaluation.load_evaluator'):
            return PRAgentEvaluator(config=config)


class TestEvaluatorInitialization:
    """Test evaluator initialization."""

    def test_evaluator_disabled_when_config_false(self):
        """Test evaluator is disabled when config.enable_evaluation is False."""
        config = PRAgentConfig()
        config.enable_evaluation = False
        config.anthropic_api_key = "test_key"

        evaluator = PRAgentEvaluator(config=config)

        assert evaluator.enabled is False

    @patch('pr_agent.evaluation.ChatAnthropic')
    @patch('pr_agent.evaluation.load_evaluator')
    def test_evaluator_initialized_successfully(self, mock_load_eval, mock_chat, config):
        """Test evaluator initializes successfully with valid config."""
        evaluator = PRAgentEvaluator(config=config)

        assert evaluator.enabled is True
        assert evaluator.config == config
        assert len(evaluator.evaluators) == 4  # tone, data, authenticity, relevance

    @patch('pr_agent.evaluation.ChatOpenAI')
    @patch('pr_agent.evaluation.load_evaluator')
    def test_evaluator_uses_openai_when_anthropic_not_available(self, mock_load_eval, mock_chat):
        """Test evaluator falls back to OpenAI when Anthropic key not available."""
        config = PRAgentConfig()
        config.enable_evaluation = True
        config.anthropic_api_key = None
        config.openai_api_key = "test_openai_key"

        evaluator = PRAgentEvaluator(config=config)

        assert evaluator.enabled is True
        mock_chat.assert_called_once()


class TestCommentEvaluation:
    """Test comment evaluation."""

    @pytest.mark.asyncio
    async def test_evaluate_comment_success(self, evaluator):
        """Test successful comment evaluation."""
        if not evaluator.enabled:
            pytest.skip("Evaluator not enabled")

        # Mock evaluators
        mock_eval_result = {
            "score": 0.85,
            "reasoning": "Good tone match"
        }

        for _, eval_instance in evaluator.evaluators:
            eval_instance.aevaluate_strings = AsyncMock(return_value=mock_eval_result)

        executive_profile = {
            "name": "Jane Doe",
            "title": "CEO",
            "communication_style": "Direct and concise",
            "tone": "Professional yet approachable"
        }

        results = await evaluator.evaluate_comment(
            comment="This is a well-crafted PR comment.",
            journalist_question="What's your view on AI?",
            executive_profile=executive_profile,
            supporting_data={"curated_data": "AI statistics"},
            article_text="Article about AI trends"
        )

        assert results["enabled"] is True
        assert "overall_score" in results
        assert "criteria_scores" in results
        assert results["overall_score"] >= 0.0
        assert results["overall_score"] <= 1.0

    @pytest.mark.asyncio
    async def test_evaluate_comment_with_high_score(self, evaluator):
        """Test evaluation with high quality comment."""
        if not evaluator.enabled:
            pytest.skip("Evaluator not enabled")

        # Mock high scores
        mock_eval_result = {
            "score": 0.95,
            "reasoning": "Excellent quality"
        }

        for _, eval_instance in evaluator.evaluators:
            eval_instance.aevaluate_strings = AsyncMock(return_value=mock_eval_result)

        results = await evaluator.evaluate_comment(
            comment="Excellent comment",
            journalist_question="Question?",
            executive_profile={"name": "Test", "title": "CEO", "communication_style": "Test", "tone": "Test"}
        )

        assert results["overall_passed"] is True
        assert results["overall_score"] >= 0.7

    @pytest.mark.asyncio
    async def test_evaluate_comment_with_low_score(self, evaluator):
        """Test evaluation with low quality comment."""
        if not evaluator.enabled:
            pytest.skip("Evaluator not enabled")

        # Mock low scores
        mock_eval_result = {
            "score": 0.45,
            "reasoning": "Poor quality"
        }

        for _, eval_instance in evaluator.evaluators:
            eval_instance.aevaluate_strings = AsyncMock(return_value=mock_eval_result)

        results = await evaluator.evaluate_comment(
            comment="Poor comment",
            journalist_question="Question?",
            executive_profile={"name": "Test", "title": "CEO", "communication_style": "Test", "tone": "Test"}
        )

        assert results["overall_passed"] is False
        assert results["overall_score"] < 0.7

    @pytest.mark.asyncio
    async def test_evaluate_comment_criteria_breakdown(self, evaluator):
        """Test that evaluation returns breakdown by criteria."""
        if not evaluator.enabled:
            pytest.skip("Evaluator not enabled")

        # Mock different scores for different criteria
        scores = {
            "tone_consistency": 0.9,
            "data_usage": 0.8,
            "authenticity": 0.85,
            "relevance": 0.95
        }

        for criterion_name, eval_instance in evaluator.evaluators:
            score = scores.get(criterion_name, 0.8)
            eval_instance.aevaluate_strings = AsyncMock(return_value={
                "score": score,
                "reasoning": f"Score for {criterion_name}"
            })

        results = await evaluator.evaluate_comment(
            comment="Test comment",
            journalist_question="Question?",
            executive_profile={"name": "Test", "title": "CEO", "communication_style": "Test", "tone": "Test"}
        )

        criteria_scores = results["criteria_scores"]
        assert "tone_consistency" in criteria_scores
        assert "data_usage" in criteria_scores
        assert "authenticity" in criteria_scores
        assert "relevance" in criteria_scores

        for criterion, data in criteria_scores.items():
            assert "score" in data
            assert "reasoning" in data
            assert "passed" in data


class TestBatchEvaluation:
    """Test batch evaluation of multiple comments."""

    @pytest.mark.asyncio
    async def test_evaluate_batch(self, evaluator):
        """Test evaluating multiple comments in batch."""
        if not evaluator.enabled:
            pytest.skip("Evaluator not enabled")

        # Mock evaluators
        mock_eval_result = {
            "score": 0.85,
            "reasoning": "Good quality"
        }

        for _, eval_instance in evaluator.evaluators:
            eval_instance.aevaluate_strings = AsyncMock(return_value=mock_eval_result)

        comments = [
            {
                "comment": "Comment 1",
                "journalist_question": "Question 1?",
                "executive_profile": {"name": "Test", "title": "CEO", "communication_style": "Test", "tone": "Test"}
            },
            {
                "comment": "Comment 2",
                "journalist_question": "Question 2?",
                "executive_profile": {"name": "Test", "title": "CEO", "communication_style": "Test", "tone": "Test"}
            },
            {
                "comment": "Comment 3",
                "journalist_question": "Question 3?",
                "executive_profile": {"name": "Test", "title": "CEO", "communication_style": "Test", "tone": "Test"}
            }
        ]

        results = await evaluator.evaluate_batch(comments)

        assert results["enabled"] is True
        assert results["comment_count"] == 3
        assert len(results["results"]) == 3
        assert "statistics" in results
        assert "average_score" in results["statistics"]
        assert "pass_rate" in results["statistics"]

    @pytest.mark.asyncio
    async def test_evaluate_batch_statistics(self, evaluator):
        """Test batch evaluation statistics calculation."""
        if not evaluator.enabled:
            pytest.skip("Evaluator not enabled")

        # Mock varying scores
        scores = [0.9, 0.75, 0.6, 0.85]
        eval_calls = 0

        async def mock_evaluate(*args, **kwargs):
            nonlocal eval_calls
            score = scores[eval_calls % len(scores)]
            eval_calls += 1
            return {
                "score": score,
                "reasoning": f"Score {score}"
            }

        for _, eval_instance in evaluator.evaluators:
            eval_instance.aevaluate_strings = mock_evaluate

        comments = [
            {"comment": f"Comment {i}", "journalist_question": f"Q{i}?",
             "executive_profile": {"name": "Test", "title": "CEO", "communication_style": "Test", "tone": "Test"}}
            for i in range(4)
        ]

        results = await evaluator.evaluate_batch(comments)

        stats = results["statistics"]
        assert "average_score" in stats
        assert "pass_rate" in stats
        assert "min_score" in stats
        assert "max_score" in stats


class TestEvaluationSummary:
    """Test evaluation summary generation."""

    def test_get_evaluation_summary_disabled(self, evaluator):
        """Test summary when evaluation is disabled."""
        results = {"enabled": False}

        summary = evaluator.get_evaluation_summary(results)

        assert "disabled" in summary.lower()

    def test_get_evaluation_summary_with_error(self, evaluator):
        """Test summary when evaluation has error."""
        results = {
            "enabled": True,
            "error": "Evaluation failed"
        }

        summary = evaluator.get_evaluation_summary(results)

        assert "failed" in summary.lower()

    def test_get_evaluation_summary_success(self, evaluator):
        """Test summary for successful evaluation."""
        results = {
            "enabled": True,
            "overall_score": 0.85,
            "overall_passed": True,
            "criteria_scores": {
                "tone_consistency": {
                    "score": 0.9,
                    "passed": True,
                    "reasoning": "Good match"
                },
                "data_usage": {
                    "score": 0.8,
                    "passed": True,
                    "reasoning": "Effective use"
                }
            }
        }

        summary = evaluator.get_evaluation_summary(results)

        assert "0.85" in summary
        assert "PASS" in summary
        assert "tone consistency" in summary.lower()
        assert "data usage" in summary.lower()


class TestErrorHandling:
    """Test error handling in evaluator."""

    @pytest.mark.asyncio
    async def test_evaluate_comment_handles_evaluator_error(self, evaluator):
        """Test evaluation handles individual evaluator errors."""
        if not evaluator.enabled:
            pytest.skip("Evaluator not enabled")

        # Mock one evaluator failing
        for i, (_, eval_instance) in enumerate(evaluator.evaluators):
            if i == 0:
                eval_instance.aevaluate_strings = AsyncMock(
                    side_effect=Exception("Evaluator failed")
                )
            else:
                eval_instance.aevaluate_strings = AsyncMock(return_value={
                    "score": 0.8,
                    "reasoning": "Good"
                })

        results = await evaluator.evaluate_comment(
            comment="Test",
            journalist_question="Question?",
            executive_profile={"name": "Test", "title": "CEO", "communication_style": "Test", "tone": "Test"}
        )

        # Should still return results with failed evaluator having score 0
        assert results["enabled"] is True
        assert "criteria_scores" in results

    @pytest.mark.asyncio
    async def test_evaluate_batch_handles_errors(self, evaluator):
        """Test batch evaluation handles errors gracefully."""
        if not evaluator.enabled:
            pytest.skip("Evaluator not enabled")

        # Mock evaluators working
        for _, eval_instance in evaluator.evaluators:
            eval_instance.aevaluate_strings = AsyncMock(return_value={
                "score": 0.8,
                "reasoning": "Good"
            })

        # Empty comments list
        results = await evaluator.evaluate_batch([])

        assert results["comment_count"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
