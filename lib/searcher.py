import re
import subprocess
from pathlib import Path
from typing import Generator

from project_search.config import settings


def _is_excluded(path: Path) -> bool:
    return any(part in settings.exclude_dirs for part in path.parts)


def iter_files(root: Path, extensions: tuple[str, ...] | None = None) -> Generator[Path, None, None]:
    exts = extensions or settings.extensions
    for path in root.rglob("*"):
        if path.is_file() and not _is_excluded(path.relative_to(settings.project_root)):
            if path.suffix.lstrip(".") in exts:
                yield path


def find_files(
    pattern: str,
    directory: str | None = None,
    extension: str | None = None,
) -> tuple[list[dict], int]:
    root = settings.project_root / directory if directory else settings.project_root
    if not root.exists():
        return [], 0

    exts = (extension.lstrip("."),) if extension else settings.extensions
    results = []
    files_checked = 0

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(settings.project_root)
        if _is_excluded(rel):
            continue
        if path.suffix.lstrip(".") not in exts:
            continue
        files_checked += 1
        if pattern.lower() in path.name.lower():
            results.append({"path": str(rel), "name": path.name})
        if len(results) >= settings.max_results:
            break

    return results, files_checked


def grep_code(
    query: str,
    directory: str | None = None,
    extensions: list[str] | None = None,
    max_results: int | None = None,
) -> tuple[list[dict], int]:
    root = settings.project_root / directory if directory else settings.project_root
    if not root.exists():
        return [], 0

    exts = tuple(e.lstrip(".") for e in extensions) if extensions else settings.extensions
    limit = max_results or settings.max_results
    results = []
    files_searched = 0

    try:
        pattern = re.compile(query)
    except re.error:
        pattern = re.compile(re.escape(query))

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(settings.project_root)
        if _is_excluded(rel):
            continue
        if path.suffix.lstrip(".") not in exts:
            continue

        files_searched += 1
        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                for lineno, line in enumerate(f, 1):
                    if pattern.search(line):
                        snippet = line.strip()[:120]
                        results.append({"path": str(rel), "line": lineno, "snippet": snippet})
                        if len(results) >= limit:
                            return results, files_searched
        except OSError:
            continue

    return results, files_searched


_CLASS_PATTERN = re.compile(
    r"^(?:abstract\s+|final\s+|readonly\s+)?"
    r"(class|interface|trait|enum)\s+(\w+)"
)
_NAMESPACE_PATTERN = re.compile(r"^namespace\s+([\w\\]+)\s*;")


def find_class(class_name: str, kind: str | None = None) -> tuple[list[dict], int]:
    root = settings.project_root
    results = []
    files_searched = 0

    for path in root.rglob("*.php"):
        rel = path.relative_to(root)
        if _is_excluded(rel):
            continue

        files_searched += 1
        namespace = ""
        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                for lineno, line in enumerate(f, 1):
                    ns_match = _NAMESPACE_PATTERN.match(line.strip())
                    if ns_match:
                        namespace = ns_match.group(1)
                        continue
                    cls_match = _CLASS_PATTERN.match(line.strip())
                    if cls_match:
                        found_kind, found_name = cls_match.group(1), cls_match.group(2)
                        if found_name == class_name:
                            if kind is None or found_kind == kind:
                                results.append({
                                    "path": str(rel),
                                    "line": lineno,
                                    "kind": found_kind,
                                    "namespace": namespace,
                                })
        except OSError:
            continue

    return results, files_searched


# ---------------------------------------------------------------------------
# Tier 1 — read_file
# ---------------------------------------------------------------------------

_DEFAULT_LINE_CAP = 200


