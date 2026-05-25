"""Small import smoke-check utility for the FastAPI application."""

import logging
import os
import sys

logger = logging.getLogger(__name__)


def main() -> None:
    """Import the backend application and fail loudly if startup imports are broken."""
    sys.path.append(os.getcwd())
    try:
        from backend.main import app  # noqa: F401
    except Exception:
        logger.exception("Unable to import backend.main")
        raise
    logger.info("backend.main imported successfully")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    main()
