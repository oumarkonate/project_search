from pydantic import BaseModel

from project_search.lib.searcher import get_file_outline as _get_file_outline
from project_search.tools.common import TokenSavings

_TOKENS_PER_FILE = 1200


class OutlineEntry(BaseModel):
    kind: str
    name: str
    line: int
    visibility: str | None = None


class GetFileOutlineReport(BaseModel):
    results: list[OutlineEntry]
    token_savings: TokenSavings


def get_file_outline(path: str) -> GetFileOutlineReport:
    """List all classes, methods, and functions declared in a file with their line numbers.

    Supports PHP (classes, interfaces, traits, enums, methods with visibility) and
    JS/TS (classes, functions, arrow functions, TypeScript class methods).
    Uses regex-based parsing — comprehensive for PHP, heuristic for JS/TS.

    Args:
        path: Relative path from project root (e.g. "src/Domain/Services/ContentService.php").

    Returns:
        results: list of declarations ordered by line number, each with kind, name, line,
                 and optional visibility (public/protected/private).
        token_savings: estimated tokens saved vs. Claude reading the full file directly.
    """
    raw = _get_file_outline(path)
    results = [OutlineEntry(**entry) for entry in raw]
    return GetFileOutlineReport(
        results=results,
        token_savings=TokenSavings(
            files_scanned=1,
            estimated_tokens_saved=_TOKENS_PER_FILE,
            note=f"parsed {path}, found {len(results)} declaration(s)",
        ),
    )
