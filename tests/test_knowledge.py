"""Tests for static knowledge parsing (llm.txt + examples.md)."""

import os
import pytest
from openreview_mcp.knowledge import KnowledgeBase, load_knowledge, search_best_practices, search_examples, get_workflow


class TestLoadKnowledge:
    def test_parses_llm_txt_sections(self, llm_txt_path, examples_md_path):
        kb = load_knowledge(llm_txt_path, examples_md_path)
        # Fixture has 4 sections: Authentication, Content Structure, Conference Workflow, Anti-Patterns
        assert len(kb.practices) == 4
        assert "Authentication" in kb.practices
        assert "Content Structure" in kb.practices
        assert "Conference Workflow" in kb.practices
        assert "Anti-Patterns to Avoid" in kb.practices

    def test_parses_examples_md_sections(self, llm_txt_path, examples_md_path):
        kb = load_knowledge(llm_txt_path, examples_md_path)
        # Fixture has sections: Authentication, Notes, Conference Workflow
        # with subsections: Connect to production, Token-based auth, Submit a paper, etc.
        assert "Authentication" in kb.examples
        assert "Notes" in kb.examples
        assert "Conference Workflow" in kb.examples

    def test_missing_file_raises(self, examples_md_path):
        with pytest.raises(FileNotFoundError):
            load_knowledge("/nonexistent/path/llm.txt", examples_md_path)


@pytest.fixture(scope="module")
def kb():
    fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
    return load_knowledge(
        os.path.join(fixtures_dir, "llm.txt"),
        os.path.join(fixtures_dir, "examples.md"),
    )


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


class TestSearchExamples:
    def test_finds_code_blocks(self, kb):
        result = search_examples("submit paper", kb)
        assert "```python" in result
        assert "post_note_edit" in result

    def test_no_match(self, kb):
        result = search_examples("zzz_nonexistent_zzz", kb)
        assert result == ""


class TestGetWorkflow:
    def test_conference(self, kb):
        result = get_workflow("conference", kb)
        assert "Venue Request" in result
        assert "Deploy" in result
        # Should also include code examples
        assert "```python" in result

    def test_journal(self, kb):
        # Fixture doesn't have journal, should return empty or partial
        result = get_workflow("journal", kb)
        # No journal section in fixture, so empty
        assert result == ""

    def test_specific_stage(self, kb):
        result = get_workflow("review", kb)
        # Should match review-related content from both practices and examples
        assert len(result) > 0
