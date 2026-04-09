"""Static knowledge parser for llm.txt and examples.md."""

import re
from dataclasses import dataclass, field


@dataclass
class KnowledgeBase:
    """Indexed sections from llm.txt and examples.md."""

    practices: dict[str, str] = field(default_factory=dict)
    examples: dict[str, str] = field(default_factory=dict)


def _parse_sections(content: str, level: str = "## ") -> dict[str, str]:
    """Split markdown content into sections by header level.

    Returns dict of {header_text: section_content_including_subsections}.
    """
    sections: dict[str, str] = {}
    current_header = None
    current_lines: list[str] = []

    for line in content.split("\n"):
        if line.startswith(level) and not line.startswith(level + "#"):
            if current_header is not None:
                sections[current_header] = "\n".join(current_lines).strip()
            current_header = line[len(level):].strip()
            current_lines = [line]
        elif current_header is not None:
            current_lines.append(line)

    if current_header is not None:
        sections[current_header] = "\n".join(current_lines).strip()

    return sections


def load_knowledge(llm_txt_path: str, examples_md_path: str) -> KnowledgeBase:
    """Parse llm.txt and examples.md into an indexed KnowledgeBase."""
    if not _file_exists(llm_txt_path):
        raise FileNotFoundError(f"llm.txt not found at: {llm_txt_path}")
    if not _file_exists(examples_md_path):
        raise FileNotFoundError(f"examples.md not found at: {examples_md_path}")

    with open(llm_txt_path, "r") as f:
        llm_content = f.read()
    with open(examples_md_path, "r") as f:
        examples_content = f.read()

    return KnowledgeBase(
        practices=_parse_sections(llm_content, "## "),
        examples=_parse_sections(examples_content, "## "),
    )


def _file_exists(path: str) -> bool:
    import os
    return os.path.isfile(path)


def search_best_practices(topic: str, kb: KnowledgeBase) -> str:
    """Search llm.txt sections by topic. Header matches ranked above content matches."""
    header_matches = []
    content_matches = []

    for header, content in kb.practices.items():
        if _all_words_match(topic, header):
            header_matches.append(content)
        elif _all_words_match(topic, content):
            content_matches.append(content)

    results = header_matches + content_matches
    if not results:
        return ""
    return "\n\n---\n\n".join(results)


def _all_words_match(query: str, text: str) -> bool:
    """Check if all words in query appear in text (case-insensitive)."""
    words = query.lower().split()
    text_lower = text.lower()
    return all(word in text_lower for word in words)


def search_examples(operation: str, kb: KnowledgeBase) -> str:
    """Search examples.md sections by operation keyword."""
    matches = []

    for header, content in kb.examples.items():
        if _all_words_match(operation, header) or _all_words_match(operation, content):
            matches.append(content)

    if not matches:
        return ""
    return "\n\n---\n\n".join(matches)


def get_workflow(workflow_type: str, kb: KnowledgeBase) -> str:
    """Get workflow guide combining practices and examples.

    For 'conference' or 'journal': returns the full workflow section + matching examples.
    For a specific stage: returns matching content from both.
    """
    parts = []

    # Search practices for workflow section
    for header, content in kb.practices.items():
        if _all_words_match(workflow_type, header):
            parts.append(content)

    # Search examples for matching code
    for header, content in kb.examples.items():
        if _all_words_match(workflow_type, header):
            parts.append(content)

    # If no direct match, search content for the keyword
    if not parts:
        for header, content in kb.practices.items():
            if _all_words_match(workflow_type, content):
                parts.append(content)
        for header, content in kb.examples.items():
            if _all_words_match(workflow_type, content):
                parts.append(content)

    if not parts:
        return ""
    return "\n\n---\n\n".join(parts)
