import json
import os
import urllib.error
import urllib.request

from editor.logger import get_logger

logger = get_logger(__name__)

ALLOWED_MIME_TYPES = ("application/json", "text/json", "+json")


class JsonLoadError(Exception):
    """Raised when JSON loading or parsing fails."""


class UrlLoadError(Exception):
    """Raised when fetching a URL fails."""


class MimeTypeError(Exception):
    """Raised when the Content-Type is not JSON."""


def load_file(path):
    """Read and parse a JSON file. Returns the parsed data."""
    logger.info(f"Loading file: {path}")

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed for {path}: {e}")
        raise JsonLoadError(f"Failed to parse JSON file:\n{e}") from e

    file_size = os.path.getsize(path)
    filename = os.path.basename(path)
    logger.info(f"Successfully loaded file: {filename}")

    return data, {"path": path, "filename": filename, "file_size": file_size}


def load_url(url):
    """Fetch and parse JSON from a URL. Returns the parsed data."""
    logger.info(f"Fetching URL: {url}")

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "JSON-Editor/1.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            content_type = response.headers.get("Content-Type", "")
            content = response.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        logger.error(f"HTTP error fetching {url}: {e}")
        raise UrlLoadError(f"Failed to fetch URL:\n{e}") from e
    except urllib.error.URLError as e:
        logger.error(f"URL error fetching {url}: {e}")
        raise UrlLoadError(f"Failed to fetch URL:\n{e}") from e

    if content_type and not any(t in content_type for t in ALLOWED_MIME_TYPES):
        logger.error(f"Invalid MIME type for URL {url}: {content_type}")
        raise MimeTypeError(
            f"URL did not return JSON.\nContent-Type: {content_type}"
        )

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed for URL {url}: {e}")
        raise JsonLoadError(f"Failed to parse JSON from URL:\n{e}") from e

    display_url = url if len(url) <= 40 else "..." + url[-37:]
    logger.info(f"Successfully loaded URL: {url}")

    return data, {"url": url, "display_url": display_url}
