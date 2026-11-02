import logging
import requests
import app.constants.api as api_constants

logger = logging.getLogger(__name__)


def get_summary_overview() -> dict | None:
    """
    Fetch data freshness summary from the backend.
    Returns {"epmc": {...}, "github": {...}, "pypi": {...}} or None on failure.
    """
    try:
        resp = requests.get(api_constants.SUMMARY_OVERVIEW, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Failed to fetch summary overview: %s", exc)
        return None
