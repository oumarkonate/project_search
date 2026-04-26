# Setup Guide

## Prerequisites

- Python 3.10+
- Claude Code (CLI or Desktop)

## Step 1 — Clone and install

```bash
git clone <repo>
cd project_search

python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Step 2 — Configure your project

```bash
cp .env.example .env
```

Edit `.env`:

```
PROJECT_SEARCH_ROOT=/path/to/your/project
```

Optional variables (uncomment to override defaults):

```
# PROJECT_SEARCH_EXCLUDE_DIRS=vendor,node_modules,.git,var,web
# PROJECT_SEARCH_MAX_RESULTS=50
# PROJECT_SEARCH_EXTENSIONS=php,js,ts,twig,yaml,scss
```

## Step 3 — Register in Claude Code

Find your config file:
- **Linux:** `~/.config/Claude/claude_desktop_config.json`
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

Add the `project-search` entry under `mcpServers`:

```json
{
  "mcpServers": {
    "project-search": {
      "command": "/absolute/path/to/project_search/.venv/bin/python3",
      "args": ["-m", "project_search"],
      "cwd": "/absolute/path/to/project_search/servers",
      "env": {
        "PYTHONPATH": "/absolute/path/to/project_search/servers"
      }
    }
  }
}
```

> Replace `/absolute/path/to/project_search` with the actual path where you cloned the repo.

## Step 4 — Restart Claude Code

Reload Claude Code to pick up the new MCP server. The `project-search` tools will be available immediately.

## Verify

Test the server manually:

```bash
cd servers
PYTHONPATH=$(pwd) ../. venv/bin/python -m project_search
# Should hang waiting for stdio input — that's correct
```
