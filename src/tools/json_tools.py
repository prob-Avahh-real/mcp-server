"""JSON file tools: list_json_files, query_json."""

import json
from pathlib import Path
from typing import Any
from mcp.server.fastmcp import FastMCP

from src.config import settings
from src.models import JSONFileInfo, JSONQueryResult


class JSONAccessError(Exception):
    """Raised when access to a JSON file is denied."""


def _validate_json_path(file_path: str) -> Path:
    """Resolve path and check against the JSON allowlist."""
    resolved = Path(file_path).resolve()

    for allowed in settings.allowed_json_paths:
        if Path(allowed).resolve() == resolved:
            return resolved

    raise JSONAccessError(
        f"JSON file path not allowed: {file_path}. "
        f"Allowed paths: {settings.allowed_json_paths}"
    )


def _resolve_dot_path(data: Any, path: str) -> Any:
    """Resolve a dot-separated path against nested dicts and lists.

    Examples:
        "jobs.0.title" -> data["jobs"][0]["title"]
        "name" -> data["name"]
    """
    parts = path.split(".")
    current = data
    for part in parts:
        if isinstance(current, list):
            try:
                idx = int(part)
                current = current[idx]
            except (ValueError, IndexError) as e:
                raise ValueError(
                    f"Invalid list index '{part}' at path '{path}'"
                ) from e
        elif isinstance(current, dict):
            if part not in current:
                raise ValueError(
                    f"Key '{part}' not found at path '{path}'. "
                    f"Available keys: {list(current.keys())[:20]}"
                )
            current = current[part]
        else:
            raise ValueError(
                f"Cannot traverse into {type(current).__name__} at segment "
                f"'{part}' (path: {path})"
            )
    return current


def _get_top_level_info(data: Any) -> tuple[str, list[str]]:
    """Get the top-level type and keys/indices summary."""
    if isinstance(data, dict):
        type_name = "object"
        keys = list(data.keys())[:20]
        return type_name, keys
    elif isinstance(data, list):
        type_name = "array"
        keys = [str(i) for i in range(min(len(data), 5))]
        return type_name, keys
    else:
        return type(data).__name__, []


def _truncate_value(value: Any, limit: int) -> tuple[Any, bool]:
    """Truncate a list value to the limit. Returns (truncated_value, was_truncated)."""
    if isinstance(value, list) and len(value) > limit:
        return value[:limit], True
    if isinstance(value, str) and len(value) > limit * 1000:
        return value[: limit * 1000] + "...", True
    return value, False


def register_json_tools(mcp: FastMCP) -> None:
    """Register JSON tools on the FastMCP instance."""

    @mcp.tool()
    def list_json_files() -> list[JSONFileInfo]:
        """列出所有已配置的本地 JSON 数据文件，包含路径、大小和顶层结构。

        Use this first to discover which JSON data files are available.
        """
        results = []
        for p in settings.allowed_json_paths:
            path = Path(p)
            if not path.exists() or not path.is_file():
                continue
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                top_type, top_keys = _get_top_level_info(data)
                results.append(
                    JSONFileInfo(
                        path=str(path),
                        size_bytes=path.stat().st_size,
                        top_level_type=top_type,
                        top_level_keys=top_keys,
                    )
                )
            except Exception:
                pass
        return results

    @mcp.tool()
    def query_json(
        file_path: str, query_path: str, limit: int = 50
    ) -> JSONQueryResult:
        """通过 . 分隔的路径（如 'jobs.0.title'）查询 JSON 文件中的特定数据。

        Use this to read specific values from a JSON file without loading the entire file.

        Args:
            file_path: Absolute path to the JSON file
            query_path: Dot-separated path to the value (e.g., "users.0.name"). Use "" for the root.
            limit: Maximum number of items to return if the result is a list (default 50)
        """
        validated = _validate_json_path(file_path)

        with open(validated, "r", encoding="utf-8") as f:
            data = json.load(f)

        # If no path provided, return the root
        if not query_path:
            value = data
        else:
            value = _resolve_dot_path(data, query_path)

        truncated_value, was_truncated = _truncate_value(value, limit)

        return JSONQueryResult(
            file_path=str(validated),
            query_path=query_path or "(root)",
            value=truncated_value,
            value_type=type(value).__name__,
            truncated=was_truncated,
        )
