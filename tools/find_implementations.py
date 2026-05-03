from pydantic import BaseModel

from project_search.lib.searcher import find_implementations as _find_implementations
from project_search.tools.common import TokenSavings

_TOKENS_PER_FILE = 1200


class ImplementationLocation(BaseModel):
    path: str
    line: int
    class_name: str
    namespace: str


class FindImplementationsReport(BaseModel):
    results: list[ImplementationLocation]
    token_savings: TokenSavings


def find_implementations(interface_name: str) -> FindImplementationsReport:
    """Find all PHP classes that implement a given interface.

    Detects direct `implements InterfaceName` declarations on a single line,
    including multi-interface declarations (e.g. `implements A, InterfaceName, B`).
    Searches only PHP files.

    Args:
        interface_name: Exact interface name to search for (e.g. "ContentRepositoryInterface").

    Returns:
        results: list of implementing classes with path, line number, class name, and namespace.
        token_savings: estimated tokens saved vs. Claude reading all PHP files directly.
    """
    raw, files_searched = _find_implementations(interface_name)
    results = [ImplementationLocation(**r) for r in raw]
    estimated_saved = files_searched * _TOKENS_PER_FILE
    return FindImplementationsReport(
        results=results,
        token_savings=TokenSavings(
            files_scanned=files_searched,
            estimated_tokens_saved=estimated_saved,
            note=(
                f"searched {files_searched} PHP file(s), "
                f"found {len(results)} implementation(s) of '{interface_name}'"
            ),
        ),
    )
