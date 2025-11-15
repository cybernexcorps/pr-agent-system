"""
Evaluation framework for PR Agent comment quality assessment.

Provides automated evaluation of generated comments using LangSmith
and custom evaluators for tone consistency, data usage, and authenticity.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from langsmith.evaluation import evaluate
from langchain.evaluation import load_evaluator, Criteria
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

from .config import PRAgentConfig
from .logging_config import get_logger

logger = get_logger(__name__)


class PRAgentEvaluator:
    """
    Evaluator for PR comment quality.

    Evaluates comments on three key criteria:
    1. Tone consistency - Does comment match executive's style?
    2. Data usage - Does comment effectively use supporting data?
    3. Authenticity - Does comment sound natural and human?
    """

    def __init__(self, config: PRAgentConfig):
        """
        Initialize evaluator.

        Args:
            config: PR Agent configuration
        """
        self.config = config
        self.enabled = config.enable_evaluation

        if not self.enabled:
            logger.info("evaluation_disabled", reason="enable_evaluation=False")
            return

        try:
            # Create evaluation LLM
            self.eval_llm = self._create_eval_llm()

            # Initialize custom evaluators
            self._initialize_evaluators()

            logger.info(
                "evaluator_initialized",
                model=config.evaluation_model,
                evaluators_count=len(self.evaluators)
            )

        except Exception as e:
            logger.error(
                "evaluator_initialization_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            self.enabled = False
            raise

    def _create_eval_llm(self):
        """Create LLM for evaluation."""
        if self.config.anthropic_api_key:
            return ChatAnthropic(
                model=self.config.evaluation_model,
                api_key=self.config.anthropic_api_key,
                temperature=0.0  # Consistent evaluation
            )
        elif self.config.openai_api_key:
            # Map to equivalent OpenAI model
            return ChatOpenAI(
                model="gpt-4o",
                api_key=self.config.openai_api_key,
                temperature=0.0
            )
        else:
            raise ValueError("No valid API key for evaluation LLM")

    def _initialize_evaluators(self):
        """Initialize custom evaluators."""
        self.evaluators = []

        # 1. Tone Consistency Evaluator
        self.tone_evaluator = load_evaluator(
            "criteria",
            criteria={
                "tone_consistency": (
                    "Does the comment match the executive's communication style, "
                    "tone, and personality as defined in their profile? "
                    "Consider speaking patterns, values, and preferred structure."
                )
            },
            llm=self.eval_llm
        )
        self.evaluators.append(("tone_consistency", self.tone_evaluator))

        # 2. Data Usage Evaluator
        self.data_evaluator = load_evaluator(
            "criteria",
            criteria={
                "data_usage": (
                    "Does the comment effectively incorporate and reference "
                    "supporting data, statistics, or insights? "
                    "Is the data used naturally and credibly?"
                )
            },
            llm=self.eval_llm
        )
        self.evaluators.append(("data_usage", self.data_evaluator))

        # 3. Authenticity Evaluator
        self.authenticity_evaluator = load_evaluator(
            "criteria",
            criteria={
                "authenticity": (
                    "Does the comment sound natural, authentic, and human? "
                    "Is it free from overly corporate or robotic language? "
                    "Would a reader believe this was written by a real person?"
                )
            },
            llm=self.eval_llm
        )
        self.evaluators.append(("authenticity", self.authenticity_evaluator))

        # 4. Relevance Evaluator
        self.relevance_evaluator = load_evaluator(
            "criteria",
            criteria={
                "relevance": (
                    "Is the comment directly relevant to the journalist's question? "
                    "Does it address the question comprehensively without straying off-topic?"
                )
            },
            llm=self.eval_llm
        )
        self.evaluators.append(("relevance", self.relevance_evaluator))

    async def evaluate_comment(
        self,
        comment: str,
        journalist_question: str,
        executive_profile: Dict[str, Any],
        supporting_data: Optional[Dict[str, Any]] = None,
        article_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a single PR comment.

        Args:
            comment: Generated comment to evaluate
            journalist_question: Original question
            executive_profile: Executive's profile
            supporting_data: Supporting data used (optional)
            article_text: Article context (optional)

        Returns:
            Dictionary with evaluation results and scores
        """
        if not self.enabled:
            return {"enabled": False}

        try:
            logger.info(
                "evaluating_comment",
                comment_length=len(comment),
                question_length=len(journalist_question)
            )

            start_time = datetime.now()

            # Build context for evaluation
            context = self._build_evaluation_context(
                journalist_question,
                executive_profile,
                supporting_data,
                article_text
            )

            # Run all evaluators
            results = {}
            scores = {}

            for criterion_name, evaluator in self.evaluators:
                try:
                    eval_result = await evaluator.aevaluate_strings(
                        prediction=comment,
                        input=context
                    )

                    # Extract score (0-1 scale)
                    score = eval_result.get("score", 0.0)
                    reasoning = eval_result.get("reasoning", "")

                    results[criterion_name] = {
                        "score": score,
                        "reasoning": reasoning,
                        "passed": score >= 0.7  # Threshold for passing
                    }
                    scores[criterion_name] = score

                    logger.info(
                        f"evaluation_{criterion_name}",
                        score=score,
                        passed=score >= 0.7
                    )

                except Exception as e:
                    logger.error(
                        f"evaluation_{criterion_name}_failed",
                        error=str(e),
                        error_type=type(e).__name__
                    )
                    results[criterion_name] = {
                        "score": 0.0,
                        "reasoning": f"Evaluation failed: {str(e)}",
                        "passed": False
                    }
                    scores[criterion_name] = 0.0

            # Calculate overall score
            overall_score = sum(scores.values()) / len(scores) if scores else 0.0

            duration = (datetime.now() - start_time).total_seconds()

            evaluation_results = {
                "enabled": True,
                "overall_score": overall_score,
                "overall_passed": overall_score >= 0.7,
                "criteria_scores": results,
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": duration,
                "comment_length": len(comment)
            }

            logger.info(
                "evaluation_complete",
                overall_score=overall_score,
                passed=overall_score >= 0.7,
                duration_seconds=round(duration, 2)
            )

            return evaluation_results

        except Exception as e:
            logger.error(
                "evaluation_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            return {
                "enabled": True,
                "error": str(e),
                "overall_score": 0.0,
                "overall_passed": False
            }

    def _build_evaluation_context(
        self,
        journalist_question: str,
        executive_profile: Dict[str, Any],
        supporting_data: Optional[Dict[str, Any]],
        article_text: Optional[str]
    ) -> str:
        """
        Build context string for evaluation.

        Args:
            journalist_question: Question asked
            executive_profile: Executive profile
            supporting_data: Supporting data
            article_text: Article text

        Returns:
            Context string for evaluation
        """
        context_parts = [
            f"Journalist Question: {journalist_question}",
            f"\nExecutive Profile:",
            f"  Name: {executive_profile.get('name', 'Unknown')}",
            f"  Title: {executive_profile.get('title', 'Unknown')}",
            f"  Communication Style: {executive_profile.get('communication_style', 'Unknown')}",
            f"  Tone: {executive_profile.get('tone', 'Unknown')}",
        ]

        if executive_profile.get('talking_points'):
            context_parts.append(
                f"  Key Talking Points: {', '.join(executive_profile['talking_points'][:3])}"
            )

        if supporting_data:
            context_parts.append(f"\nSupporting Data Available: Yes")

        if article_text:
            context_parts.append(f"\nArticle Context: {article_text[:500]}...")

        return "\n".join(context_parts)

    async def evaluate_batch(
        self,
        comments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluate multiple comments in batch.

        Args:
            comments: List of comment dictionaries with context

        Returns:
            Batch evaluation results
        """
        if not self.enabled:
            return {"enabled": False}

        try:
            logger.info("batch_evaluation_started", comment_count=len(comments))

            results = []
            for i, comment_data in enumerate(comments):
                eval_result = await self.evaluate_comment(
                    comment=comment_data.get("comment", ""),
                    journalist_question=comment_data.get("journalist_question", ""),
                    executive_profile=comment_data.get("executive_profile", {}),
                    supporting_data=comment_data.get("supporting_data"),
                    article_text=comment_data.get("article_text")
                )
                results.append(eval_result)

                logger.info(
                    "batch_evaluation_progress",
                    completed=i + 1,
                    total=len(comments),
                    score=eval_result.get("overall_score", 0.0)
                )

            # Calculate batch statistics
            scores = [r.get("overall_score", 0.0) for r in results]
            avg_score = sum(scores) / len(scores) if scores else 0.0
            pass_rate = sum(1 for r in results if r.get("overall_passed", False)) / len(results)

            batch_results = {
                "enabled": True,
                "comment_count": len(comments),
                "results": results,
                "statistics": {
                    "average_score": avg_score,
                    "pass_rate": pass_rate,
                    "min_score": min(scores) if scores else 0.0,
                    "max_score": max(scores) if scores else 0.0
                },
                "timestamp": datetime.now().isoformat()
            }

            logger.info(
                "batch_evaluation_complete",
                comment_count=len(comments),
                average_score=avg_score,
                pass_rate=pass_rate
            )

            return batch_results

        except Exception as e:
            logger.error(
                "batch_evaluation_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            return {
                "enabled": True,
                "error": str(e),
                "comment_count": len(comments)
            }

    def get_evaluation_summary(
        self,
        evaluation_results: Dict[str, Any]
    ) -> str:
        """
        Generate human-readable evaluation summary.

        Args:
            evaluation_results: Results from evaluate_comment()

        Returns:
            Formatted summary string
        """
        if not evaluation_results.get("enabled"):
            return "Evaluation is disabled."

        if "error" in evaluation_results:
            return f"Evaluation failed: {evaluation_results['error']}"

        overall_score = evaluation_results.get("overall_score", 0.0)
        passed = evaluation_results.get("overall_passed", False)

        summary = [
            f"Overall Quality Score: {overall_score:.2f}/1.00 ({'PASS' if passed else 'FAIL'})",
            "\nCriteria Breakdown:"
        ]

        criteria_scores = evaluation_results.get("criteria_scores", {})
        for criterion, data in criteria_scores.items():
            score = data.get("score", 0.0)
            status = "✓" if data.get("passed", False) else "✗"
            summary.append(f"  {status} {criterion.replace('_', ' ').title()}: {score:.2f}")

        return "\n".join(summary)
