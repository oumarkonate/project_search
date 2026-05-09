# Setup Guide

## Prerequisites

- Python 3.10+
- Claude Code (CLI or Desktop)

## Step 1 — Clone and install

**macOS / Linux**

```bash
git clone <repo>
cd project_search

python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

**Windows (PowerShell)**

```powershell
git clone <repo>
cd project_search

python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

> No need to activate the venv — calling `.venv\Scripts\pip` directly installs into the correct environment.

## Step 2 — Configure your project

**macOS / Linux**

```bash
cp .env.example .env
```

**Windows (PowerShell)**

```powershell
copy .env.example .env
```

Edit `.env`:

```
PROJECT_SEARCH_ROOT=/path/to/your/project       # macOS / Linux
PROJECT_SEARCH_ROOT=C:\path\to\your\project     # Windows
```

Optional variables (uncomment to override defaults):

```
# PROJECT_SEARCH_EXCLUDE_DIRS=vendor,node_modules,.git,var,web
# PROJECT_SEARCH_MAX_RESULTS=50
# PROJECT_SEARCH_EXTENSIONS=php,js,ts,twig,yaml,scss
```

## Step 3 — Register in Claude Desktop

Open the configuration file:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

Add the `project_search` entry under `mcpServers`.

**macOS / Linux**

```json
{
  "mcpServers": {
    "project_search": {
      "command": "/absolute/path/to/mcp/project_search/.venv/bin/python3",
      "args": ["-m", "project_search"],
      "env": {
        "PYTHONPATH": "/absolute/path/to/mcp"
      }
    }
  }
}
```

**Windows**

```json
{
  "mcpServers": {
    "project_search": {
      "command": "C:\\path\\to\\mcp\\project_search\\.venv\\Scripts\\python.exe",
      "args": ["-m", "project_search"],
      "env": {
        "PYTHONPATH": "C:\\path\\to\\mcp"
      }
    }
  }
}
```

> `PYTHONPATH` must point to the **parent directory** of `project_search/` so that `python -m project_search` can resolve the package. `PROJECT_SEARCH_ROOT` is loaded from `.env` automatically.

See `claude_desktop_config.json.linux.example` (Linux/macOS) and `claude_desktop_config.json.windows.example` (Windows) for ready-to-copy templates.

Restart Claude Desktop after any change to this file.

## Step 4 — Register in Claude Code (VS Code / CLI)

Add a `.mcp.json` at the root of your project — same format as above.

## Verify

Test the server manually (it should hang waiting for stdio input — that is correct):

**macOS / Linux**

```bash
cd /absolute/path/to/mcp
PYTHONPATH=$(pwd) project_search/.venv/bin/python3 -m project_search
```

**Windows (PowerShell)**

```powershell
$env:PYTHONPATH = "C:\path\to\mcp"
& "C:\path\to\mcp\project_search\.venv\Scripts\python.exe" -m project_search
```

Press `Ctrl+C` to stop.
