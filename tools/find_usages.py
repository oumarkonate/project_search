from pydantic import BaseModel

from project_search.lib.searcher import find_usages as _find_usages
from project_search.tools.common import TokenSavings

_TOKENS_PER_FILE = 1200


class UsageMatch(BaseModel):
    path: str
    line: int
    snippet: str


class FindUsagesReport(BaseModel):
    matches: list[UsageMatch]
    token_savings: TokenSavings


def find_usages(
    symbol: str,
    directory: str | None = None,
    extensions: list[str] | None = None,
) -> FindUsagesReport:
    """Find all references to a symbol across the project.

    Searches by whole-word match to reduce false positives. Results include matches
    in comments and string literals — this is a text search, not AST-based.
    Suitable for navigation and discovery; cross-check with grep_code for critical usage.

    Args:
        symbol: Symbol name to search for (class, method, variable, constant, etc.).
        directory: Optional subdirectory to restrict the search (relative to project root).
        extensions: Optional list of file extensions to search, e.g. ["php", "ts"].

    Returns:
        matches: list of usages with file path, line number, and a short snippet.
        token_savings: estimated tokens saved vs. Claude reading files directly.
    """
    raw, files_searched = _find_usages(symbol, directory, extensions)
    matches = [UsageMatch(**r) for r in raw]
    estimated_saved = files_searched * _TOKENS_PER_FILE
    return FindUsagesReport(
        matches=matches,
        token_savings=TokenSavings(
            files_scanned=files_searched,
            estimated_tokens_saved=estimated_saved,
            note=(
                f"searched {files_searched} file(s), "
                f"found {len(matches)} reference(s) to '{symbol}'"
            ),
        ),
    )
