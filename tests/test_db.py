import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cat_weather.database import Database


def test_timezone_roundtrip(tmp_path):
    db = Database(tmp_path / "db.sqlite")
    db.set_timezone(1, 3)
    assert db.get_timezone(1) == 3
