"""Verifies the bundled knowledge files ship with the package and load correctly."""

import os

from openreview_mcp.knowledge import load_knowledge


def test_bundled_knowledge_files_exist():
    """The package must ship with knowledge_files/llm.txt and examples.md."""
    import openreview_mcp
    pkg_dir = os.path.dirname(os.path.abspath(openreview_mcp.__file__))
    bundled_dir = os.path.join(pkg_dir, "knowledge_files")
    assert os.path.isfile(os.path.join(bundled_dir, "llm.txt"))
    assert os.path.isfile(os.path.join(bundled_dir, "examples.md"))


def test_bundled_knowledge_loads_non_empty():
    """Loading the bundled files must yield non-empty practices and examples."""
    import openreview_mcp
    pkg_dir = os.path.dirname(os.path.abspath(openreview_mcp.__file__))
    bundled_dir = os.path.join(pkg_dir, "knowledge_files")

    kb = load_knowledge(
        os.path.join(bundled_dir, "llm.txt"),
        os.path.join(bundled_dir, "examples.md"),
    )

    assert len(kb.practices) > 0, "Bundled llm.txt produced zero practice sections"
    assert len(kb.examples) > 0, "Bundled examples.md produced zero example sections"
