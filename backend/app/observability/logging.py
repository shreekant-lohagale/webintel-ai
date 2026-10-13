
import json
import logging
import os
from datetime import datetime, timezone


STANDARD_FIELDS = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
    "taskName",
}


class JsonFormatter(logging.Formatter):

    def format(self, record):
        payload = {
            "timestamp": datetime.fromtimestamp(
                record.created,
                tz=timezone.utc,
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if (
                key not in STANDARD_FIELDS
                and not key.startswith("_")
            ):
                payload[key] = value

        return json.dumps(
            payload,
            ensure_ascii=False,
            default=str,
        )


def configure_logging():
    level_name = os.getenv(
        "WEBINTEL_LOG_LEVEL",
        "INFO",
    ).upper()

    level = getattr(
        logging,
        level_name,
        logging.INFO,
    )

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    logger = logging.getLogger("webintel")
    logger.setLevel(level)

    # Avoid duplicate handlers on app reloads.
    for existing in logger.handlers[:]:
        logger.removeHandler(existing)

    logger.addHandler(handler)
    logger.propagate = False

    return logger
