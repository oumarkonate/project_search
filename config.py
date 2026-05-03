import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    project_root: Path
    exclude_dirs: frozenset[str]
    max_results: int
    extensions: tuple[str, ...]


def _load() -> Settings:
    root_str = os.environ.get("PROJECT_SEARCH_ROOT", "")
    if not root_str:
        raise RuntimeError("PROJECT_SEARCH_ROOT environment variable is required")

    root = Path(root_str)
    if not root.exists():
        raise RuntimeError(f"PROJECT_SEARCH_ROOT does not exist: {root}")

    exclude_raw = os.environ.get(
        "PROJECT_SEARCH_EXCLUDE_DIRS", "vendor,node_modules,.git,var,web"
    )
    exclude_dirs = frozenset(d.strip() for d in exclude_raw.split(",") if d.strip())

    max_results = int(os.environ.get("PROJECT_SEARCH_MAX_RESULTS", "50"))

    ext_raw = os.environ.get("PROJECT_SEARCH_EXTENSIONS", "php,js,ts,twig,yaml,scss")
    extensions = tuple(e.strip().lstrip(".") for e in ext_raw.split(",") if e.strip())

    return Settings(
        project_root=root,
        exclude_dirs=exclude_dirs,
        max_results=max_results,
        extensions=extensions,
    )


settings = _load()
