"""Tests for MCP tools — calls underlying tool functions directly."""

from openreview_mcp.server import search_api, get_method_signature, get_best_practices, get_code_example, get_workflow_guide


def test_search_api_returns_results():
    text = search_api(query="post_note")
    assert "post_note_edit" in text


def test_search_api_with_class_filter():
    text = search_api(query="setup", class_name="Venue")
    # All results should be from Venue class
    assert "Venue" in text
    assert "OpenReviewClient" not in text


def test_get_method_signature_returns_details():
    text = get_method_signature(method_name="post_note_edit")
    assert "post_note_edit" in text
    assert "invitation" in text
    assert "signatures" in text
    assert "await_process" in text


def test_get_best_practices_returns_section():
    text = get_best_practices(topic="authentication")
    assert "token" in text.lower()


def test_get_code_example_returns_snippet():
    text = get_code_example(operation="submit paper")
    assert "post_note_edit" in text
    assert "```python" in text


def test_get_workflow_guide_conference():
    text = get_workflow_guide(workflow_type="conference")
    assert "Venue Request" in text or "Deploy" in text


def test_get_workflow_guide_journal():
    text = get_workflow_guide(workflow_type="journal")
    assert "Submit" in text or "Review" in text
