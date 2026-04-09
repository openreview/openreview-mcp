"""Tests for live introspection of the openreview-py library."""

import pytest
from openreview_mcp.introspection import introspect_library, search_methods, get_method_details


@pytest.fixture(scope="module")
def cache():
    return introspect_library()


class TestIntrospectLibrary:
    def test_returns_all_target_classes(self, cache):
        expected_classes = [
            "OpenReviewClient",
            "Client",
            "Note",
            "Invitation",
            "Edge",
            "Group",
            "Tag",
            "Edit",
            "Profile",
            "Venue",
        ]
        for cls_name in expected_classes:
            assert cls_name in cache, f"Missing class: {cls_name}"

    def test_captures_method_signatures(self, cache):
        methods = cache["OpenReviewClient"]
        assert "post_note_edit" in methods
        params = methods["post_note_edit"]["params"]
        param_names = [p["name"] for p in params]
        assert "invitation" in param_names
        assert "signatures" in param_names
        assert "note" in param_names
        assert "await_process" in param_names

    def test_captures_docstrings(self, cache):
        # OpenReviewClient.__init__ has a docstring
        methods = cache["OpenReviewClient"]
        init_info = methods["__init__"]
        assert init_info["docstring"] is not None
        assert len(init_info["docstring"]) > 0

    def test_skips_private_methods(self, cache):
        methods = cache["OpenReviewClient"]
        for method_name in methods:
            assert not method_name.startswith("_") or method_name == "__init__", (
                f"Private method included: {method_name}"
            )


class TestSearchMethods:
    def test_exact_name_match(self, cache):
        results = search_methods("post_note_edit", None, cache)
        assert len(results) > 0
        assert results[0]["name"] == "post_note_edit"

    def test_partial_name_match(self, cache):
        results = search_methods("post_note", None, cache)
        names = [r["name"] for r in results]
        assert "post_note_edit" in names

    def test_docstring_match(self, cache):
        # "baseurl" appears in OpenReviewClient.__init__ docstring
        results = search_methods("baseurl", None, cache)
        assert len(results) > 0

    def test_class_filter(self, cache):
        results = search_methods("setup", "Venue", cache)
        for r in results:
            assert r["class_name"] == "Venue"

    def test_max_results(self, cache):
        results = search_methods("get", None, cache)
        assert len(results) <= 15

    def test_relevance_ordering(self, cache):
        results = search_methods("post_note_edit", None, cache)
        # Exact match should be first
        assert results[0]["name"] == "post_note_edit"

    def test_no_match_returns_empty(self, cache):
        results = search_methods("zzz_nonexistent_zzz", None, cache)
        assert results == []


class TestGetMethodDetails:
    def test_returns_full_info(self, cache):
        results = get_method_details("post_note_edit", cache)
        assert len(results) > 0
        detail = results[0]
        assert detail["class_name"] == "OpenReviewClient"
        assert detail["name"] == "post_note_edit"
        assert "params" in detail
        assert "signature" in detail

    def test_partial_match(self, cache):
        results = get_method_details("get_all", cache)
        names = [r["name"] for r in results]
        assert "get_all_notes" in names

    def test_no_match_returns_empty(self, cache):
        results = get_method_details("zzz_nonexistent_zzz", cache)
        assert results == []
