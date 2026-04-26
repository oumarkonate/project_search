from pydantic import BaseModel

from project_search.lib.searcher import find_tests as _find_tests


class TestMatch(BaseModel):
    path: str
    framework: str


def find_tests(source_path: str) -> list[TestMatch]:
    """Find test files corresponding to a source file.

    Works for PHP (PHPUnit), JS/TS (Jest), and Playwright.

    Args:
        source_path: Relative path to the source file (e.g. "src/Domain/Services/Content.php")
                     or just a file name (e.g. "Content.php").

    Returns:
        List of test files with their relative path and the test framework name.
    """
    raw = _find_tests(source_path)
    return [TestMatch(**r) for r in raw]
