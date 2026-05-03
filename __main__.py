import sys
from pathlib import Path

_root = Path(__file__).parent
_env_file = _root / ".env"

from dotenv import load_dotenv
load_dotenv(_env_file, override=False)

from project_search.server import mcp

mcp.run()
