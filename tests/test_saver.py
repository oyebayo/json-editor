"""Tests for editor.json.saver."""

import json
import os
import tempfile

from editor.json.saver import save_file

SAMPLE_DATA = {"name": "test", "version": "1.0", "items": [1, 2, 3]}


class TestSaveFile:
    """Tests for save_file."""

    def test_saves_valid_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name

        try:
            meta = save_file(path, SAMPLE_DATA)
            assert meta["path"] == path
            assert meta["filename"] == os.path.basename(path)
            assert meta["file_size"] > 0

            with open(path, "r") as f:
                loaded = json.loads(f.read())
            assert loaded == SAMPLE_DATA
        finally:
            os.unlink(path)

    def test_overwrites_existing_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"old": "data"}')
            path = f.name

        try:
            save_file(path, SAMPLE_DATA)
            with open(path, "r") as f:
                loaded = json.loads(f.read())
            assert loaded == SAMPLE_DATA
        finally:
            os.unlink(path)

    def test_creates_new_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "new_file.json")
            assert not os.path.exists(path)

            meta = save_file(path, SAMPLE_DATA)
            assert os.path.exists(path)
            assert meta["filename"] == "new_file.json"

    def test_unicode_content(self):
        data = {"emoji": "🎉", "chinese": "中文", "arabic": "عربي"}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name

        try:
            save_file(path, data)
            with open(path, "r", encoding="utf-8") as f:
                loaded = json.loads(f.read())
            assert loaded == data
        finally:
            os.unlink(path)

    def test_file_size_matches(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name

        try:
            meta = save_file(path, SAMPLE_DATA)
            actual_size = os.path.getsize(path)
            assert meta["file_size"] == actual_size
        finally:
            os.unlink(path)
