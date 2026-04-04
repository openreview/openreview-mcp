"""Live introspection of the openreview-py library using Python's inspect module."""

import inspect
from typing import Any


# Classes to introspect, mapped as (module_path, class_name)
TARGET_CLASSES = [
    ("openreview.api.client", "OpenReviewClient"),
    ("openreview.openreview", "Client"),
    ("openreview.api.client", "Note"),
    ("openreview.api.client", "Invitation"),
    ("openreview.api.client", "Edge"),
    ("openreview.api.client", "Group"),
    ("openreview.api.client", "Tag"),
    ("openreview.api.client", "Edit"),
    ("openreview.openreview", "Profile"),
    ("openreview.venue", "Venue"),
    ("openreview.journal", "Journal"),
]


def _extract_params(sig: inspect.Signature) -> list[dict[str, Any]]:
    """Extract parameter info from a signature."""
    params = []
    for name, param in sig.parameters.items():
        if name == "self":
            continue
        info: dict[str, Any] = {"name": name}
        if param.annotation != inspect.Parameter.empty:
            info["type"] = str(param.annotation)
        if param.default != inspect.Parameter.empty:
            info["default"] = repr(param.default)
        params.append(info)
    return params


def introspect_library() -> dict[str, dict[str, dict[str, Any]]]:
    """Import openreview and introspect all target classes.

    Returns a dict keyed by class name, where each value is a dict
    of method_name -> method_info.
    """
    import importlib

    cache: dict[str, dict[str, dict[str, Any]]] = {}

    for module_path, class_name in TARGET_CLASSES:
        try:
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)
        except (ImportError, AttributeError):
            continue

        methods: dict[str, dict[str, Any]] = {}
        for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
            # Skip private methods except __init__
            if name.startswith("_") and name != "__init__":
                continue

            try:
                sig = inspect.signature(method)
            except (ValueError, TypeError):
                sig = None

            docstring = inspect.getdoc(method)

            methods[name] = {
                "name": name,
                "class_name": class_name,
                "module": module_path,
                "signature": str(sig) if sig else "()",
                "params": _extract_params(sig) if sig else [],
                "docstring": docstring,
            }

        cache[class_name] = methods

    return cache


def search_methods(
    query: str,
    class_name: str | None,
    cache: dict[str, dict[str, dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Search methods by keyword with relevance ranking.

    Ranking: exact name match > name contains > docstring contains > param contains.
    Returns at most 15 results.
    """
    query_lower = query.lower()
    exact = []
    name_contains = []
    doc_contains = []
    param_contains = []

    classes_to_search = (
        {class_name: cache[class_name]} if class_name and class_name in cache else cache
    )

    for cls_name, methods in classes_to_search.items():
        for method_name, info in methods.items():
            if method_name == "__init__":
                continue

            if method_name.lower() == query_lower:
                exact.append(info)
            elif query_lower in method_name.lower():
                name_contains.append(info)
            elif info.get("docstring") and query_lower in info["docstring"].lower():
                doc_contains.append(info)
            elif any(query_lower in p["name"].lower() for p in info.get("params", [])):
                param_contains.append(info)

    results = exact + name_contains + doc_contains + param_contains
    return results[:15]


def get_method_details(
    method_name: str,
    cache: dict[str, dict[str, dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Get full details for methods matching the given name.

    Exact matches first, then partial matches.
    """
    method_lower = method_name.lower()
    exact = []
    partial = []

    for cls_name, methods in cache.items():
        for name, info in methods.items():
            if name.lower() == method_lower:
                exact.append(info)
            elif method_lower in name.lower() and name != "__init__":
                partial.append(info)

    return exact + partial