def read_file(
    path: str,
    start_line: int | None = None,
    end_line: int | None = None,
) -> tuple[str, int]:
    """Returns (content, total_lines)."""
    full_path = settings.project_root / path
    if not full_path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not full_path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    with open(full_path, encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    total = len(lines)
    start = (start_line - 1) if start_line else 0
    end = end_line if end_line else (start + _DEFAULT_LINE_CAP if not start_line else min(start + _DEFAULT_LINE_CAP, total))
    end = min(end, total)

    return "".join(lines[start:end]), total


# ---------------------------------------------------------------------------
# Tier 1 — get_file_outline
# ---------------------------------------------------------------------------

_PHP_CLASS_RE = re.compile(
    r"^(?:abstract\s+|final\s+|readonly\s+)?(class|interface|trait|enum)\s+(\w+)"
)
_PHP_METHOD_RE = re.compile(
    r"^\s*(?:(public|protected|private)\s+)?(?:static\s+)?(?:abstract\s+|final\s+)?function\s+(\w+)\s*\("
)
_JS_CLASS_RE = re.compile(r"^(?:export\s+)?(?:default\s+)?class\s+(\w+)")
_JS_FUNC_RE = re.compile(r"^(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+(\w+)\s*\(")
_JS_ARROW_RE = re.compile(r"^(?:export\s+)?(?:const|let)\s+(\w+)\s*=\s*(?:async\s+)?\(")
_TS_METHOD_RE = re.compile(
    r"^\s+(?:(public|protected|private|readonly)\s+)?(?:static\s+)?(?:async\s+)?(\w+)\s*\("
)


def get_file_outline(path: str) -> list[dict]:
    full_path = settings.project_root / path
    if not full_path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    ext = full_path.suffix.lstrip(".")
    results: list[dict] = []
    in_class = False

    with open(full_path, encoding="utf-8", errors="ignore") as f:
        for lineno, line in enumerate(f, 1):
            stripped = line.strip()
            if not stripped:
                continue

            if ext == "php":
                m = _PHP_CLASS_RE.match(stripped)
                if m:
                    results.append({"kind": m.group(1), "name": m.group(2), "line": lineno})
                    continue
                m = _PHP_METHOD_RE.match(stripped)
                if m:
                    results.append({
                        "kind": "method",
                        "name": m.group(2),
                        "line": lineno,
                        "visibility": m.group(1) or "public",
                    })

            elif ext in ("js", "ts", "tsx", "jsx"):
                m = _JS_CLASS_RE.match(stripped)
                if m:
                    results.append({"kind": "class", "name": m.group(1), "line": lineno})
                    in_class = True
                    continue
                m = _JS_FUNC_RE.match(stripped)
                if m:
                    results.append({"kind": "function", "name": m.group(1), "line": lineno})
                    continue
                m = _JS_ARROW_RE.match(stripped)
                if m:
                    results.append({"kind": "function", "name": m.group(1), "line": lineno})
                    continue
                if in_class and ext in ("ts", "tsx"):
                    m = _TS_METHOD_RE.match(line)
                    if m and m.group(2) not in ("if", "for", "while", "switch", "catch"):
                        results.append({
                            "kind": "method",
                            "name": m.group(2),
                            "line": lineno,
                            "visibility": m.group(1) or "public",
                        })

    return results


# ---------------------------------------------------------------------------
# Tier 1 — grep_with_context
# ---------------------------------------------------------------------------


def grep_with_context(
    query: str,
    context_lines: int = 3,
    directory: str | None = None,
    extensions: list[str] | None = None,
    max_results: int | None = None,
) -> tuple[list[dict], int]:
    root = settings.project_root / directory if directory else settings.project_root
    if not root.exists():
        return [], 0

    exts = tuple(e.lstrip(".") for e in extensions) if extensions else settings.extensions
    limit = max_results or settings.max_results
    ctx = min(max(context_lines, 0), 10)
    results: list[dict] = []
    files_searched = 0

    try:
        pattern = re.compile(query)
    except re.error:
        pattern = re.compile(re.escape(query))

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(settings.project_root)
        if _is_excluded(rel):
            continue
        if path.suffix.lstrip(".") not in exts:
            continue

        files_searched += 1
        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                file_lines = f.readlines()

            for lineno, line in enumerate(file_lines, 1):
                if not pattern.search(line):
                    continue

                before_start = max(0, lineno - 1 - ctx)
                after_end = min(len(file_lines), lineno + ctx)

                before = [file_lines[i].rstrip() for i in range(before_start, lineno - 1)]
                after = [file_lines[i].rstrip() for i in range(lineno, after_end)]

                results.append({
                    "path": str(rel),
                    "line": lineno,
                    "snippet": line.strip()[:120],
                    "before": before,
                    "after": after,
                })
                if len(results) >= limit:
                    return results, files_searched
        except OSError:
            continue

    return results, files_searched


# ---------------------------------------------------------------------------
# Tier 1 — directory_tree
# ---------------------------------------------------------------------------


def directory_tree(
    directory: str | None = None,
    depth: int = 3,
    extensions_filter: list[str] | None = None,
) -> tuple[str, int]:
    """Returns (tree_string, files_traversed)."""
    root = settings.project_root / directory if directory else settings.project_root
    if not root.exists():
        return f"Directory not found: {directory or '.'}", 0

    max_depth = min(max(depth, 1), 6)
    exts = tuple(e.lstrip(".") for e in extensions_filter) if extensions_filter else None
    lines: list[str] = []
    files_traversed = 0

    def _walk(current: Path, prefix: str, current_depth: int) -> None:
        nonlocal files_traversed
        if current_depth > max_depth:
            return
        try:
            entries = sorted(current.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        except PermissionError:
            return

        visible = []
        for entry in entries:
            rel = entry.relative_to(settings.project_root)
            if _is_excluded(rel):
                continue
            if entry.is_file():
                files_traversed += 1
                if exts and entry.suffix.lstrip(".") not in exts:
                    continue
            visible.append(entry)

        for i, entry in enumerate(visible):
            is_last = i == len(visible) - 1
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{entry.name}")
            if entry.is_dir():
                child_prefix = prefix + ("    " if is_last else "│   ")
                if current_depth < max_depth:
                    _walk(entry, child_prefix, current_depth + 1)
                else:
                    lines.append(f"{child_prefix}└── ...")

    root_label = str(root.relative_to(settings.project_root)) if directory else "."
    lines.append(root_label)
    _walk(root, "", 1)
    return "\n".join(lines), files_traversed


# ---------------------------------------------------------------------------
# Tier 1 — find_method
# ---------------------------------------------------------------------------

_PHP_CLASS_NAME_RE = re.compile(
    r"^(?:abstract\s+|final\s+|readonly\s+)?(?:class|interface|trait|enum)\s+(\w+)"
)
_PHP_FUNC_DECL_RE = re.compile(
    r"^\s*(?:(public|protected|private)\s+)?(?:static\s+)?(?:abstract\s+|final\s+)?function\s+(\w+)\s*\("
)
_JS_METHOD_DECL_RE = re.compile(
    r"^\s*(?:(?:public|protected|private|static|async|readonly)\s+)*(\w+)\s*\("
)


def find_method(
    method_name: str,
    class_name: str | None = None,
    directory: str | None = None,
) -> tuple[list[dict], int]:
    root = settings.project_root / directory if directory else settings.project_root
    if not root.exists():
        return [], 0

    name_lower = method_name.lower()
    results: list[dict] = []
    files_searched = 0

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(settings.project_root)
        if _is_excluded(rel):
            continue
        ext = path.suffix.lstrip(".")
        if ext not in settings.extensions:
            continue

        files_searched += 1
        current_class: str | None = None

        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                for lineno, line in enumerate(f, 1):
                    stripped = line.strip()

                    if ext == "php":
                        cm = _PHP_CLASS_NAME_RE.match(stripped)
                        if cm:
                            current_class = cm.group(1)
                            continue

                        m = _PHP_FUNC_DECL_RE.match(stripped)
                        if m:
                            vis, fname = m.group(1), m.group(2)
                            if fname.lower() == name_lower:
                                if class_name is None or (
                                    current_class and current_class.lower() == class_name.lower()
                                ):
                                    results.append({
                                        "path": str(rel),
                                        "line": lineno,
                                        "kind": "method" if current_class else "function",
                                        "class_name": current_class,
                                        "visibility": vis or "public",
                                    })

                    elif ext in ("js", "ts", "tsx", "jsx"):
                        m = _JS_FUNC_RE.match(stripped)
                        if m and m.group(1).lower() == name_lower:
                            results.append({
                                "path": str(rel),
                                "line": lineno,
                                "kind": "function",
                                "class_name": None,
                                "visibility": None,
                            })
                            continue
                        m = _JS_ARROW_RE.match(stripped)
                        if m and m.group(1).lower() == name_lower:
                            results.append({
                                "path": str(rel),
                                "line": lineno,
                                "kind": "function",
                                "class_name": None,
                                "visibility": None,
                            })
        except OSError:
            continue

    return results, files_searched


# ---------------------------------------------------------------------------
# Tier 1 — count_matches
# ---------------------------------------------------------------------------


def count_matches(
    query: str,
    directory: str | None = None,
    extensions: list[str] | None = None,
) -> dict:
    root = settings.project_root / directory if directory else settings.project_root
    if not root.exists():
        return {"total_matches": 0, "files_matched": 0, "files_searched": 0}

    exts = tuple(e.lstrip(".") for e in extensions) if extensions else settings.extensions

    try:
        pattern = re.compile(query)
    except re.error:
        pattern = re.compile(re.escape(query))

    total_matches = 0
    files_matched = 0
    files_searched = 0

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(settings.project_root)
        if _is_excluded(rel):
            continue
        if path.suffix.lstrip(".") not in exts:
            continue

        files_searched += 1
        file_count = 0
        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                for line in f:
                    file_count += len(pattern.findall(line))
        except OSError:
            continue

        if file_count:
            total_matches += file_count
            files_matched += 1

    return {
        "total_matches": total_matches,
        "files_matched": files_matched,
        "files_searched": files_searched,
    }


# ---------------------------------------------------------------------------
# Tier 2 — find_usages
# ---------------------------------------------------------------------------


def find_usages(
    symbol: str,
    directory: str | None = None,
    extensions: list[str] | None = None,
) -> tuple[list[dict], int]:
    query = r"\b" + re.escape(symbol) + r"\b"
    return grep_code(query, directory, extensions)


# ---------------------------------------------------------------------------
# Tier 2 — find_implementations
# ---------------------------------------------------------------------------

_IMPLEMENTS_RE = re.compile(r"\bimplements\b([^{;]+)")


def find_implementations(interface_name: str) -> tuple[list[dict], int]:
    root = settings.project_root
    results: list[dict] = []
    files_searched = 0

    for path in root.rglob("*.php"):
        rel = path.relative_to(root)
        if _is_excluded(rel):
            continue

        files_searched += 1
        namespace = ""

        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                for lineno, line in enumerate(f, 1):
                    stripped = line.strip()

                    ns_match = _NAMESPACE_PATTERN.match(stripped)
                    if ns_match:
                        namespace = ns_match.group(1)
                        continue

                    impl_match = _IMPLEMENTS_RE.search(stripped)
                    if not impl_match:
                        continue
                    interfaces = [i.strip().split("\\")[-1] for i in impl_match.group(1).split(",")]
                    if interface_name not in interfaces:
                        continue

                    cls_match = _CLASS_PATTERN.match(stripped)
                    results.append({
                        "path": str(rel),
                        "line": lineno,
                        "class_name": cls_match.group(2) if cls_match else "",
                        "namespace": namespace,
                    })
        except OSError:
            continue

    return results, files_searched


# ---------------------------------------------------------------------------
# Tier 2 — find_extends
# ---------------------------------------------------------------------------

_EXTENDS_RE = re.compile(r"\bextends\s+([\w\\]+)")


def find_extends(base_class: str) -> tuple[list[dict], int]:
    root = settings.project_root
    results: list[dict] = []
    files_searched = 0

    for path in root.rglob("*.php"):
        rel = path.relative_to(root)
        if _is_excluded(rel):
            continue

        files_searched += 1
        namespace = ""

        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                for lineno, line in enumerate(f, 1):
                    stripped = line.strip()

                    ns_match = _NAMESPACE_PATTERN.match(stripped)
                    if ns_match:
                        namespace = ns_match.group(1)
                        continue

                    ext_match = _EXTENDS_RE.search(stripped)
                    if not ext_match:
                        continue
                    parent = ext_match.group(1).split("\\")[-1]
                    if parent != base_class:
                        continue

                    cls_match = _CLASS_PATTERN.match(stripped)
                    results.append({
                        "path": str(rel),
                        "line": lineno,
                        "class_name": cls_match.group(2) if cls_match else "",
                        "namespace": namespace,
                    })
        except OSError:
            continue

    return results, files_searched


# ---------------------------------------------------------------------------
# Tier 2 — find_route (Symfony PHP 8 #[Route] attributes)
# ---------------------------------------------------------------------------

_ROUTE_ATTR_RE = re.compile(r"#\[Route\(([^)]+)\)\]")
_ROUTE_METHODS_RE = re.compile(r"methods\s*:\s*\[([^\]]+)\]")


def _extract_route_path(attr_content: str) -> str | None:
    # Named parameter: path: '...' or value: '...'
    named = re.search(r"(?:path|value)\s*:\s*['\"]([^'\"]+)['\"]", attr_content)
    if named:
        return named.group(1)
    # Positional: strip named params, take first quoted string
    cleaned = re.sub(r"\w+\s*:\s*['\"][^'\"]*['\"]", "", attr_content)
    cleaned = re.sub(r"\w+\s*:\s*\[[^\]]*\]", "", cleaned)
    first = re.search(r"['\"]([^'\"]+)['\"]", cleaned)
    return first.group(1) if first else None


def find_route(pattern: str) -> tuple[list[dict], int]:
    root = settings.project_root
    results: list[dict] = []
    files_searched = 0
    pattern_lower = pattern.lower()

    for path in root.rglob("*.php"):
        rel = path.relative_to(root)
        if _is_excluded(rel):
            continue

        files_searched += 1
        current_class: str | None = None

        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                file_lines = f.readlines()

            for lineno, line in enumerate(file_lines, 1):
                stripped = line.strip()

                cls_match = _CLASS_PATTERN.match(stripped)
                if cls_match:
                    current_class = cls_match.group(2)

                route_match = _ROUTE_ATTR_RE.search(stripped)
                if not route_match:
                    continue

                attr_content = route_match.group(1)
                route_path = _extract_route_path(attr_content)
                if not route_path or pattern_lower not in route_path.lower():
                    continue

                methods: list[str] = []
                methods_match = _ROUTE_METHODS_RE.search(attr_content)
                if methods_match:
                    methods = [m.strip().strip("'\"") for m in methods_match.group(1).split(",")]

                action = ""
                for next_line in file_lines[lineno:lineno + 5]:
                    ns = next_line.strip()
                    if ns and not ns.startswith("#["):
                        fm = re.search(r"function\s+(\w+)", ns)
                        if fm:
                            action = fm.group(1)
                        break

                results.append({
                    "path": str(rel),
                    "line": lineno,
                    "route": route_path,
                    "methods": methods,
                    "class_name": current_class or "",
                    "action": action,
                })
        except OSError:
            continue

    return results, files_searched


# ---------------------------------------------------------------------------
# Tier 3 — git_changed_files
# ---------------------------------------------------------------------------


def _assert_git_repo() -> None:
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=str(settings.project_root),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Not a git repository: {settings.project_root}")


def git_changed_files(scope: str = "unstaged") -> list[dict]:
    _assert_git_repo()

    if scope == "staged":
        cmd = ["git", "diff", "--cached", "--name-status"]
    elif scope == "all":
        cmd = ["git", "status", "--porcelain"]
    elif scope == "unstaged":
        cmd = ["git", "diff", "--name-status"]
    else:
        cmd = ["git", "diff-tree", "--no-commit-id", "-r", "--name-status", scope]

    result = subprocess.run(
        cmd,
        cwd=str(settings.project_root),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git command failed: {result.stderr.strip()}")

    files: list[dict] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        if scope == "all":
            status = line[:2].strip() or "M"
            path = line[3:].strip()
        else:
            parts = line.split("\t", 1)
            if len(parts) < 2:
                continue
            status, path = parts[0][0], parts[1].strip()
        files.append({"path": path, "status": status})

    return files


# ---------------------------------------------------------------------------
# Tier 3 — grep_changed
# ---------------------------------------------------------------------------


def grep_changed(
    query: str,
    scope: str = "unstaged",
    extensions: list[str] | None = None,
) -> tuple[list[dict], int]:
    changed = git_changed_files(scope)
    if not changed:
        return [], 0

    exts = tuple(e.lstrip(".") for e in extensions) if extensions else settings.extensions
    relevant = [
        f["path"] for f in changed
        if f["status"] != "D" and Path(f["path"]).suffix.lstrip(".") in exts
    ]
    if not relevant:
        return [], 0

    try:
        pattern = re.compile(query)
    except re.error:
        pattern = re.compile(re.escape(query))

    results: list[dict] = []
    files_searched = 0

    for rel_path in relevant:
        full_path = settings.project_root / rel_path
        if not full_path.exists():
            continue
        files_searched += 1
        try:
            with open(full_path, encoding="utf-8", errors="ignore") as f:
                for lineno, line in enumerate(f, 1):
                    if pattern.search(line):
                        results.append({
                            "path": rel_path,
                            "line": lineno,
                            "snippet": line.strip()[:120],
                        })
        except OSError:
            continue

    return results, files_searched


# ---------------------------------------------------------------------------
# find_tests (original)
# ---------------------------------------------------------------------------

def find_tests(source_path: str) -> list[dict]:
    root = settings.project_root
    results = []

    src = Path(source_path)
    stem = src.stem
    ext = src.suffix.lstrip(".")

    # PHP: replace src/ → tests/, append Test to stem
    if ext == "php":
        candidates = [
            # Direct mirror: src/Domain/X.php → tests/Domain/XTest.php
            Path(str(src).replace("src/", "tests/", 1)).with_stem(stem + "Test"),
            # Flat search by name
        ]
        for candidate in candidates:
            full = root / candidate
            if full.exists():
                results.append({"path": str(candidate), "framework": "phpunit"})

        # Fallback: rglob for *Test.php with same stem
        if not results:
            for path in root.rglob(f"{stem}Test.php"):
                rel = path.relative_to(root)
                if not _is_excluded(rel):
                    results.append({"path": str(rel), "framework": "phpunit"})

    # JS/TS: look for *.test.ts, *.spec.ts, *.test.js, *.spec.js
    elif ext in ("js", "ts", "tsx", "jsx"):
        for test_ext in (f"{stem}.test.ts", f"{stem}.spec.ts", f"{stem}.test.js", f"{stem}.spec.js", f"{stem}.test.tsx"):
            for path in root.rglob(test_ext):
                rel = path.relative_to(root)
                if not _is_excluded(rel):
                    results.append({"path": str(rel), "framework": "jest"})

        # Playwright: look in playwright/ or features/ by stem
        for path in (root / "playwright").rglob(f"*{stem}*"):
            if path.is_file() and path.suffix in (".ts", ".js"):
                rel = path.relative_to(root)
                results.append({"path": str(rel), "framework": "playwright"})

    return results
