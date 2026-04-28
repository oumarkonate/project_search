import re
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
