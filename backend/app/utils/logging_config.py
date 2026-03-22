import logging
import sys

from pythonjsonlogger import jsonlogger


class CorrelationFilter(logging.Filter):
    """Inject the current correlation ID into every log record."""

    def filter(self, record):
        from app.middleware.correlation import get_correlation_id

        record.correlation_id = get_correlation_id() or "-"
        return True


def setup_logging(level: str = "INFO"):
    """Configure structured JSON logging for production."""
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(correlation_id)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level", "name": "logger"},
    )
    handler.setFormatter(formatter)
    handler.addFilter(CorrelationFilter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Quiet noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
