"""SQLite tools: list_databases, list_tables, query_database."""

from pathlib import Path
from mcp.server.fastmcp import FastMCP, Context

from src.adapters.database import (
    get_db_files,
    validate_db_path,
    validate_readonly_query,
    get_readonly_connection,
    DatabaseAccessError,
    QueryNotAllowedError,
)
from src.models import DatabaseInfo, TableInfo, ColumnInfo, QueryResult


def register_sqlite_tools(mcp: FastMCP) -> None:
    """Register SQLite tools on the FastMCP instance."""

    @mcp.tool()
    def list_databases() -> list[DatabaseInfo]:
        """列出所有已配置的本地 SQLite 数据库，包含路径、文件大小和表数量。

        Returns a list of database metadata.
        Use this first to discover which databases are available.
        """
        results = []
        for path in get_db_files():
            try:
                conn = get_readonly_connection(path)
                tables = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
                conn.close()
                table_count = len(tables)
                size = path.stat().st_size
                results.append(
                    DatabaseInfo(
                        path=str(path),
                        size_bytes=size,
                        table_count=table_count,
                    )
                )
            except Exception:
                # Skip databases we can't open
                pass
        return results

    @mcp.tool()
    def list_tables(db_path: str) -> list[TableInfo]:
        """列出指定数据库中所有表的名称、列信息和行数。

        Use this to explore the schema before querying.

        Args:
            db_path: Absolute path to the SQLite database
        """
        validated = validate_db_path(db_path)
        conn = get_readonly_connection(validated)
        tables = []

        try:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()

            for (table_name,) in rows:
                # Get column info
                cols = conn.execute(f'PRAGMA table_info("{table_name}")').fetchall()
                columns = [
                    ColumnInfo(
                        name=c["name"],
                        type=c["type"],
                        nullable=not bool(c["notnull"]),
                        primary_key=bool(c["pk"]),
                    )
                    for c in cols
                ]

                # Get approximate row count
                count_row = conn.execute(
                    f'SELECT COUNT(*) FROM "{table_name}"'
                ).fetchone()
                row_count = count_row[0] if count_row else 0

                tables.append(
                    TableInfo(name=table_name, columns=columns, row_count=row_count)
                )
        finally:
            conn.close()

        return tables

    @mcp.tool()
    def query_database(
        db_path: str, query: str, limit: int = 100
    ) -> QueryResult:
        """在 SQLite 数据库上执行只读 SELECT 查询。

        Only SELECT, WITH, EXPLAIN, and PRAGMA queries are allowed.
        Multi-statement queries are rejected.
        Results are automatically truncated to the limit (default 100 rows).

        Args:
            db_path: Absolute path to the SQLite database
            query: A read-only SQL query (SELECT, WITH, EXPLAIN, or PRAGMA)
            limit: Maximum number of rows to return (default 100)
        """
        validated = validate_db_path(db_path)
        validated_query = validate_readonly_query(query)

        conn = get_readonly_connection(validated)
        try:
            # Add LIMIT if not present (for SELECT statements only)
            upper = validated_query.upper()
            needs_limit = upper.startswith("SELECT") and "LIMIT" not in upper

            final_query = validated_query
            if needs_limit:
                final_query = f"{validated_query} LIMIT {limit}"

            cursor = conn.execute(final_query)
            columns = [d[0] for d in cursor.description] if cursor.description else []
            rows = [list(row) for row in cursor.fetchall()]
            row_count = len(rows)

            truncated = needs_limit and row_count >= limit

            return QueryResult(
                columns=columns,
                rows=rows,
                row_count=row_count,
                truncated=truncated,
            )
        finally:
            conn.close()
