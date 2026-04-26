# Plan — MCP Server `project-search`

## Context

Claude consomme beaucoup de tokens pour trouver des fichiers dans un grand projet (5 000+ sources PHP/JS/TS/Twig). L'objectif est de créer un serveur MCP local générique — **open-source**, configurable via variables d'env — qui expose des tools de recherche de fichiers hautes performance. Claude interroge ce serveur au lieu de lire des répertoires en brut, ce qui économise des tokens tout en gardant des résultats précis.

Inspiré directement de **ckeditor_audit** (même stack Python + MCP SDK, même structure de package).

---

## Emplacement

```
~/IA/mcp/servers/project_search/          ← racine du dépôt git open-source
├── .env                                  # config projet-spécifique (non versionné)
├── .env.example                          # template publié
├── .gitignore
├── README.md
├── SETUP.md
├── requirements.txt
└── servers/
    └── project_search/                   ← package Python
        ├── __init__.py
        ├── __main__.py                   # entry point: python -m project_search
        ├── server.py                     # MCPServer + enregistrement tools
        ├── config.py                     # Settings (frozen dataclass, env vars)
        ├── lib/
        │   ├── __init__.py
        │   └── searcher.py               # moteur de recherche
        └── tools/
            ├── __init__.py
            ├── find_files.py
            ├── grep_code.py
            ├── find_class.py
            └── find_tests.py
```

---

## Variables d'environnement (config.py)

| Variable | Requis | Défaut | Exemple |
|---|---|---|---|
| `PROJECT_SEARCH_ROOT` | ✅ | — | `/home/konate/Workspace/verso-cms` |
| `PROJECT_SEARCH_EXCLUDE_DIRS` | | `vendor,node_modules,.git,var,web` | — |
| `PROJECT_SEARCH_MAX_RESULTS` | | `50` | `100` |
| `PROJECT_SEARCH_EXTENSIONS` | | `php,js,ts,twig,yaml,scss` | — |

---

## Les 4 Tools

### 1. `find_files(pattern, directory?, extension?)`
Retourne les chemins de fichiers correspondant au pattern (substring ou glob).

### 2. `grep_code(query, directory?, extensions?, max_results?)`
Recherche regex dans le code, retourne `{path, line, snippet}` — jamais le fichier complet.

### 3. `find_class(class_name, kind?)`
Localise une classe/interface/trait/enum PHP par nom — retourne `{path, line, kind, namespace}`.

### 4. `find_tests(source_path)`
Trouve les fichiers de test correspondant à un fichier source (PHPUnit, Jest, Playwright).

---

## Enregistrement Claude Code

```json
{
  "mcpServers": {
    "project-search": {
      "command": "/home/konate/IA/mcp/servers/project_search/.venv/bin/python3",
      "args": ["-m", "project_search"],
      "cwd": "/home/konate/IA/mcp/servers/project_search/servers",
      "env": {
        "PYTHONPATH": "/home/konate/IA/mcp/servers/project_search/servers"
      }
    }
  }
}
```