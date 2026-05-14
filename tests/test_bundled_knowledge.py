"""Verifies the bundled knowledge file ships with the package and loads correctly."""

import os

from openreview_mcp.knowledge import load_knowledge


def test_bundled_knowledge_file_exists():
    """The package must ship with knowledge_files/llm.txt."""
    import openreview_mcp
    pkg_dir = os.path.dirname(os.path.abspath(openreview_mcp.__file__))
    bundled_dir = os.path.join(pkg_dir, "knowledge_files")
    assert os.path.isfile(os.path.join(bundled_dir, "llm.txt"))


def test_bundled_knowledge_loads_non_empty():
    """Loading the bundled file must yield non-empty practice sections."""
    import openreview_mcp
    pkg_dir = os.path.dirname(os.path.abspath(openreview_mcp.__file__))
    bundled_dir = os.path.join(pkg_dir, "knowledge_files")

    kb = load_knowledge(os.path.join(bundled_dir, "llm.txt"))

    assert len(kb.practices) > 0, "Bundled llm.txt produced zero practice sections"
