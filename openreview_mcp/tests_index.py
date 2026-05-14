"""Index over the upstream openreview-py test suite.

Builds an AST-postings index keyed by identifier/string-literal tokens so that
`search_test_examples` can surface canonical call sites for a query. Test files
are parsed once at registration time; bodies are read lazily via `linecache`
when a query hits.
"""

import ast
import linecache
import logging
import os
import re
import textwrap
from dataclasses import dataclass, field

logger = logging.getLogger("openreview_mcp")


_STOPWORDS = frozenset(
    {
        "self",
        "cls",
        "args",
        "kwargs",
        "true",
        "false",
        "none",
        "assert",
        "print",
        "len",
        "list",
        "dict",
        "set",
        "tuple",
        "str",
        "int",
        "bool",
        "float",
        "test",
        "tests",
        "value",
        "values",
        "name",
        "names",
        "id",
        "ids",
        "type",
        "types",
        "result",
        "results",
        "i",
        "j",
        "k",
        "x",
        "y",
    }
)

# Substring pattern for tokens worth extracting out of string literals (e.g.
# invitation IDs, group IDs). 4+ chars to skip noise.
_STRING_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_./]{3,}")

# Selenium / webdriver imports anywhere in the file head mark it as a UI test.
_SELENIUM_RE = re.compile(r"(?:from|import)\s+\S*(?:selenium|webdriver)")


@dataclass
class TestSnippet:
    """One indexed test function."""

    file: str
    class_name: str | None
    func_name: str
    start_lineno: int
    end_lineno: int
    arg_names: list[str]
    length_lines: int
    tokens: frozenset[str]


@dataclass
class TestIndex:
    """In-memory index of all indexed test functions."""

    snippets: list[TestSnippet]
    postings: dict[str, list[int]] = field(default_factory=dict)
    helpers_methods: list[str] = field(default_factory=list)
    tests_dir: str = ""


def _add_split(tokens: set[str], identifier: str) -> None:
    """Add an identifier (lowercased) plus underscore/slash/dot-split parts."""
    low = identifier.lower()
    if len(low) >= 2 and low not in _STOPWORDS:
        tokens.add(low)
    for part in re.split(r"[_/.]", low):
        if len(part) >= 2 and part not in _STOPWORDS:
            tokens.add(part)


def _extract_tokens(node: ast.AST, class_name: str | None) -> frozenset[str]:
    """Extract a token set from a function definition AST node.

    Combines: function name, class name, identifier names, attribute access
    names, and substrings of string literals matching `_STRING_TOKEN_RE`.
    """
    tokens: set[str] = set()
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        _add_split(tokens, node.name)
    if class_name:
        _add_split(tokens, class_name)
    for sub in ast.walk(node):
        if isinstance(sub, ast.Name):
            _add_split(tokens, sub.id)
        elif isinstance(sub, ast.Attribute):
            _add_split(tokens, sub.attr)
        elif isinstance(sub, ast.Constant) and isinstance(sub.value, str):
            for match in _STRING_TOKEN_RE.findall(sub.value):
                _add_split(tokens, match)
    return frozenset(tokens)


def _build_snippet(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    path: str,
    class_name: str | None,
) -> TestSnippet:
    end_lineno = getattr(node, "end_lineno", None) or node.lineno
    arg_names = [a.arg for a in node.args.args]
    return TestSnippet(
        file=path,
        class_name=class_name,
        func_name=node.name,
        start_lineno=node.lineno,
        end_lineno=end_lineno,
        arg_names=arg_names,
        length_lines=end_lineno - node.lineno + 1,
        tokens=_extract_tokens(node, class_name),
    )


def _collect_test_functions(
    container: ast.Module | ast.ClassDef,
    path: str,
    class_name: str | None,
    snippets: list[TestSnippet],
) -> None:
    for node in container.body:
        if isinstance(node, ast.ClassDef):
            _collect_test_functions(node, path, node.name, snippets)
        elif isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef)
        ) and node.name.startswith("test_"):
            snippets.append(_build_snippet(node, path, class_name))


def _is_selenium_tainted(path: str) -> bool:
    """Cheap check: scan the first ~50 lines for selenium/webdriver imports."""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            head = "".join(next(f, "") for _ in range(50))
    except OSError:
        return False
    return bool(_SELENIUM_RE.search(head))


def _extract_helpers_methods(tests_dir: str) -> list[str]:
    """AST-extract method names off conftest.py's `Helpers` class, if present.

    Pure parse — no import — so conftest fixtures never execute.
    """
    conftest = os.path.join(tests_dir, "conftest.py")
    if not os.path.isfile(conftest):
        return []
    try:
        with open(conftest, encoding="utf-8", errors="replace") as f:
            tree = ast.parse(f.read(), filename=conftest)
    except (SyntaxError, OSError) as e:
        logger.debug("Could not parse %s: %s", conftest, e)
        return []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "Helpers":
            methods = []
            for child in node.body:
                if isinstance(
                    child, (ast.FunctionDef, ast.AsyncFunctionDef)
                ) and not child.name.startswith("_"):
                    methods.append(child.name)
            return methods
    return []


