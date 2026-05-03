from pydantic import BaseModel

from project_search.lib.searcher import count_matches as _count_matches
from project_search.tools.common import TokenSavings

_TOKENS_PER_FILE = 1200


class CountMatchesReport(BaseModel):
    total_matches: int
    files_matched: int
    files_searched: int
    token_savings: TokenSavings


def count_matches(
    query: str,
    directory: str | None = None,
    extensions: list[str] | None = None,
) -> CountMatchesReport:
    """Count occurrences of a pattern without returning all results.

    Useful to gauge the scope of a pattern before running grep_code.
    If total_matches is much larger than PROJECT_SEARCH_MAX_RESULTS,
    consider refining the pattern first.

    Args:
        query: Regex pattern (or plain text) to count.
        directory: Optional subdirectory to restrict the search (relative to project root).
        extensions: Optional list of file extensions to search, e.g. ["php", "ts"].

    Returns:
        total_matches: Total number of pattern occurrences across all files.
        files_matched: Number of files that contain at least one match.
        files_searched: Total number of files scanned.
        token_savings: estimated tokens saved vs. Claude reading files directly.
    """
    raw = _count_matches(query, directory, extensions)
    files_searched = raw["files_searched"]
    estimated_saved = files_searched * _TOKENS_PER_FILE
    return CountMatchesReport(
        **raw,
        token_savings=TokenSavings(
            files_scanned=files_searched,
            estimated_tokens_saved=estimated_saved,
            note=(
                f"searched {files_searched} file(s), "
                f"found {raw['total_matches']} match(es) in {raw['files_matched']} file(s)"
            ),
        ),
    )
