#!/usr/bin/env python3
"""
Helper script for debugging Zulip Terminal.

This script provides utilities for common debugging tasks:
1. Analyzing debug logs
2. Testing connectivity to Zulip server
3. Checking terminal capabilities
"""

import argparse
import json
import logging
import os
import re
import subprocess
from typing import Optional


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def analyze_debug_log(log_file: str = "debug.log") -> None:
    """
    Analyze a debug log file for common issues.
    """
    if not os.path.exists(log_file):
        logger.error("Log file '%s' not found", log_file)
        return

    logger.info("Analyzing %s...", log_file)
    with open(log_file, "r") as f:
        content = f.read()

    # Look for error patterns
    error_patterns = [r"ERROR", r"Exception", r"Traceback", r"Failed to"]

    errors_found = False
    for pattern in error_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            line_start = content.rfind("\n", 0, match.start()) + 1
            line_end = content.find("\n", match.end())
            if line_end == -1:
                line_end = len(content)

            line = content[line_start:line_end].strip()
            logger.warning("Potential issue found: %s", line)
            errors_found = True

    if not errors_found:
        logger.info("No obvious errors found in the log file.")


def test_connectivity(server_url: Optional[str] = None) -> None:
    """
    Test connectivity to a Zulip server.
    """
    if not server_url:
        # Try to get server URL from zuliprc
        zuliprc_path = os.path.expanduser("~/.zuliprc")
        if os.path.exists(zuliprc_path):
            with open(zuliprc_path, "r") as f:
                for line in f:
                    if line.startswith("site="):
                        server_url = line.split("=")[1].strip()
                        break

    if not server_url:
        logger.error("No server URL provided and couldn't find one in ~/.zuliprc")
        return

    logger.info("Testing connectivity to %s...", server_url)
    try:
        import requests

        response = requests.get(f"{server_url}/api/v1/server_settings")
        if response.status_code == 200:
            logger.info("Successfully connected to %s", server_url)
            try:
                settings = response.json()
                logger.info(
                    "Server version: %s", settings.get("zulip_version", "unknown")
                )
            except json.JSONDecodeError:
                logger.error("Received response, but couldn't parse as JSON")
        else:
            logger.error("Failed to connect: HTTP status %s", response.status_code)
    except Exception as e:
        logger.error("Connection error: %s", e)


def check_terminal_capabilities() -> None:
    """
    Check for terminal capabilities that might affect Zulip Terminal.
    """
    logger.info("Checking terminal capabilities...")

    # Check for color support
    colors = os.environ.get("TERM", "unknown")
    logger.info("TERM environment: %s", colors)

    if "COLORTERM" in os.environ:
        logger.info("COLORTERM: %s", os.environ["COLORTERM"])

    # Check for Unicode support
    logger.info("Testing Unicode rendering capabilities:")
    test_chars = [
        ("Basic symbols", "▶ ◀ ✓ ✗"),
        ("Emoji (simple)", "😀 🙂 👍"),
        ("Box drawing", "│ ┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼"),
        ("Math symbols", "∞ ∑ √ ∫ π"),
    ]

    for name, chars in test_chars:
        logger.info("  %s: %s", name, chars)


def main() -> None:
    """
    Main entry point for the debugging helper.
    """
    parser = argparse.ArgumentParser(description="Zulip Terminal Debugging Helper")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Log analyzer
    log_parser = subparsers.add_parser("log", help="Analyze debug logs")
    log_parser.add_argument("--file", default="debug.log", help="Log file to analyze")

    # Connectivity test
    conn_parser = subparsers.add_parser("connect", help="Test connectivity")
    conn_parser.add_argument(
        "--server", help="Server URL (e.g., https://chat.zulip.org)"
    )

    # Terminal test
    subparsers.add_parser("terminal", help="Check terminal capabilities")

    # Run zulip-term with debug
    run_parser = subparsers.add_parser("run", help="Run zulip-term with debugging")
    run_parser.add_argument("--profile", action="store_true", help="Enable profiling")

    args = parser.parse_args()

    if args.command == "log":
        analyze_debug_log(args.file)
    elif args.command == "connect":
        test_connectivity(args.server)
    elif args.command == "terminal":
        check_terminal_capabilities()
    elif args.command == "run":
        cmd = ["zulip-term", "-d"]
        if args.profile:
            cmd.append("--profile")
        logger.info("Running: %s", " ".join(cmd))
        subprocess.run(cmd, check=False)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
