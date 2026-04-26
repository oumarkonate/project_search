import logging
import sys

from mcp.server.mcpserver import MCPServer

from project_search.tools.find_files import find_files
from project_search.tools.grep_code import grep_code
from project_search.tools.find_class import find_class
from project_search.tools.find_tests import find_tests

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

mcp = MCPServer(
    name="project-search",
    title="Project File Search",
    description="Fast local file and code search for any project. Saves tokens by returning paths and snippets instead of full file contents.",
)

mcp.tool()(find_files)
mcp.tool()(grep_code)
mcp.tool()(find_class)
mcp.tool()(find_tests)
