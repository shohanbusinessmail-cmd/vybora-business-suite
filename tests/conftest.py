"""Shared pytest fixtures: temp database, migrated schema, display prefs."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure src is importable without installation.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture()
def db(tmp_path):
    from vybora.data.db import Database
    from vybora.data.migrations import migrate

    database = Database(tmp_path / "test.db")
    migrate(database)
    yield database
    database.close()


@pytest.fixture()
def prefs():
    from vybora.core.formatting import DisplayPrefs

    return DisplayPrefs()
