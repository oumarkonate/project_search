from pydantic import BaseModel

from project_search.lib.searcher import find_route as _find_route
from project_search.tools.common import TokenSavings

_TOKENS_PER_FILE = 1200


class RouteLocation(BaseModel):
    path: str
    line: int
    route: str
    methods: list[str]
    class_name: str
    action: str


class FindRouteReport(BaseModel):
    results: list[RouteLocation]
    token_savings: TokenSavings


def find_route(pattern: str) -> FindRouteReport:
    """Find Symfony controllers and actions by route path pattern.

    Searches PHP 8 attribute syntax only: #[Route('/path', methods: ['GET'])].
    Introduced in Symfony 5.2. Does not support Doctrine @Route annotations,
    YAML routing (config/routes.yaml), or XML routing.

    Args:
        pattern: Substring to match against route paths (e.g. "/api/content" or "/api").

    Returns:
        results: list of matching routes with path, line number, route string, HTTP methods,
                 controller class name, and action method name.
        token_savings: estimated tokens saved vs. Claude reading all PHP files directly.
    """
    raw, files_searched = _find_route(pattern)
    results = [RouteLocation(**r) for r in raw]
    estimated_saved = files_searched * _TOKENS_PER_FILE
    return FindRouteReport(
        results=results,
        token_savings=TokenSavings(
            files_scanned=files_searched,
            estimated_tokens_saved=estimated_saved,
            note=(
                f"searched {files_searched} PHP file(s), "
                f"found {len(results)} route(s) matching '{pattern}'"
            ),
        ),
    )
