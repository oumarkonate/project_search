from pydantic import BaseModel

from project_search.lib.searcher import grep_with_context as _grep_with_context
from project_search.tools.common import TokenSavings

_TOKENS_PER_FILE = 1200


class ContextMatch(BaseModel):
    path: str
    line: int
    snippet: str
    before: list[str]
    after: list[str]


class GrepContextReport(BaseModel):
    matches: list[ContextMatch]
    token_savings: TokenSavings


def grep_with_context(
    query: str,
    context_lines: int = 3,
    directory: str | None = None,
    extensions: list[str] | None = None,
    max_results: int | None = None,
) -> GrepContextReport:
    """Search for a regex pattern and return surrounding lines for each match.

    Args:
        query: Regex pattern (or plain text) to search for.
        context_lines: Number of lines to include before and after each match (default: 3, max: 10).
        directory: Optional subdirectory to restrict the search (relative to project root).
        extensions: Optional list of file extensions to search, e.g. ["php", "yaml"].
        max_results: Maximum number of matches to return (defaults to PROJECT_SEARCH_MAX_RESULTS).

    Returns:
        matches: Each match with file path, line number, the matching snippet, and lists of
                 lines before and after the match.
        token_savings: estimated tokens saved vs. Claude reading the files directly.
    """
    raw, files_searched = _grep_with_context(query, context_lines, directory, extensions, max_results)
    matches = [ContextMatch(**r) for r in raw]
    estimated_saved = files_searched * _TOKENS_PER_FILE
    return GrepContextReport(
        matches=matches,
        token_savings=TokenSavings(
            files_scanned=files_searched,
            estimated_tokens_saved=estimated_saved,
            note=(
                f"searched {files_searched} file(s), "
                f"returned {len(matches)} match(es) with {context_lines} context line(s)"
            ),
        ),
    )
