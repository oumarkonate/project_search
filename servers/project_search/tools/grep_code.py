from pydantic import BaseModel

from project_search.lib.searcher import grep_code as _grep_code
from project_search.tools.common import TokenSavings

_TOKENS_PER_FILE = 1200


class GrepMatch(BaseModel):
    path: str
    line: int
    snippet: str


class GrepCodeReport(BaseModel):
    matches: list[GrepMatch]
    token_savings: TokenSavings


def grep_code(
    query: str,
    directory: str | None = None,
    extensions: list[str] | None = None,
    max_results: int | None = None,
) -> GrepCodeReport:
    """Search for a regex pattern in source files.

    Returns one result per matching line with a short snippet (never full file content).

    Args:
        query: Regex pattern (or plain text) to search for.
        directory: Optional subdirectory to restrict the search (relative to project root).
        extensions: Optional list of file extensions to search, e.g. ["php", "yaml"].
        max_results: Maximum number of results to return (defaults to PROJECT_SEARCH_MAX_RESULTS).

    Returns:
        matches: list of matches with file path, line number, and a short snippet (≤ 120 chars).
        token_savings: estimated tokens saved vs. Claude reading the files directly.
    """
    raw, files_searched = _grep_code(query, directory, extensions, max_results)
    matches = [GrepMatch(**r) for r in raw]
    estimated_saved = files_searched * _TOKENS_PER_FILE
    return GrepCodeReport(
        matches=matches,
        token_savings=TokenSavings(
            files_scanned=files_searched,
            estimated_tokens_saved=estimated_saved,
            note=(
                f"searched {files_searched} file(s), "
                f"returned {len(matches)} match(es)"
            ),
        ),
    )