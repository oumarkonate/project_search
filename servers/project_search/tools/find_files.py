from pydantic import BaseModel

from project_search.lib.searcher import find_files as _find_files


class FileMatch(BaseModel):
    path: str
    name: str


def find_files(
    pattern: str,
    directory: str | None = None,
    extension: str | None = None,
) -> list[FileMatch]:
    """Find files whose name contains the given pattern.

    Args:
        pattern: Substring to search for in file names (case-insensitive).
        directory: Optional subdirectory to restrict the search (relative to project root).
        extension: Optional file extension filter, e.g. "php" or "ts".

    Returns:
        List of matching files with their relative path and name.
    """
    raw = _find_files(pattern, directory, extension)
    return [FileMatch(**r) for r in raw]
