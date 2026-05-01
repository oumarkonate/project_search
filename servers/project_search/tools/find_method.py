from pydantic import BaseModel

from project_search.lib.searcher import find_method as _find_method
from project_search.tools.common import TokenSavings

_TOKENS_PER_FILE = 1200


class MethodLocation(BaseModel):
    path: str
    line: int
    kind: str
    class_name: str | None
    visibility: str | None


class FindMethodReport(BaseModel):
    results: list[MethodLocation]
    token_savings: TokenSavings


def find_method(
    method_name: str,
    class_name: str | None = None,
    directory: str | None = None,
) -> FindMethodReport:
    """Locate method or function declarations by name (PHP and JS/TS).

    For PHP: detects functions and class methods with optional visibility/modifiers.
    For JS/TS: detects function declarations and arrow functions assigned to const/let.

    Args:
        method_name: Name of the method or function to find (case-insensitive).
        class_name: Optional PHP class name to restrict the search to a specific class.
        directory: Optional subdirectory to restrict the search (relative to project root).

    Returns:
        results: list of declarations with path, line number, kind (method/function),
                 class name (if inside a class), and visibility.
        token_savings: estimated tokens saved vs. Claude reading files directly.
    """
    raw, files_searched = _find_method(method_name, class_name, directory)
    results = [MethodLocation(**r) for r in raw]
    estimated_saved = files_searched * _TOKENS_PER_FILE
    return FindMethodReport(
        results=results,
        token_savings=TokenSavings(
            files_scanned=files_searched,
            estimated_tokens_saved=estimated_saved,
            note=(
                f"searched {files_searched} file(s), "
                f"found {len(results)} declaration(s) of '{method_name}'"
            ),
        ),
    )
