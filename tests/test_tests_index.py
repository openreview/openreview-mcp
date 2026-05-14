"""Unit tests for the openreview-py test-suite index."""

import os

import pytest

from openreview_mcp.tests_index import (
    build_test_index,
    format_test_results,
    search_test_index,
)


FAKE_TESTS_DIR = os.path.join(
    os.path.dirname(__file__), "fixtures", "fake_tests"
)


@pytest.fixture(scope="module")
def index():
    idx = build_test_index(FAKE_TESTS_DIR)
    assert idx is not None
    return idx


class TestBuildTestIndex:
    def test_returns_none_for_missing_dir(self, tmp_path):
        assert build_test_index(str(tmp_path / "nope")) is None

    def test_excludes_selenium_tainted_files(self, index):
        for s in index.snippets:
            assert "selenium" not in s.file, (
                f"selenium-tainted file slipped through: {s.file}"
            )

    def test_indexes_class_methods_and_top_level(self, index):
        names = {(s.class_name, s.func_name) for s in index.snippets}
        assert ("TestConferenceDecisions", "test_post_decisions") in names
        assert ("TestConferenceDecisions", "test_post_meta_review") in names
        assert (None, "test_post_submission") in names
        assert (None, "test_long_workflow") in names

    def test_captures_arg_names(self, index):
        target = next(
            s for s in index.snippets if s.func_name == "test_post_decisions"
        )
        assert target.arg_names == ["self", "client", "helpers", "openreview_client"]

    def test_extracts_string_literal_tokens(self, index):
        target = next(
            s for s in index.snippets if s.func_name == "test_post_decisions"
        )
        # Invitation ID substrings get tokenized
        assert "decision" in target.tokens
        assert "conf25" in target.tokens
        assert "program_chairs" in target.tokens or "chairs" in target.tokens

    def test_extracts_helpers_methods(self, index):
        assert "create_user" in index.helpers_methods
        assert "await_queue_edit" in index.helpers_methods
        # Private methods are excluded
        assert "_private_helper" not in index.helpers_methods

    def test_postings_built(self, index):
        # 'decision' should map to the decisions test at minimum
        decision_idxs = index.postings.get("decision", [])
        decision_names = {index.snippets[i].func_name for i in decision_idxs}
        assert "test_post_decisions" in decision_names


class TestSearchTestIndex:
    def test_ranks_function_name_match_highest(self, index):
        results = search_test_index("post_decisions", index, max_results=5)
        assert results
        assert results[0]["snippet"].func_name == "test_post_decisions"

    def test_returns_empty_for_no_match(self, index):
        results = search_test_index("zzz_nonexistent_zzz", index)
        assert results == []

    def test_respects_max_results_cap(self, index):
        results = search_test_index("post", index, max_results=1)
        assert len(results) == 1

    def test_stopword_query_returns_empty(self, index):
        # Pure stopwords yield no usable terms.
        results = search_test_index("self test", index)
        assert results == []


class TestFormatTestResults:
    def test_empty_results_message(self, index):
        out = format_test_results([], index.helpers_methods, index.tests_dir)
        assert "No matching tests" in out

    def test_renders_file_and_line_refs(self, index):
        results = search_test_index("post_decisions", index, max_results=2)
        out = format_test_results(
            results, index.helpers_methods, index.tests_dir
        )
        assert "test_clean_conference.py:L" in out
        assert "TestConferenceDecisions.test_post_decisions" in out

    def test_renders_fixtures_preamble(self, index):
        results = search_test_index("post_decisions", index, max_results=1)
        out = format_test_results(
            results, index.helpers_methods, index.tests_dir
        )
        # 'self' is stripped; remaining args appear.
        assert "# fixtures: client, helpers, openreview_client" in out

    def test_appends_helpers_methods_when_body_references_helpers(self, index):
        results = search_test_index("post_decisions", index, max_results=1)
        out = format_test_results(
            results, index.helpers_methods, index.tests_dir
        )
        assert "conftest Helpers methods available" in out
        assert "await_queue_edit" in out

    def test_omits_helpers_footer_when_body_has_no_helpers_ref(self, index):
        results = search_test_index("test_post_meta_review", index, max_results=1)
        # This test method does NOT call helpers.* so the footer should be suppressed.
        # Note: result is selected by name, body is rendered without 'helpers.'
        out = format_test_results(
            results, index.helpers_methods, index.tests_dir
        )
        assert "conftest Helpers methods available" not in out

    def test_truncates_long_method_body(self, index):
        results = search_test_index("long_workflow", index, max_results=1)
        out = format_test_results(
            results, index.helpers_methods, index.tests_dir
        )
        assert "lines elided" in out
        # End of method must still appear (last-20 tail)
        assert "longwf-end-3" in out


class TestMalformedFile:
    def test_skips_unparseable_file(self, tmp_path):
        good = tmp_path / "test_good.py"
        good.write_text("def test_alpha():\n    pass\n")
        bad = tmp_path / "test_bad.py"
        bad.write_text("def test_broken(:\n    pass\n")  # syntax error
        idx = build_test_index(str(tmp_path))
        assert idx is not None
        names = {s.func_name for s in idx.snippets}
        assert names == {"test_alpha"}