def build_test_index(tests_dir: str) -> TestIndex | None:
    """Walk `tests_dir` top-level `test_*.py` files and build an AST index.

    Returns None if the directory does not exist. Per-file parse failures are
    swallowed (logged at DEBUG) so a single bad file doesn't break the index.
    """
    if not os.path.isdir(tests_dir):
        return None

    snippets: list[TestSnippet] = []
    helpers_methods = _extract_helpers_methods(tests_dir)

    for name in sorted(os.listdir(tests_dir)):
        if not (name.startswith("test_") and name.endswith(".py")):
            continue
        path = os.path.join(tests_dir, name)
        if not os.path.isfile(path):
            continue
        if _is_selenium_tainted(path):
            logger.debug("Skipping selenium-tainted test file: %s", name)
            continue
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                src = f.read()
            tree = ast.parse(src, filename=path)
        except (SyntaxError, OSError) as e:
            logger.debug("Could not parse %s: %s", path, e)
            continue
        _collect_test_functions(tree, path, None, snippets)

    postings: dict[str, list[int]] = {}
    for idx, snippet in enumerate(snippets):
        for token in snippet.tokens:
            postings.setdefault(token, []).append(idx)

    return TestIndex(
        snippets=snippets,
        postings=postings,
        helpers_methods=helpers_methods,
        tests_dir=tests_dir,
    )


def _tokenize_query(query: str) -> list[str]:
    return [
        t
        for t in query.lower().replace("_", " ").split()
        if t and t not in _STOPWORDS
    ]


def search_test_index(
    query: str,
    index: TestIndex,
    max_results: int = 5,
) -> list[dict]:
    """Rank snippets by query term hits and return the top results.

    Scoring: query terms in func name or class name count 2x; terms in body
    tokens count 1x. A mild length penalty discourages enormous methods.
    """
    query_terms = _tokenize_query(query)
    if not query_terms:
        return []

    candidates: set[int] = set()
    for term in query_terms:
        candidates.update(index.postings.get(term, []))

    scored: list[tuple[float, int, TestSnippet]] = []
    for idx in candidates:
        snippet = index.snippets[idx]
        name_terms = set(snippet.func_name.lower().replace("_", " ").split())
        class_terms = (
            set(snippet.class_name.lower().replace("_", " ").split())
            if snippet.class_name
            else set()
        )
        score = 0.0
        for term in query_terms:
            if term in name_terms:
                score += 2
            elif term in class_terms:
                score += 2
            elif term in snippet.tokens:
                score += 1
        score -= 0.1 * max(0, (snippet.length_lines - 50) // 100)
        if score > 0:
            scored.append((score, idx, snippet))

    scored.sort(
        key=lambda r: (-r[0], r[2].length_lines, r[2].file, r[2].start_lineno)
    )
    cap = min(max(1, max_results), 10)
    return [{"snippet": s, "score": sc} for sc, _, s in scored[:cap]]


def _read_body(snippet: TestSnippet) -> str:
    lines = [
        linecache.getline(snippet.file, ln)
        for ln in range(snippet.start_lineno, snippet.end_lineno + 1)
    ]
    return textwrap.dedent("".join(lines)).rstrip("\n")


def _truncate_body(body: str, max_lines: int = 60) -> str:
    lines = body.splitlines()
    if len(lines) <= max_lines:
        return body
    head_n, tail_n = 30, 20
    elided = len(lines) - head_n - tail_n
    return "\n".join(
        lines[:head_n]
        + [f"# ... <{elided} lines elided> ..."]
        + lines[-tail_n:]
    )


def format_test_results(
    results: list[dict],
    helpers_methods: list[str],
    tests_dir: str,
    response_cap_bytes: int = 8192,
) -> str:
    """Render search results as a single plain-text string."""
    if not results:
        return "No matching tests found."

    parts: list[str] = []
    total = 0
    referenced_helpers = False

    for r in results:
        snippet: TestSnippet = r["snippet"]
        rel = os.path.relpath(snippet.file, tests_dir) if tests_dir else snippet.file
        header_target = (
            f"{snippet.class_name}.{snippet.func_name}"
            if snippet.class_name
            else snippet.func_name
        )
        header = (
            f"### {rel}:L{snippet.start_lineno}-L{snippet.end_lineno} — "
            f"{header_target}"
        )

        fixture_args = [a for a in snippet.arg_names if a != "self"]
        preamble = (
            f"# fixtures: {', '.join(fixture_args)}\n" if fixture_args else ""
        )

        body = _truncate_body(_read_body(snippet))
        section = f"{header}\n{preamble}{body}"

        if "helpers." in body:
            referenced_helpers = True

        if total + len(section) > response_cap_bytes and parts:
            parts.append("... (further results omitted to fit response cap)")
            break
        parts.append(section)
        total += len(section)

    out = "\n\n---\n\n".join(parts)
    if referenced_helpers and helpers_methods:
        out += (
            "\n\n# conftest Helpers methods available: "
            + ", ".join(helpers_methods)
        )
    return out
