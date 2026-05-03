from pydantic import BaseModel

from project_search.lib.searcher import find_class as _find_class
from project_search.tools.common import TokenSavings

_TOKENS_PER_FILE = 1200


class ClassLocation(BaseModel):
    path: str
    line: int
    kind: str
    namespace: str


class FindClassReport(BaseModel):
    results: list[ClassLocation]
    token_savings: TokenSavings


def find_class(
    class_name: str,
    kind: str | None = None,
) -> FindClassReport:
    """Locate a PHP class, interface, trait, or enum declaration by name.

    Args:
        class_name: Exact class name to find (e.g. "ContentRepository").
        kind: Optional filter: "class", "interface", "trait", or "enum".

    Returns:
        results: list of locations where the class is declared, with path, line number,
                 kind, and namespace.
        token_savings: estimated tokens saved vs. Claude reading all PHP files directly.
    """
    raw, files_searched = _find_class(class_name, kind)
    results = [ClassLocation(**r) for r in raw]
    estimated_saved = files_searched * _TOKENS_PER_FILE
    return FindClassReport(
        results=results,
        token_savings=TokenSavings(
            files_scanned=files_searched,
            estimated_tokens_saved=estimated_saved,
            note=(
                f"searched {files_searched} PHP file(s), "
                f"found {len(results)} declaration(s) of '{class_name}'"
            ),
        ),
    )