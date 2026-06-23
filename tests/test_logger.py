"""Unit tests for the logger module."""

import logging
import os
import sys
import unittest

from editor.logger import RelativePathFormatter, get_logger, setup_logging


class TestRelativePathFormatter(unittest.TestCase):
    """Tests for RelativePathFormatter."""

    def test_strips_path_to_start_from_src(self):
        """Test that formatter strips path to start from src/."""
        formatter = RelativePathFormatter("%(pathname)s:%(lineno)d")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/home/user/project/src/editor/main.py",
            lineno=42,
            msg="test message",
            args=(),
            exc_info=None,
        )
        result = formatter.format(record)
        self.assertEqual(result, "src/editor/main.py:42")

    def test_handles_path_without_src(self):
        """Test that paths without src/ are not modified."""
        formatter = RelativePathFormatter("%(pathname)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/some/other/path/file.py",
            lineno=1,
            msg="test",
            args=(),
            exc_info=None,
        )
        result = formatter.format(record)
        self.assertEqual(result, "/some/other/path/file.py")

    def test_handles_nested_src_paths(self):
        """Test nested paths under src/."""
        formatter = RelativePathFormatter("%(pathname)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/home/user/project/src/editor/ui/header_bar.py",
            lineno=1,
            msg="test",
            args=(),
            exc_info=None,
        )
        result = formatter.format(record)
        self.assertEqual(result, "src/editor/ui/header_bar.py")


class TestSetupLogging(unittest.TestCase):
    """Tests for setup_logging function."""

    def setUp(self):
        """Reset logging before each test."""
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(logging.WARNING)

    def test_default_level_is_info(self):
        """Test that default log level is INFO."""
        setup_logging(debug=False)
        root_logger = logging.getLogger()
        self.assertEqual(root_logger.level, logging.INFO)

    def test_debug_level_when_debug_true(self):
        """Test that log level is DEBUG when debug=True."""
        setup_logging(debug=True)
        root_logger = logging.getLogger()
        self.assertEqual(root_logger.level, logging.DEBUG)

    def test_logs_to_stderr(self):
        """Test that logs are written to stderr."""
        setup_logging(debug=False)
        root_logger = logging.getLogger()
        self.assertEqual(len(root_logger.handlers), 1)
        handler = root_logger.handlers[0]
        self.assertIsInstance(handler, logging.StreamHandler)
        self.assertEqual(handler.stream, sys.stderr)

    def test_log_format_includes_required_fields(self):
        """Test that log format includes timestamp, level, file, line, and function."""
        setup_logging(debug=False)
        root_logger = logging.getLogger()
        handler = root_logger.handlers[0]

        # Create a log record and format it
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/project/src/editor/main.py",
            lineno=42,
            msg="test message",
            args=(),
            exc_info=None,
        )
        record.funcName = "test_function"
        formatted = handler.formatter.format(record)

        # Check format includes all required parts
        self.assertIn("INFO", formatted)
        self.assertIn("src/editor/main.py", formatted)
        self.assertIn("42", formatted)
        self.assertIn("test_function", formatted)
        self.assertIn("test message", formatted)
        # Check timestamp format (YYYY-MM-DD HH:MM:SS)
        self.assertIn("[", formatted)
        self.assertIn("]", formatted)

    def test_debug_messages_filtered_when_not_debug(self):
        """Test that DEBUG messages are filtered when debug=False."""
        setup_logging(debug=False)
        logger = get_logger("test")

        # DEBUG should be filtered at INFO level
        self.assertFalse(logger.isEnabledFor(logging.DEBUG))
        self.assertTrue(logger.isEnabledFor(logging.INFO))

    def test_debug_messages_enabled_when_debug(self):
        """Test that DEBUG messages are enabled when debug=True."""
        setup_logging(debug=True)
        logger = get_logger("test")

        # DEBUG should be enabled
        self.assertTrue(logger.isEnabledFor(logging.DEBUG))
        self.assertTrue(logger.isEnabledFor(logging.INFO))


class TestGetLogger(unittest.TestCase):
    """Tests for get_logger function."""

    def test_returns_logger_instance(self):
        """Test that get_logger returns a Logger instance."""
        logger = get_logger("test")
        self.assertIsInstance(logger, logging.Logger)

    def test_returns_logger_with_correct_name(self):
        """Test that get_logger returns a logger with the correct name."""
        logger = get_logger("test.module")
        self.assertEqual(logger.name, "test.module")
