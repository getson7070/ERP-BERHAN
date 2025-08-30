"""In-memory plugin registry with optional chatbot/RPA hooks."""

from typing import Callable, Dict, List, Any

_registry: List[Dict[str, Any]] = []


def register(
    name: str,
    bp=None,
    jobs: List[Callable] | None = None,
    chatbot: Callable | None = None,
):
    _registry.append(
        {"name": name, "blueprint": bp, "jobs": jobs or [], "chatbot": chatbot}
    )


def get_plugins() -> List[Dict[str, Any]]:
    return list(_registry)
