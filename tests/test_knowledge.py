"""Tests for static knowledge parsing (llm.txt)."""

import os

import pytest

from openreview_mcp.knowledge import (
    load_knowledge,
    search_best_practices,
)


class TestLoadKnowledge:
    def test_parses_llm_txt_sections(self, llm_txt_path):
        kb = load_knowledge(llm_txt_path)
        # Fixture has 4 sections: Authentication, Content Structure, Conference Workflow, Anti-Patterns
        assert len(kb.practices) == 4
        assert "Authentication" in kb.practices
        assert "Content Structure" in kb.practices
        assert "Conference Workflow" in kb.practices
        assert "Anti-Patterns to Avoid" in kb.practices

    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            load_knowledge("/nonexistent/path/llm.txt")


@pytest.fixture(scope="module")
def kb():
    fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
    return load_knowledge(os.path.join(fixtures_dir, "llm.txt"))


class TestSearchBestPractices:
    def test_header_match(self, kb):
        result = search_best_practices("Authentication", kb)
        assert "Token auth" in result
        assert "username" in result.lower()

    def test_content_match(self, kb):
        result = search_best_practices("token", kb)
        assert len(result) > 0
        assert "token" in result.lower()

    def test_case_insensitive(self, kb):
        result = search_best_practices("AUTHENTICATION", kb)
        assert "Token auth" in result

    def test_no_match(self, kb):
        result = search_best_practices("zzz_nonexistent_zzz", kb)
        assert result == ""

    def test_header_ranked_above_content(self, kb):
        # "Authentication" is a header; "token" appears in content of Auth AND Anti-Patterns
        result = search_best_practices("Authentication", kb)
        # The Authentication section should come first
        lines = result.strip().split("\n")
        assert "Authentication" in lines[0]
