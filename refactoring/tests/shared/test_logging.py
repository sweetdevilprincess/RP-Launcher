"""Unit tests for shared logging utilities."""

import logging
from unittest.mock import patch

import pytest
from refactoring.src.shared.logging import (
    PythonLogger,
    SimpleLogger,
    get_logger,
    get_silent_logger,
)


class TestSimpleLogger:
    """Test SimpleLogger (no-op logger for testing)."""

    def test_initialization(self):
        """Test logger can be created with a name."""
        logger = SimpleLogger("test_module")
        assert logger.name == "test_module"

    def test_debug_does_nothing(self):
        """Test debug() is a no-op."""
        logger = SimpleLogger("test")
        # Should not raise, should do nothing
        logger.debug("test message")
        logger.debug("test message", context={"key": "value"})

    def test_info_does_nothing(self):
        """Test info() is a no-op."""
        logger = SimpleLogger("test")
        logger.info("test message")
        logger.info("test message", context={"key": "value"})

    def test_warning_does_nothing(self):
        """Test warning() is a no-op."""
        logger = SimpleLogger("test")
        logger.warning("test message")
        logger.warning("test message", context={"key": "value"})

    def test_error_does_nothing(self):
        """Test error() is a no-op."""
        logger = SimpleLogger("test")
        logger.error("test message")
        logger.error("test message", context={"key": "value"})

    def test_exception_does_nothing(self):
        """Test exception() is a no-op."""
        logger = SimpleLogger("test")
        logger.exception("test message")
        logger.exception("test message", context={"key": "value"})
        logger.exception("test message", exc=ValueError("test"))


class TestPythonLogger:
    """Test PythonLogger (production logger)."""

    def test_initialization(self):
        """Test logger creates underlying logging.Logger."""
        logger = PythonLogger("test_module")
        assert logger._logger.name == "test_module"

    def test_debug_logs_message(self):
        """Test debug() calls logging.debug()."""
        logger = PythonLogger("test")
        with patch.object(logger._logger, "debug") as mock_debug:
            logger.debug("test message")
            mock_debug.assert_called_once_with("test message")

    def test_debug_with_context(self):
        """Test debug() formats context as JSON."""
        logger = PythonLogger("test")
        with patch.object(logger._logger, "debug") as mock_debug:
            logger.debug("test message", context={"user": "alice", "count": 42})
            call_args = mock_debug.call_args[0][0]
            assert "test message" in call_args
            assert "context=" in call_args
            assert "alice" in call_args
            assert "42" in call_args

    def test_info_logs_message(self):
        """Test info() calls logging.info()."""
        logger = PythonLogger("test")
        with patch.object(logger._logger, "info") as mock_info:
            logger.info("operation completed")
            mock_info.assert_called_once_with("operation completed")

    def test_info_with_context(self):
        """Test info() formats context."""
        logger = PythonLogger("test")
        with patch.object(logger._logger, "info") as mock_info:
            logger.info("event", context={"status": "success"})
            call_args = mock_info.call_args[0][0]
            assert "event" in call_args
            assert "success" in call_args

    def test_warning_logs_message(self):
        """Test warning() calls logging.warning()."""
        logger = PythonLogger("test")
        with patch.object(logger._logger, "warning") as mock_warning:
            logger.warning("deprecated feature used")
            mock_warning.assert_called_once_with("deprecated feature used")

    def test_error_logs_message(self):
        """Test error() calls logging.error()."""
        logger = PythonLogger("test")
        with patch.object(logger._logger, "error") as mock_error:
            logger.error("operation failed")
            mock_error.assert_called_once_with("operation failed")

    def test_exception_without_exc(self):
        """Test exception() calls logging.exception() without exc_info."""
        logger = PythonLogger("test")
        with patch.object(logger._logger, "exception") as mock_exception:
            logger.exception("error occurred")
            mock_exception.assert_called_once()
            assert mock_exception.call_args[0][0] == "error occurred"

    def test_exception_with_exc(self):
        """Test exception() includes exc_info when provided."""
        logger = PythonLogger("test")
        exc = ValueError("test error")
        with patch.object(logger._logger, "exception") as mock_exception:
            logger.exception("error occurred", exc=exc)
            mock_exception.assert_called_once()
            # Check that exc_info was passed
            assert "exc_info" in mock_exception.call_args[1]
            assert mock_exception.call_args[1]["exc_info"] == exc

    def test_context_serialization_handles_non_json(self):
        """Test context serialization handles non-JSON-serializable data."""
        logger = PythonLogger("test")

        # Object that can't be JSON serialized
        class NonSerializable:
            pass

        obj = NonSerializable()

        with patch.object(logger._logger, "info") as mock_info:
            logger.info("test", context={"obj": obj})
            call_args = mock_info.call_args[0][0]
            # Should fall back to str() representation
            assert "test" in call_args
            assert "context=" in call_args

    def test_empty_context_not_included(self):
        """Test that empty context is not included in message."""
        logger = PythonLogger("test")
        with patch.object(logger._logger, "info") as mock_info:
            logger.info("test message", context={})
            mock_info.assert_called_once_with("test message")

    def test_none_context_not_included(self):
        """Test that None context is not included in message."""
        logger = PythonLogger("test")
        with patch.object(logger._logger, "info") as mock_info:
            logger.info("test message", context=None)
            mock_info.assert_called_once_with("test message")


class TestGetLogger:
    """Test get_logger() function."""

    def test_returns_python_logger(self):
        """Test get_logger() returns PythonLogger instance."""
        logger = get_logger("test_module")
        assert isinstance(logger, PythonLogger)

    def test_creates_unique_loggers(self):
        """Test get_logger() creates separate logger for each name."""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")

        assert logger1._logger.name == "module1"
        assert logger2._logger.name == "module2"

    def test_logger_respects_logging_config(self):
        """Test logger respects logging configuration."""
        # Configure logging to WARNING level
        logging.basicConfig(level=logging.WARNING)

        logger = get_logger("test")

        # DEBUG should not be logged
        with patch.object(logger._logger, "debug") as mock_debug:
            logger.debug("debug message")
            mock_debug.assert_called_once()  # Called but won't output

        # WARNING should be logged
        with patch.object(logger._logger, "warning") as mock_warning:
            logger.warning("warning message")
            mock_warning.assert_called_once()


class TestGetSilentLogger:
    """Test get_silent_logger() function."""

    def test_returns_simple_logger(self):
        """Test get_silent_logger() returns SimpleLogger instance."""
        logger = get_silent_logger("test_module")
        assert isinstance(logger, SimpleLogger)

    def test_logger_does_nothing(self):
        """Test silent logger produces no output."""
        logger = get_silent_logger("test")

        # None of these should raise or produce output
        logger.debug("test")
        logger.info("test")
        logger.warning("test")
        logger.error("test")
        logger.exception("test")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
