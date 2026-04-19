"""Shared test fixtures."""

import pytest
from src.db.database import get_engine, verify_database


@pytest.fixture(scope="session", autouse=True)
def ensure_database():
    """Ensure the Chinook database is loaded before any tests run."""
    engine = get_engine()
    assert engine is not None
    health = verify_database()
    assert health["status"] == "healthy"
    return engine
