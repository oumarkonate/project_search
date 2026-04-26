from pydantic import BaseModel

from project_search.lib.searcher import grep_code as _grep_code


class GrepMatch(BaseModel):
    path: str
    line: int
    snippet: str


def grep_code(
    query: str,
    directory: str | None = None,
    extensions: list[str] | None = None,
    max_results: int | None = None,
) -> list[GrepMatch]:
    """Search for a regex pattern in source files.

    Returns one result per matching line with a short snippet (never full file content).

    Args:
        query: Regex pattern (or plain text) to search for.
        directory: Optional subdirectory to restrict the search (relative to project root).
        extensions: Optional list of file extensions to search, e.g. ["php", "yaml"].
        max_results: Maximum number of results to return (defaults to PROJECT_SEARCH_MAX_RESULTS).

    Returns:
        List of matches with file path, line number, and a short snippet (≤ 120 chars).
    """
    raw = _grep_code(query, directory, extensions, max_results)
    return [GrepMatch(**r) for r in raw]
