import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db import Database  # noqa: E402


@pytest.fixture
def db(tmp_path):
    return Database(str(tmp_path / "test.db"))
