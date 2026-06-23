import json
import os

from editor.logger import get_logger

logger = get_logger(__name__)


def save_file(path, data):
    """Write data as formatted JSON to a file."""
    logger.info(f"Saving file: {path}")

    content = json.dumps(data, indent=2, ensure_ascii=False)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
        f.write("\n")

    file_size = os.path.getsize(path)
    filename = os.path.basename(path)
    logger.info(f"Successfully saved file: {filename}")

    return {"path": path, "filename": filename, "file_size": file_size}
