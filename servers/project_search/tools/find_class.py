from pydantic import BaseModel

from project_search.lib.searcher import find_class as _find_class


class ClassLocation(BaseModel):
    path: str
    line: int
    kind: str
    namespace: str


def find_class(
    class_name: str,
    kind: str | None = None,
) -> list[ClassLocation]:
    """Locate a PHP class, interface, trait, or enum declaration by name.

    Args:
        class_name: Exact class name to find (e.g. "ContentRepository").
        kind: Optional filter: "class", "interface", "trait", or "enum".

    Returns:
        List of locations where the class is declared, with path, line number,
        kind, and namespace.
    """
    raw = _find_class(class_name, kind)
    return [ClassLocation(**r) for r in raw]
