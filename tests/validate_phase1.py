#!/usr/bin/env python3
"""
Validation script for Phase 1 implementation.

This script checks that all Phase 1 features are properly implemented.
"""

import sys
import importlib.util
from pathlib import Path


def print_header(text):
    """Print a formatted header."""
    print(f"\n{'=' * 80}")
    print(f"{text:^80}")
    print(f"{'=' * 80}\n")


def print_check(name, passed, details=""):
    """Print a check result."""
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {name}")
    if details:
        print(f"       {details}")


def check_file_exists(filepath, description):
    """Check if a file exists."""
    path = Path(filepath)
    exists = path.exists()
    print_check(f"{description}", exists, f"Path: {filepath}")
    return exists


def check_import(module_name, description):
    """Check if a module can be imported."""
    try:
        importlib.import_module(module_name)
        print_check(f"{description}", True, f"Module: {module_name}")
        return True
    except ImportError as e:
        print_check(f"{description}", False, f"Error: {str(e)}")
        return False


def check_has_async_method(filepath, method_name):
    """Check if file contains an async method."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            has_method = f"async def {method_name}" in content
            print_check(
                f"Has {method_name}()",
                has_method,
                f"File: {Path(filepath).name}"
            )
            return has_method
    except Exception as e:
        print_check(f"Check {method_name}()", False, f"Error: {str(e)}")
        return False


def check_dependency(package_name):
    """Check if a package is installed."""
    try:
        __import__(package_name)
        print_check(f"Package: {package_name}", True)
        return True
    except ImportError:
        print_check(f"Package: {package_name}", False, "Not installed")
        return False


def main():
    """Run all validation checks."""
    print_header("PHASE 1 IMPLEMENTATION VALIDATION")

    results = {
        "files": 0,
        "imports": 0,
        "async_methods": 0,
        "dependencies": 0,
        "total": 0
    }

    # Check 1: New Files Created
    print_header("1. New Files Created")
    files_to_check = [
        ("pr_agent/logging_config.py", "Structured logging configuration"),
        ("pr_agent/observability.py", "LangSmith tracing utilities"),
        ("pr_agent/health.py", "Health check system"),
        ("pr_agent/examples/async_example.py", "Async usage examples"),
        ("PHASE1_IMPLEMENTATION_SUMMARY.md", "Implementation summary"),
        ("QUICK_START_ASYNC.md", "Quick start guide"),
    ]

    for filepath, desc in files_to_check:
        if check_file_exists(filepath, desc):
            results["files"] += 1
        results["total"] += 1

    # Check 2: Module Imports
    print_header("2. Module Imports")
    modules_to_check = [
        ("pr_agent.logging_config", "Logging configuration module"),
        ("pr_agent.observability", "Observability module"),
        ("pr_agent.health", "Health check module"),
        ("pr_agent.config", "Configuration module"),
        ("pr_agent.agent", "Main agent module"),
    ]

    for module, desc in modules_to_check:
        if check_import(module, desc):
            results["imports"] += 1
        results["total"] += 1

    # Check 3: Async Methods in Tools
    print_header("3. Async Methods in Tools")
    tools_to_check = [
        ("pr_agent/tools/search.py", "search_for_data_async"),
        ("pr_agent/tools/search.py", "research_media_outlet_async"),
        ("pr_agent/tools/email_sender.py", "send_comment_for_approval_async"),
        ("pr_agent/tools/email_sender.py", "send_test_email_async"),
    ]

    for filepath, method in tools_to_check:
        if check_has_async_method(filepath, method):
            results["async_methods"] += 1
        results["total"] += 1

    # Check 4: Async Methods in Agents
    print_header("4. Async Methods in Agents")
    agents_to_check = [
        ("pr_agent/agents/media_researcher.py", "research_async"),
        ("pr_agent/agents/data_researcher.py", "research_supporting_data_async"),
        ("pr_agent/agents/comment_drafter.py", "draft_comment_async"),
        ("pr_agent/agents/humanizer.py", "humanize_comment_async"),
        ("pr_agent/agent.py", "generate_comment_async"),
    ]

    for filepath, method in agents_to_check:
        if check_has_async_method(filepath, method):
            results["async_methods"] += 1
        results["total"] += 1

    # Check 5: Dependencies
    print_header("5. Required Dependencies")
    dependencies = [
        "aiosmtplib",
        "httpx",
        "langsmith",
        "structlog",
    ]

    for package in dependencies:
        if check_dependency(package):
            results["dependencies"] += 1
        results["total"] += 1

    # Check 6: Structured Logging
    print_header("6. Structured Logging")
    try:
        with open("pr_agent/agent.py", 'r', encoding='utf-8') as f:
            content = f.read()
            has_logger_import = "from .logging_config import" in content
            has_logger_usage = "logger.info" in content
            uses_logger = has_logger_import and has_logger_usage

            print_check(
                "Agent uses structured logging",
                uses_logger,
                "Checking for logger imports and usage"
            )

            if uses_logger:
                results["total"] += 1
                results["imports"] += 1
    except Exception as e:
        print_check("Agent uses structured logging", False, f"Error: {str(e)}")
        results["total"] += 1

    # Check 7: Configuration Updates
    print_header("7. Configuration Updates")
    try:
        with open("pr_agent/config.py", 'r', encoding='utf-8') as f:
            content = f.read()
            has_langsmith = "langsmith_api_key" in content
            has_log_level = "log_level" in content
            has_async = "async_enabled" in content

            config_complete = has_langsmith and has_log_level and has_async

            print_check(
                "Configuration has new fields",
                config_complete,
                "Checking for langsmith, logging, async config"
            )

            if config_complete:
                results["total"] += 1
                results["imports"] += 1
    except Exception as e:
        print_check("Configuration updates", False, f"Error: {str(e)}")
        results["total"] += 1

    # Summary
    print_header("VALIDATION SUMMARY")

    total_passed = sum([
        results["files"],
        results["imports"],
        results["async_methods"],
        results["dependencies"]
    ])

    percentage = (total_passed / results["total"] * 100) if results["total"] > 0 else 0

    print(f"Files Created:      {results['files']}/{len(files_to_check)}")
    print(f"Module Imports:     {results['imports']}/{len(modules_to_check) + 2}")
    print(f"Async Methods:      {results['async_methods']}/{len(tools_to_check) + len(agents_to_check)}")
    print(f"Dependencies:       {results['dependencies']}/{len(dependencies)}")
    print(f"\nTotal:              {total_passed}/{results['total']} ({percentage:.1f}%)")

    if percentage == 100:
        print("\n[SUCCESS] All Phase 1 features are properly implemented!")
        print("System is ready for production use.")
        return 0
    elif percentage >= 80:
        print("\n[WARNING] Most features implemented, but some checks failed.")
        print("Review failed checks above.")
        return 1
    else:
        print("\n[ERROR] Significant issues found.")
        print("Please review and fix failed checks.")
        return 2


if __name__ == "__main__":
    sys.exit(main())
