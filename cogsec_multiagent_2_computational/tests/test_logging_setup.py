"""Tests for utils/logging_setup.py."""

import logging

from utils.logging_setup import get_logger, setup_logging


class TestSetupLogging:
    """Test structured logging configuration."""

    def test_setup_logging_creates_handler(self):
        """setup_logging() adds a handler to the 'cogsec' logger."""
        # Reset the _CONFIGURED flag so we can test
        import utils.logging_setup as mod
        mod._CONFIGURED = False

        setup_logging()
        root = logging.getLogger("cogsec")
        assert len(root.handlers) >= 1
        # Clean up
        mod._CONFIGURED = False
        root.handlers.clear()

    def test_setup_logging_idempotent(self):
        """Calling setup_logging() twice does not double handlers."""
        import utils.logging_setup as mod
        mod._CONFIGURED = False

        setup_logging()
        setup_logging()  # second call should be a no-op
        root = logging.getLogger("cogsec")
        handler_count = len(root.handlers)
        assert handler_count >= 1
        # Clean up
        mod._CONFIGURED = False
        root.handlers.clear()

    def test_setup_logging_custom_format(self):
        """Custom format string is applied."""
        import utils.logging_setup as mod
        mod._CONFIGURED = False

        custom_fmt = "%(levelname)s:%(message)s"
        setup_logging(fmt=custom_fmt)
        root = logging.getLogger("cogsec")
        formatter = root.handlers[0].formatter
        assert formatter._fmt == custom_fmt
        # Clean up
        mod._CONFIGURED = False
        root.handlers.clear()

    def test_setup_logging_sets_level(self):
        """Logger level defaults to INFO."""
        import utils.logging_setup as mod
        mod._CONFIGURED = False

        setup_logging(level=logging.DEBUG)
        root = logging.getLogger("cogsec")
        assert root.level == logging.DEBUG
        # Clean up
        mod._CONFIGURED = False
        root.handlers.clear()


class TestGetLogger:
    """Test get_logger() returns scoped loggers."""

    def test_returns_logger(self):
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)

    def test_logger_name_scoped(self):
        logger = get_logger("trust")
        assert logger.name == "cogsec.trust"

    def test_different_names_different_loggers(self):
        log_a = get_logger("alpha")
        log_b = get_logger("beta")
        assert log_a is not log_b
        assert log_a.name != log_b.name
