"""Read-only SQLite database adapter."""

import sqlite3
from pathlib import Path
from src.config import settings


class DatabaseAccessError(Exception):
    """Raised when access to a database is denied."""


class QueryNotAllowedError(Exception):
    """Raised when a non-SELECT query is attempted."""


def validate_db_path(db_path: str) -> Path:
    """Resolve path and check against the allowlist.

    Raises DatabaseAccessError if the path is not in the allowlist.
    """
    resolved = Path(db_path).resolve()

    # Check against allowlist (use string comparison after resolve)
    for allowed in settings.allowed_sqlite_paths:
        if Path(allowed).resolve() == resolved:
            return resolved

    raise DatabaseAccessError(
        f"Database path not allowed: {db_path}. "
        f"Allowed paths: {settings.allowed_sqlite_paths}"
    )


def validate_readonly_query(query: str) -> str:
    """Ensure query is a read-only SELECT or WITH statement.

    Raises QueryNotAllowedError if the query is not allowed.
    """
    stripped = query.strip()

    # Remove comments (simple -- style)
    lines = []
    for line in stripped.split("\n"):
        comment_idx = line.find("--")
        if comment_idx >= 0:
            line = line[:comment_idx]
        lines.append(line)
    cleaned = " ".join(lines).strip()

    upper = cleaned.upper()

    allowed_starts = ("SELECT", "WITH", "EXPLAIN", "PRAGMA")
    if not any(upper.startswith(start) for start in allowed_starts):
        raise QueryNotAllowedError(
            f"Only SELECT, WITH, EXPLAIN, and PRAGMA queries are allowed. "
            f"Got: {query[:100]}"
        )

    # Reject multi-statement queries (semicolon followed by non-whitespace)
    semicolon_idx = cleaned.find(";")
    if semicolon_idx >= 0:
        after = cleaned[semicolon_idx + 1:].strip()
        if after:
            raise QueryNotAllowedError(
                "Multi-statement queries are not allowed."
            )

    return query.strip().rstrip(";")


def get_readonly_connection(db_path: Path) -> sqlite3.Connection:
    """Open a read-only SQLite connection."""
    # Use URI mode for read-only VFS enforcement
    uri = f"file:{db_path}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def get_db_files() -> list[Path]:
    """Return all allowed database paths that actually exist."""
    result = []
    for p in settings.allowed_sqlite_paths:
        path = Path(p)
        if path.exists() and path.is_file():
            result.append(path)
    return result
