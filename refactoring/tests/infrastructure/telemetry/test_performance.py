"""Unit tests for performance profiling utilities."""

import time
from unittest.mock import MagicMock

import pytest
from refactoring.src.infrastructure.telemetry.performance import (
    PerformanceProfiler,
    PerformanceTimer,
    timed,
    timed_operation,
)
from refactoring.src.shared.logging import get_silent_logger


class TestPerformanceTimer:
    """Test PerformanceTimer class."""

    def test_initialization(self):
        """Test timer can be created."""
        logger = get_silent_logger("test")
        timer = PerformanceTimer("test_operation", logger)

        assert timer.operation_name == "test_operation"
        assert timer.logger == logger
        assert timer.log_level == "info"

    def test_custom_log_level(self):
        """Test timer can use custom log level."""
        logger = get_silent_logger("test")
        timer = PerformanceTimer("test_operation", logger, log_level="debug")

        assert timer.log_level == "debug"

    def test_start_records_time(self):
        """Test start() records start time."""
        logger = get_silent_logger("test")
        timer = PerformanceTimer("test_operation", logger)

        timer.start()

        assert timer._start_time is not None
        assert timer._start_time > 0

    def test_stop_calculates_duration(self):
        """Test stop() calculates duration correctly."""
        logger = get_silent_logger("test")
        timer = PerformanceTimer("test_operation", logger)

        timer.start()
        time.sleep(0.01)  # Sleep 10ms
        duration_ms = timer.stop()

        assert duration_ms >= 10  # Should be at least 10ms
        assert duration_ms < 100  # But not too long
        assert timer._end_time is not None

    def test_stop_without_start_warns(self):
        """Test stop() without start() logs warning."""
        logger = MagicMock()
        timer = PerformanceTimer("test_operation", logger)

        duration_ms = timer.stop()

        assert duration_ms == 0.0
        logger.warning.assert_called_once()

    def test_stop_with_context(self):
        """Test stop() includes additional context."""
        logger = MagicMock()
        timer = PerformanceTimer("test_operation", logger)

        timer.start()
        timer.stop(context={"items_processed": 100})

        # Check that info was called with context
        logger.info.assert_called_once()
        call_context = logger.info.call_args[1]["context"]
        assert "items_processed" in call_context
        assert call_context["items_processed"] == 100
        assert "duration_ms" in call_context

    def test_debug_log_level(self):
        """Test timer uses debug log level when specified."""
        logger = MagicMock()
        timer = PerformanceTimer("test_operation", logger, log_level="debug")

        timer.start()
        timer.stop()

        logger.debug.assert_called()


class TestTimedOperation:
    """Test timed_operation context manager."""

    def test_times_operation(self):
        """Test context manager times operation."""
        logger = get_silent_logger("test")

        with timed_operation("test_op", logger) as timer:
            time.sleep(0.01)  # Sleep 10ms

        # Timer should have completed
        assert timer._end_time is not None
        assert timer._start_time is not None

    def test_provides_timer_instance(self):
        """Test context manager provides timer."""
        logger = get_silent_logger("test")

        with timed_operation("test_op", logger) as timer:
            assert isinstance(timer, PerformanceTimer)
            assert timer.operation_name == "test_op"

    def test_logs_on_exit(self):
        """Test context manager logs on exit."""
        logger = MagicMock()

        with timed_operation("test_op", logger):
            pass

        # Should log completion
        logger.info.assert_called()
        call_context = logger.info.call_args[1]["context"]
        assert "duration_ms" in call_context

    def test_custom_context(self):
        """Test context manager includes custom context."""
        logger = MagicMock()

        with timed_operation("test_op", logger, context={"user": "alice"}):
            pass

        call_context = logger.info.call_args[1]["context"]
        assert "user" in call_context
        assert call_context["user"] == "alice"

    def test_times_even_on_exception(self):
        """Test context manager times operation even if exception occurs."""
        logger = MagicMock()

        with pytest.raises(ValueError), timed_operation("test_op", logger):
            raise ValueError("test error")

        # Should still log timing
        logger.info.assert_called()


class TestTimedDecorator:
    """Test @timed decorator."""

    def test_decorator_times_function(self):
        """Test decorator times function execution."""
        logger = MagicMock()

        @timed("user_validation")
        def validate_user(user_id: str, logger) -> bool:
            time.sleep(0.01)
            return True

        result = validate_user("alice", logger=logger)

        assert result is True
        logger.info.assert_called()
        call_context = logger.info.call_args[1]["context"]
        assert "duration_ms" in call_context

    def test_decorator_uses_function_name(self):
        """Test decorator uses function name when operation_name not provided."""
        logger = MagicMock()

        @timed()
        def process_data(data: dict, logger) -> None:
            pass

        process_data({"test": "data"}, logger=logger)

        # Should use function name "process_data"
        call_msg = logger.info.call_args[0][0]
        assert "process_data" in call_msg

    def test_decorator_with_keyword_logger(self):
        """Test decorator works with logger as keyword argument."""
        logger = MagicMock()

        @timed()
        def do_work(value: int, logger) -> int:
            return value * 2

        result = do_work(5, logger=logger)

        assert result == 10
        logger.info.assert_called()

    def test_decorator_with_instance_logger(self):
        """Test decorator finds logger from self._logger."""

        class Worker:
            def __init__(self):
                self._logger = MagicMock()

            @timed()
            def do_work(self) -> None:
                pass

        worker = Worker()
        worker.do_work()

        worker._logger.info.assert_called()

    def test_decorator_without_logger_still_works(self):
        """Test decorator doesn't break if no logger found."""

        @timed()
        def do_work(value: int) -> int:
            return value * 2

        # Should not raise, just skips timing
        result = do_work(5)
        assert result == 10


