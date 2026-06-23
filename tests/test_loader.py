"""Unit tests for editor.json.loader."""

import io
import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from editor.json.loader import (
    JsonLoadError,
    MimeTypeError,
    UrlLoadError,
    load_file,
    load_url,
)

SAMPLE_JSON = {"name": "test", "version": "1.0"}
SAMPLE_DIR = os.path.dirname(__file__)
SAMPLE_PATH = os.path.join(SAMPLE_DIR, "test.json")


class TestLoadFile(unittest.TestCase):
    """Tests for load_file."""

    def test_loads_valid_json(self):
        data, meta = load_file(SAMPLE_PATH)
        self.assertIn("object_arrays", data)
        self.assertEqual(meta["path"], SAMPLE_PATH)
        self.assertEqual(meta["filename"], "test.json")
        self.assertIn("file_size", meta)

    def test_invalid_json_raises_error(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write("{bad json}")
            f.flush()
            path = f.name
        try:
            with self.assertRaises(JsonLoadError):
                load_file(path)
        finally:
            os.unlink(path)

    def test_missing_file_raises_error(self):
        with self.assertRaises(FileNotFoundError):
            load_file("/nonexistent/path.json")

    def test_meta_contains_file_size(self):
        _, meta = load_file(SAMPLE_PATH)
        self.assertGreater(meta["file_size"], 0)


class TestLoadUrl(unittest.TestCase):
    """Tests for load_url."""

    def _mock_response(self, content, content_type="application/json"):
        resp = MagicMock()
        resp.headers = {"Content-Type": content_type}
        resp.read.return_value = content.encode("utf-8")
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        return resp

    @patch("editor.json.loader.urllib.request.urlopen")
    def test_loads_valid_json_from_url(self, mock_urlopen):
        mock_urlopen.return_value = self._mock_response(json.dumps(SAMPLE_JSON))
        data, meta = load_url("https://example.com/data.json")
        self.assertEqual(data, SAMPLE_JSON)
        self.assertEqual(meta["url"], "https://example.com/data.json")
        self.assertIn("display_url", meta)

    @patch("editor.json.loader.urllib.request.urlopen")
    def test_rejects_non_json_mime_type(self, mock_urlopen):
        mock_urlopen.return_value = self._mock_response(
            "<html>not json</html>", content_type="text/html"
        )
        with self.assertRaises(MimeTypeError):
            load_url("https://example.com/page.html")

    @patch("editor.json.loader.urllib.request.urlopen")
    def test_accepts_json_subtype(self, mock_urlopen):
        mock_urlopen.return_value = self._mock_response(
            json.dumps(SAMPLE_JSON), content_type="application/vnd.api+json"
        )
        data, meta = load_url("https://example.com/api")
        self.assertEqual(data, SAMPLE_JSON)

    @patch("editor.json.loader.urllib.request.urlopen")
    def test_accepts_missing_content_type(self, mock_urlopen):
        mock_urlopen.return_value = self._mock_response(
            json.dumps(SAMPLE_JSON), content_type=""
        )
        data, meta = load_url("https://example.com/data.json")
        self.assertEqual(data, SAMPLE_JSON)

    @patch("editor.json.loader.urllib.request.urlopen")
    def test_invalid_json_from_url_raises_error(self, mock_urlopen):
        mock_urlopen.return_value = self._mock_response("{bad}")
        with self.assertRaises(JsonLoadError):
            load_url("https://example.com/bad.json")

    @patch("editor.json.loader.urllib.request.urlopen")
    def test_url_error_raises_error(self, mock_urlopen):
        import urllib.error

        mock_urlopen.side_effect = urllib.error.URLError("connection refused")
        with self.assertRaises(UrlLoadError):
            load_url("https://example.com/fail")

    def test_display_url_truncates_long_urls(self):
        long_url = "https://example.com/" + "a" * 50
        with patch("editor.json.loader.urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = self._mock_response(json.dumps(SAMPLE_JSON))
            _, meta = load_url(long_url)
        self.assertTrue(meta["display_url"].startswith("..."))
        self.assertLessEqual(len(meta["display_url"]), 40)


if __name__ == "__main__":
    unittest.main()
