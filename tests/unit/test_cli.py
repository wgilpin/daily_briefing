"""Unit tests for CLI argument parsing."""

import sys
from unittest.mock import patch

import pytest

from src.cli.main import parse_arguments


def test_cli_argument_parsing_with_output_flag():
    """Test CLI argument parsing with --output flag."""
    test_args = ["script.py", "--output", "/path/to/output.md"]
    
    with patch.object(sys, "argv", test_args):
        args = parse_arguments()
        assert args.output == "/path/to/output.md"


def test_cli_argument_parsing_with_days_flag():
    """Test CLI argument parsing with --days flag."""
    test_args = ["script.py", "--days", "7"]
    
    with patch.object(sys, "argv", test_args):
        args = parse_arguments()
        assert args.days == 7


def test_cli_argument_parsing_with_help_flag():
    """Test CLI argument parsing with --help flag."""
    test_args = ["script.py", "--help"]
    
    with patch.object(sys, "argv", test_args):
        # argparse exits with SystemExit(0) when --help is used
        with pytest.raises(SystemExit) as exc_info:
            parse_arguments()
        assert exc_info.value.code == 0


def test_cli_argument_parsing_with_default_values():
    """Test CLI argument parsing with default values."""
    test_args = ["script.py"]
    
    with patch.object(sys, "argv", test_args):
        args = parse_arguments()
        assert args.output == "digest.md"
        assert args.days == 1
        assert args.include == []
        assert args.exclude == []


def test_cli_argument_parsing_with_include_keywords():
    """Test CLI argument parsing with --include flag."""
    test_args = ["script.py", "--include", "machine learning", "AI"]
    
    with patch.object(sys, "argv", test_args):
        args = parse_arguments()
        assert "machine learning" in args.include
        assert "AI" in args.include


def test_cli_argument_parsing_with_exclude_keywords():
    """Test CLI argument parsing with --exclude flag."""
    test_args = ["script.py", "--exclude", "review", "survey"]
    
    with patch.object(sys, "argv", test_args):
        args = parse_arguments()
        assert "review" in args.exclude
        assert "survey" in args.exclude


def test_cli_argument_parsing_with_all_flags():
    """Test CLI argument parsing with all flags combined."""
    test_args = [
        "script.py",
        "--output", "custom.md",
        "--days", "5",
        "--include", "python", "testing",
        "--exclude", "draft",
    ]
    
    with patch.object(sys, "argv", test_args):
        args = parse_arguments()
        assert args.output == "custom.md"
        assert args.days == 5
        assert "python" in args.include
        assert "testing" in args.include
        assert "draft" in args.exclude