class TestPerformanceProfiler:
    """Test PerformanceProfiler class."""

    def test_initialization(self):
        """Test profiler can be created."""
        logger = get_silent_logger("test")
        profiler = PerformanceProfiler(logger)

        assert profiler.logger == logger
        assert profiler._timings == {}

    def test_time_records_duration(self):
        """Test time() context manager records duration."""
        logger = get_silent_logger("test")
        profiler = PerformanceProfiler(logger)

        with profiler.time("test_operation"):
            time.sleep(0.01)

        assert "test_operation" in profiler._timings
        assert len(profiler._timings["test_operation"]) == 1
        assert profiler._timings["test_operation"][0] >= 10  # At least 10ms

    def test_time_records_multiple_operations(self):
        """Test profiler records multiple different operations."""
        logger = get_silent_logger("test")
        profiler = PerformanceProfiler(logger)

        with profiler.time("op1"):
            time.sleep(0.01)

        with profiler.time("op2"):
            time.sleep(0.01)

        assert "op1" in profiler._timings
        assert "op2" in profiler._timings
        assert len(profiler._timings["op1"]) == 1
        assert len(profiler._timings["op2"]) == 1

    def test_time_records_repeated_operations(self):
        """Test profiler records multiple executions of same operation."""
        logger = get_silent_logger("test")
        profiler = PerformanceProfiler(logger)

        for _ in range(3):
            with profiler.time("test_operation"):
                time.sleep(0.01)

        assert "test_operation" in profiler._timings
        assert len(profiler._timings["test_operation"]) == 3

    def test_get_stats_empty(self):
        """Test get_stats() returns zeros for unknown operation."""
        logger = get_silent_logger("test")
        profiler = PerformanceProfiler(logger)

        stats = profiler.get_stats("unknown_operation")

        assert stats["count"] == 0
        assert stats["total_ms"] == 0.0
        assert stats["avg_ms"] == 0.0
        assert stats["min_ms"] == 0.0
        assert stats["max_ms"] == 0.0

    def test_get_stats_calculates_correctly(self):
        """Test get_stats() calculates statistics correctly."""
        logger = get_silent_logger("test")
        profiler = PerformanceProfiler(logger)

        # Manually add timings
        profiler._timings["test_op"] = [10.0, 20.0, 30.0]

        stats = profiler.get_stats("test_op")

        assert stats["count"] == 3
        assert stats["total_ms"] == 60.0
        assert stats["avg_ms"] == 20.0
        assert stats["min_ms"] == 10.0
        assert stats["max_ms"] == 30.0

    def test_log_summary_with_data(self):
        """Test log_summary() logs all recorded operations."""
        logger = MagicMock()
        profiler = PerformanceProfiler(logger)

        with profiler.time("op1"):
            time.sleep(0.01)

        with profiler.time("op2"):
            time.sleep(0.01)

        profiler.log_summary()

        logger.info.assert_called_once()
        call_msg = logger.info.call_args[0][0]
        call_context = logger.info.call_args[1]["context"]

        assert "performance.summary" in call_msg
        assert "operations" in call_context
        assert "op1" in call_context["operations"]
        assert "op2" in call_context["operations"]

    def test_log_summary_empty(self):
        """Test log_summary() handles empty profiler."""
        logger = MagicMock()
        profiler = PerformanceProfiler(logger)

        profiler.log_summary()

        logger.info.assert_called_once()
        call_msg = logger.info.call_args[0][0]
        assert "empty" in call_msg

    def test_clear_resets_timings(self):
        """Test clear() resets all timings."""
        logger = get_silent_logger("test")
        profiler = PerformanceProfiler(logger)

        with profiler.time("test_op"):
            pass

        assert len(profiler._timings) > 0

        profiler.clear()

        assert len(profiler._timings) == 0

    def test_time_even_on_exception(self):
        """Test time() records duration even if exception occurs."""
        logger = get_silent_logger("test")
        profiler = PerformanceProfiler(logger)

        with pytest.raises(ValueError), profiler.time("test_op"):
            time.sleep(0.01)
            raise ValueError("test error")

        # Should still have recorded the timing
        assert "test_op" in profiler._timings
        assert len(profiler._timings["test_op"]) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
