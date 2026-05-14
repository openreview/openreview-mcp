"""Static knowledge parser for best_practices.md."""

import os
from dataclasses import dataclass, field


@dataclass
class KnowledgeBase:
    """Indexed sections parsed from best_practices.md."""

    practices: dict[str, str] = field(default_factory=dict)


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


def load_knowledge(best_practices_path: str) -> KnowledgeBase:
    """Parse best_practices.md into an indexed KnowledgeBase."""
    if not os.path.isfile(best_practices_path):
        raise FileNotFoundError(
            f"best_practices.md not found at: {best_practices_path}"
        )

    with open(best_practices_path) as f:
        content = f.read()

    return KnowledgeBase(practices=_parse_sections(content, "## "))


def search_best_practices(topic: str, kb: KnowledgeBase) -> str:
    """Search best_practices.md sections by topic. Header matches ranked above content matches."""
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
