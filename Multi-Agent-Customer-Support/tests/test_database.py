"""Tests for the database module."""

import json
import pytest
from src.db.database import run_query_safe, normalize_phone, verify_database


class TestRunQuerySafe:
    def test_basic_select(self):
        result = run_query_safe("SELECT COUNT(*) AS cnt FROM Customer;")
        data = json.loads(result)
        assert len(data) == 1
        assert data[0]["cnt"] == 59

    def test_parameterized_query(self):
        result = run_query_safe(
            "SELECT FirstName FROM Customer WHERE CustomerId = :cid",
            {"cid": 1},
        )
        data = json.loads(result)
        assert len(data) == 1
        assert data[0]["FirstName"] is not None

    def test_empty_result(self):
        result = run_query_safe(
            "SELECT * FROM Customer WHERE CustomerId = :cid",
            {"cid": 99999},
        )
        assert result == "[]"

    def test_returns_valid_json(self):
        result = run_query_safe("SELECT AlbumId, Title FROM Album LIMIT 3;")
        data = json.loads(result)
        assert isinstance(data, list)
        assert len(data) == 3
        assert "AlbumId" in data[0]
        assert "Title" in data[0]


class TestNormalizePhone:
    def test_international_format(self):
        assert normalize_phone("+1 (555) 123-4567") == "+15551234567"

    def test_domestic_digits(self):
        assert normalize_phone("5551234567") == "5551234567"

    def test_with_dashes(self):
        assert normalize_phone("555-123-4567") == "5551234567"

    def test_empty_string(self):
        assert normalize_phone("") == ""

    def test_none_input(self):
        assert normalize_phone(None) == ""

    def test_plus_prefix_preserved(self):
        assert normalize_phone("+55 (12) 3923-5555") == "+551239235555"


class TestVerifyDatabase:
    def test_returns_healthy(self):
        result = verify_database()
        assert result["status"] == "healthy"
        assert result["tables"] > 0
