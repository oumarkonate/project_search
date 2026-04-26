# project-search MCP Server

A local MCP server that provides fast file and code search for any project.
Designed to save Claude tokens by returning only paths and snippets — never full file contents.

## Tools

| Tool | Description |
|------|-------------|
| `find_files` | Find files by name substring or glob pattern |
| `grep_code` | Search for text/regex in code, returns `file:line:snippet` |
| `find_class` | Locate a PHP class/interface/trait/enum declaration |
| `find_tests` | Find test files corresponding to a source file (PHPUnit, Jest, Playwright) |

## Installation

See [SETUP.md](SETUP.md) for detailed setup instructions.

### Quick start

```bash
git clone <repo>
cd project_search

# Create venv and install dependencies
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Configure your project
cp .env.example .env
# Edit .env and set PROJECT_SEARCH_ROOT to your project path
```

### Register in Claude Code

Add to `~/.config/Claude/claude_desktop_config.json` (Linux) or `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

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

## Configuration

| Variable | Required | Default | Description |
|---|---|---|---|
| `PROJECT_SEARCH_ROOT` | Yes | — | Absolute path to your project root |
| `PROJECT_SEARCH_EXCLUDE_DIRS` | No | `vendor,node_modules,.git,var,web` | Directories to skip |
| `PROJECT_SEARCH_MAX_RESULTS` | No | `50` | Max results for grep/find |
| `PROJECT_SEARCH_EXTENSIONS` | No | `php,js,ts,twig,yaml,scss` | File extensions to index |

## Examples

```
find_files("ContentService", extension="php")
→ src/Domain/Services/ContentService.php

grep_code("implements ContentRepositoryInterface", extensions=["php"])
→ src/Domain/Repository/ContentRepository.php:41 — class ContentRepository implements ...

find_class("ContentRepository")
→ path: src/Domain/Repository/ContentRepository.php, line: 41, namespace: Domain\Repository

find_tests("src/Domain/Services/Content.php")
→ tests/Domain/Services/ContentTest.php (phpunit)
```

## Architecture

Inspired by [ckeditor-audit](https://github.com/...) — same Python + MCP SDK stack.

```
servers/project_search/
├── __main__.py     # entry point
├── server.py       # MCPServer + tool registration
├── config.py       # Settings from env vars
├── lib/searcher.py # Search engine (pathlib, regex)
└── tools/          # One file per MCP tool
```
