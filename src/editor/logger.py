import logging
import sys


class RelativePathFormatter(logging.Formatter):
    """Custom formatter that strips the path to start from 'src/'."""

    def format(self, record):
        # Find the 'src/' part in the pathname and keep everything from 'src/' onwards
        if "src/" in record.pathname:
            # Split on 'src/' and keep 'src/' and everything after it
            parts = record.pathname.split("src/", 1)
            if len(parts) > 1:
                record.pathname = "src/" + parts[1]
        return super().format(record)


def setup_logging(debug=False):
    """Configure logging with the specified format and level.

    Args:
        debug: If True, set level to DEBUG; otherwise INFO
    """
    # Custom format matching requirements
    log_format = "[%(asctime)s] [%(levelname)s] %(pathname)s:%(lineno)d (%(funcName)s): %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Create formatter with relative paths
    formatter = RelativePathFormatter(log_format, datefmt=date_format)

    # Create handler for stderr
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()  # Remove any existing handlers
    root_logger.addHandler(handler)

    # Set level based on debug flag
    if debug:
        root_logger.setLevel(logging.DEBUG)
    else:
        root_logger.setLevel(logging.INFO)


def get_logger(name):
    """Get a logger instance with the given name.

    Args:
        name: Logger name (usually __name__ of the module)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
