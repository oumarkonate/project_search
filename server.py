import logging
import sys

from mcp.server.mcpserver import MCPServer

from project_search.tools.find_files import find_files
from project_search.tools.grep_code import grep_code
from project_search.tools.find_class import find_class
from project_search.tools.find_tests import find_tests
from project_search.tools.read_file import read_file
from project_search.tools.get_file_outline import get_file_outline
from project_search.tools.grep_with_context import grep_with_context
from project_search.tools.directory_tree import directory_tree
from project_search.tools.find_method import find_method
from project_search.tools.count_matches import count_matches
from project_search.tools.find_usages import find_usages
from project_search.tools.find_implementations import find_implementations
from project_search.tools.find_extends import find_extends
from project_search.tools.find_route import find_route
from project_search.tools.git_changed_files import git_changed_files
from project_search.tools.grep_changed import grep_changed

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

# Navigation & structure
mcp.tool()(find_files)
mcp.tool()(directory_tree)
mcp.tool()(read_file)
mcp.tool()(get_file_outline)

# Search
mcp.tool()(grep_code)
mcp.tool()(grep_with_context)
mcp.tool()(count_matches)

# PHP & framework
mcp.tool()(find_class)
mcp.tool()(find_method)
mcp.tool()(find_implementations)
mcp.tool()(find_extends)
mcp.tool()(find_route)
mcp.tool()(find_tests)
mcp.tool()(find_usages)

# Git-aware search
mcp.tool()(git_changed_files)
mcp.tool()(grep_changed)
