"""Top-level package for handy-utils."""

__author__ = """Akhil Vempali"""
__email__ = "vempaliakhil96@gmail.com"
__version__ = "0.3.0"

import os

import logfire
from loguru import logger

LOGFIRE_API_KEY = os.getenv("HANDY_UTILS_LOGFIRE_API_KEY", None)

if LOGFIRE_API_KEY is None:
    logger.warning(
        "HANDY_UTILS_LOGFIRE_API_KEY is not set. Logging will not be sent to Logfire. "
        "Set the environment variable to enable logging."
    )

logfire.configure(
    token=LOGFIRE_API_KEY,
    scrubbing=False,
    service_name="handy-utils",
    console=False,
)
logfire.instrument_pydantic_ai()
