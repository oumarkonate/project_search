# project-search MCP Server

A local MCP server that provides fast file and code search for any project.
Designed to save Claude tokens by returning only paths and snippets — never full file contents.

## Why this server exists — token savings

Without this server, Claude's default strategy to find a class or locate usages is to read files one by one: list a directory, open a file, scan it, repeat. On a medium PHP/JS project (500–2 000 files) that pattern burns tokens fast:

| Task | Without server | With server |
|---|---|---|
| Find where `ContentRepository` is declared | List directory + read 5–20 files | One `find_class` call → path + line |
| Find all callers of a service method | Read each candidate file | One `grep_code` call → `file:line:snippet` list |
| Locate a test file for a source file | Read directory tree, guess name | One `find_tests` call → exact path |
| Find files matching a pattern | Recursive `find` via Bash + read output | One `find_files` call → filtered path list |

**Typical saving: 70–90 % of search tokens per task.**

The key design principle: every tool returns the minimum useful unit — a path, a line number, and a ≤ 120-char snippet. Claude never receives full file contents from this server; it reads the file only when it actually needs to edit or understand it in depth.

## Tools

### Navigation & structure

| Tool | Description |
|------|-------------|
| `find_files` | Find files by name substring or glob pattern |
| `directory_tree` | Show project directory tree (configurable depth, respects excluded dirs) |
| `read_file` | Read a file with optional line range — returns content and total line count |
| `get_file_outline` | List all classes, methods and functions in a file with their line numbers |

### Search

| Tool | Description |
|------|-------------|
| `grep_code` | Search for text/regex in code, returns `file:line:snippet` |
| `grep_with_context` | Like `grep_code` but includes N lines before/after each match (default: 3, max: 10) |
| `count_matches` | Count occurrences of a pattern without returning all results — useful before a full grep |

### PHP & framework

| Tool | Description | Requirements |
|------|-------------|--------------|
| `find_class` | Locate a PHP class/interface/trait/enum declaration by name | PHP files |
| `find_method` | Locate method/function declarations by name | PHP + JS/TS files |
| `find_implementations` | Find all PHP classes implementing a given interface | PHP files |
| `find_extends` | Find all PHP classes extending a given class | PHP files |
| `find_route` | Find Symfony controllers/actions by route pattern | Symfony 5.2+ with PHP 8 `#[Route]` attributes |
| `find_tests` | Find test files for a source file (PHPUnit, Jest, Playwright) | PHP / JS / TS files |
| `find_usages` | Find all references to a symbol across the project | All configured extensions |

### Git-aware search

| Tool | Description | Requirements |
|------|-------------|--------------|
| `git_changed_files` | List files modified by git (unstaged, staged, or by commit SHA) | Git repository |
| `grep_changed` | Grep only in files modified by git — focus on the current diff | Git repository |

## Notes per tool

### `read_file`
Returns up to 200 lines by default when no range is specified. Use `start_line`/`end_line` to target a specific section. Line numbers are 1-indexed and match the numbers returned by `grep_code` and `grep_with_context`.

### `get_file_outline`
Uses regex-based parsing (not AST). PHP support is comprehensive: classes, interfaces, traits, enums, and methods with visibility/modifiers. JS/TS support covers `function` declarations and `class` definitions; arrow functions assigned to `const`/`let` are also detected. Class method bodies in JS/TS are not extracted.

### `grep_with_context`
Context lines are capped at 10 to avoid token bloat. When working on large codebases, combine with a reduced `max_results` value.

### `find_usages`
Searches by whole-word match (`\bSymbolName\b`). Results include matches in comments and string literals — this is a text search, not an AST traversal. Suitable for navigation and discovery.

### `find_implementations` and `find_extends`
PHP-only. Detects direct declarations on a single line (e.g. `implements InterfaceA, InterfaceB`). Multi-line declarations are not detected. `find_extends` returns direct children only — call it recursively to walk a full hierarchy.

### `find_route`
**Symfony only.** Supports PHP 8 attribute syntax (`#[Route('/path', methods: ['GET'])]`) introduced in Symfony 5.2. Does **not** support:
- Doctrine annotation style (`@Route`) — deprecated since Symfony 6.x
- YAML routing (`config/routes.yaml`)
- XML routing
- Laravel routes (`routes/web.php`)

### `git_changed_files` and `grep_changed`
Require `PROJECT_SEARCH_ROOT` to be inside a git repository. If not, a clear error message is returned. When using inside a monorepo where `PROJECT_SEARCH_ROOT` is a sub-directory, paths are resolved relative to the configured root.

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

grep_with_context("class ContentRepository", context_lines=2)
→ src/Domain/Repository/ContentRepository.php:41
  before: ["<?php", "namespace Domain\\Repository;"]
  snippet: "class ContentRepository implements ContentRepositoryInterface"
  after:  ["{", "    public function __construct("]

find_class("ContentRepository")
→ path: src/Domain/Repository/ContentRepository.php, line: 41, namespace: Domain\Repository

get_file_outline("src/Domain/Services/ContentService.php")
→ [{kind: "class", name: "ContentService", line: 12},
   {kind: "method", name: "findById", line: 20, visibility: "public"},
   {kind: "method", name: "save", line: 35, visibility: "public"}]

find_implementations("ContentRepositoryInterface")
→ [{path: "src/Domain/Repository/ContentRepository.php", line: 41, class_name: "ContentRepository"}]

find_route("/api/content")
→ [{path: "src/Controller/ContentController.php", line: 18, route: "/api/content/{id}",
    methods: ["GET"], class_name: "ContentController", action: "show"}]

find_tests("src/Domain/Services/Content.php")
→ tests/Domain/Services/ContentTest.php (phpunit)

git_changed_files(scope="unstaged")
→ [{path: "src/Domain/Services/ContentService.php", status: "M"}]

grep_changed("TODO", scope="unstaged")
→ src/Domain/Services/ContentService.php:57 — // TODO: handle empty result
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
