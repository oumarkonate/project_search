import sys
from pathlib import Path

# Load .env from the server root (3 levels up: project_search/ → servers/ → project_search/)
_root = Path(__file__).parent.parent.parent
_env_file = _root / ".env"

from dotenv import load_dotenv
load_dotenv(_env_file, override=False)

from project_search.server import mcp

mcp.run()
