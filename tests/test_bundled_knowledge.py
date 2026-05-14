"""Verifies the bundled knowledge file ships with the package and loads correctly."""

import os

from openreview_mcp.knowledge import load_knowledge


def test_bundled_knowledge_file_exists():
    """The package must ship with knowledge_files/best_practices.md."""
    import openreview_mcp
    pkg_dir = os.path.dirname(os.path.abspath(openreview_mcp.__file__))
    bundled_dir = os.path.join(pkg_dir, "knowledge_files")
    assert os.path.isfile(os.path.join(bundled_dir, "best_practices.md"))


def test_bundled_knowledge_loads_non_empty():
    """Loading the bundled file must yield non-empty practice sections."""
    import openreview_mcp
    pkg_dir = os.path.dirname(os.path.abspath(openreview_mcp.__file__))
    bundled_dir = os.path.join(pkg_dir, "knowledge_files")

    kb = load_knowledge(os.path.join(bundled_dir, "best_practices.md"))

    assert len(kb.practices) > 0, (
        "Bundled best_practices.md produced zero practice sections"
    )
