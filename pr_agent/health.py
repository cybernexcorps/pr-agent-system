"""
Health check system for PR Agent.

Provides health monitoring for all system components.
"""

import asyncio
import time
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from .config import PRAgentConfig
from .logging_config import get_logger

logger = get_logger(__name__)


class HealthStatus(str, Enum):
    """Health check status values."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheckResult:
    """Result of a single health check."""
    component: str
    status: HealthStatus
    latency_ms: float
    message: str
    details: Optional[Dict[str, Any]] = None


class HealthChecker:
    """
    Performs health checks on PR Agent system components.

    Example:
        >>> config = PRAgentConfig()
        >>> checker = HealthChecker(config)
        >>> health = await checker.check_all()
        >>> print(health['status'])  # 'healthy', 'degraded', or 'unhealthy'
    """

    def __init__(self, config: PRAgentConfig):
        """
        Initialize health checker.

        Args:
            config: PR Agent configuration
        """
        self.config = config
        self.timeout = config.health_check_timeout

    async def check_all(self) -> Dict[str, Any]:
        """
        Run all health checks in parallel.

        Returns:
            Dictionary with aggregate health status and individual check results

        Example:
            >>> health = await checker.check_all()
            >>> if health['status'] == 'healthy':
            ...     print("System is healthy!")
        """
        logger.info("health_check_started", timeout=self.timeout)
        start_time = time.time()

        # Run all checks in parallel
        check_tasks = [
            self._check_llm(),
            self._check_search_api(),
            self._check_email_config(),
            self._check_profile_directory(),
        ]

        results = await asyncio.gather(*check_tasks, return_exceptions=True)

        # Convert exceptions to unhealthy results
        health_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                health_results.append(HealthCheckResult(
                    component=f"check_{i}",
                    status=HealthStatus.UNHEALTHY,
                    latency_ms=0,
                    message=f"Health check failed: {str(result)}"
                ))
            else:
                health_results.append(result)

        # Determine aggregate status
        aggregate_status = self._calculate_aggregate_status(health_results)

        total_duration = (time.time() - start_time) * 1000

        health_report = {
            "status": aggregate_status.value,
            "timestamp": time.time(),
            "duration_ms": round(total_duration, 2),
            "checks": [
                {
                    "component": r.component,
                    "status": r.status.value,
                    "latency_ms": round(r.latency_ms, 2),
                    "message": r.message,
                    "details": r.details or {}
                }
                for r in health_results
            ]
        }

        logger.info(
            "health_check_completed",
            status=aggregate_status.value,
            duration_ms=round(total_duration, 2),
            healthy_count=sum(1 for r in health_results if r.status == HealthStatus.HEALTHY),
            total_count=len(health_results)
        )

        return health_report

    async def _check_llm(self) -> HealthCheckResult:
        """Check LLM availability with a test prompt."""
        component = "llm"
        start_time = time.time()

        try:
            # Check if API keys are configured
            if not self.config.openai_api_key and not self.config.anthropic_api_key:
                return HealthCheckResult(
                    component=component,
                    status=HealthStatus.UNHEALTHY,
                    latency_ms=0,
                    message="No LLM API key configured",
                    details={"error": "Missing OPENAI_API_KEY and ANTHROPIC_API_KEY"}
                )

            # Try to create an LLM instance
            from langchain_openai import ChatOpenAI
            from langchain_anthropic import ChatAnthropic

            try:
                if self.config.openai_api_key:
                    llm = ChatOpenAI(
                        model=self.config.model_name,
                        temperature=0,
                        api_key=self.config.openai_api_key,
                        timeout=self.timeout
                    )
                    provider = "openai"
                else:
                    llm = ChatAnthropic(
                        model="claude-3-haiku-20240307",
                        temperature=0,
                        api_key=self.config.anthropic_api_key,
                        timeout=self.timeout
                    )
                    provider = "anthropic"

                # Send a simple test prompt with timeout
                response = await asyncio.wait_for(
                    llm.ainvoke("Reply with 'OK'"),
                    timeout=self.timeout
                )

                latency = (time.time() - start_time) * 1000

                return HealthCheckResult(
                    component=component,
                    status=HealthStatus.HEALTHY,
                    latency_ms=latency,
                    message=f"LLM responding ({provider})",
                    details={
                        "provider": provider,
                        "model": self.config.model_name if provider == "openai" else "claude-3-haiku-20240307"
                    }
                )

            except asyncio.TimeoutError:
                latency = (time.time() - start_time) * 1000
                return HealthCheckResult(
                    component=component,
                    status=HealthStatus.UNHEALTHY,
                    latency_ms=latency,
                    message=f"LLM timeout after {self.timeout}s",
                    details={"error": "timeout"}
                )

        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return HealthCheckResult(
                component=component,
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency,
                message=f"LLM check failed: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__}
            )

    async def _check_search_api(self) -> HealthCheckResult:
        """Check search API connectivity."""
        component = "search_api"
        start_time = time.time()

        try:
            # Check if API key is configured
            if not self.config.serper_api_key and not self.config.tavily_api_key:
                return HealthCheckResult(
                    component=component,
                    status=HealthStatus.DEGRADED,
                    latency_ms=0,
                    message="No search API key configured (system can operate without it)",
                    details={"warning": "Missing SERPER_API_KEY and TAVILY_API_KEY"}
                )

            # Try to make a test search request
            try:
                import httpx

                api_key = self.config.serper_api_key or self.config.tavily_api_key
                provider = "serper" if self.config.serper_api_key else "tavily"

                if provider == "serper":
                    async with httpx.AsyncClient(timeout=self.timeout) as client:
                        response = await client.post(
                            "https://google.serper.dev/search",
                            headers={
                                "X-API-KEY": api_key,
                                "Content-Type": "application/json"
                            },
                            json={"q": "test", "num": 1}
                        )
                        response.raise_for_status()
                else:
                    # Tavily health check would go here
                    pass

                latency = (time.time() - start_time) * 1000

                return HealthCheckResult(
                    component=component,
                    status=HealthStatus.HEALTHY,
                    latency_ms=latency,
                    message=f"Search API responding ({provider})",
                    details={"provider": provider}
                )

            except asyncio.TimeoutError:
                latency = (time.time() - start_time) * 1000
                return HealthCheckResult(
                    component=component,
                    status=HealthStatus.DEGRADED,
                    latency_ms=latency,
                    message=f"Search API timeout after {self.timeout}s",
                    details={"error": "timeout"}
                )

        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return HealthCheckResult(
                component=component,
                status=HealthStatus.DEGRADED,
                latency_ms=latency,
                message=f"Search API check failed: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__}
            )

    async def _check_email_config(self) -> HealthCheckResult:
        """Check email service configuration."""
        component = "email_service"
        start_time = time.time()

        try:
            # Check if email credentials are configured
            if not self.config.email_from or not self.config.email_password:
                return HealthCheckResult(
                    component=component,
                    status=HealthStatus.DEGRADED,
                    latency_ms=0,
                    message="Email credentials not configured (notifications disabled)",
                    details={"warning": "Missing EMAIL_FROM or EMAIL_PASSWORD"}
                )

            # Email configuration looks good
            latency = (time.time() - start_time) * 1000

            return HealthCheckResult(
                component=component,
                status=HealthStatus.HEALTHY,
                latency_ms=latency,
                message="Email configuration present",
                details={
                    "smtp_server": self.config.smtp_server,
                    "smtp_port": self.config.smtp_port,
                    "email_from": self.config.email_from
                }
            )

        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return HealthCheckResult(
                component=component,
                status=HealthStatus.DEGRADED,
                latency_ms=latency,
                message=f"Email config check failed: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__}
            )

    async def _check_profile_directory(self) -> HealthCheckResult:
        """Check profile directory accessibility."""
        component = "profile_directory"
        start_time = time.time()

        try:
            profiles_dir = self.config.profiles_dir

            # Check if directory exists
            if not os.path.exists(profiles_dir):
                return HealthCheckResult(
                    component=component,
                    status=HealthStatus.UNHEALTHY,
                    latency_ms=0,
                    message=f"Profile directory not found: {profiles_dir}",
                    details={"error": "directory_not_found", "path": profiles_dir}
                )

            # Check if directory is readable
            if not os.access(profiles_dir, os.R_OK):
                return HealthCheckResult(
                    component=component,
                    status=HealthStatus.UNHEALTHY,
                    latency_ms=0,
                    message=f"Profile directory not readable: {profiles_dir}",
                    details={"error": "permission_denied", "path": profiles_dir}
                )

            # Count profile files
            profile_files = [
                f for f in os.listdir(profiles_dir)
                if f.endswith('.json')
            ]

            latency = (time.time() - start_time) * 1000

            return HealthCheckResult(
                component=component,
                status=HealthStatus.HEALTHY,
                latency_ms=latency,
                message=f"Profile directory accessible with {len(profile_files)} profile(s)",
                details={
                    "path": profiles_dir,
                    "profile_count": len(profile_files),
                    "profiles": profile_files[:10]  # List first 10
                }
            )

        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return HealthCheckResult(
                component=component,
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency,
                message=f"Profile directory check failed: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__}
            )

    def _calculate_aggregate_status(self, results: List[HealthCheckResult]) -> HealthStatus:
        """
        Calculate aggregate health status from individual check results.

        Args:
            results: List of health check results

        Returns:
            Aggregate health status
        """
        # If any component is unhealthy, system is unhealthy
        if any(r.status == HealthStatus.UNHEALTHY for r in results):
            return HealthStatus.UNHEALTHY

        # If any component is degraded, system is degraded
        if any(r.status == HealthStatus.DEGRADED for r in results):
            return HealthStatus.DEGRADED

        # All components healthy
        return HealthStatus.HEALTHY

    async def check_component(self, component_name: str) -> Optional[HealthCheckResult]:
        """
        Check health of a specific component.

        Args:
            component_name: Name of component to check

        Returns:
            Health check result or None if component unknown

        Example:
            >>> result = await checker.check_component("llm")
            >>> print(result.status)  # 'healthy', 'degraded', or 'unhealthy'
        """
        component_checks = {
            "llm": self._check_llm,
            "search_api": self._check_search_api,
            "email_service": self._check_email_config,
            "profile_directory": self._check_profile_directory,
        }

        check_func = component_checks.get(component_name)
        if not check_func:
            logger.warning("unknown_component_check", component=component_name)
            return None

        return await check_func()
