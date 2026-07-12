"""Pydantic models for structured MCP tool return types."""

from typing import Any
from pydantic import BaseModel, Field


# --- SQLite Models ---

class DatabaseInfo(BaseModel):
    path: str = Field(description="Absolute path to the database file")
    size_bytes: int = Field(description="File size in bytes")
    table_count: int = Field(description="Number of tables in the database")


class ColumnInfo(BaseModel):
    name: str = Field(description="Column name")
    type: str = Field(description="Column data type")
    nullable: bool = Field(description="Whether the column allows NULL")
    primary_key: bool = Field(description="Whether the column is a primary key")


class TableInfo(BaseModel):
    name: str = Field(description="Table name")
    columns: list[ColumnInfo] = Field(description="Column definitions")
    row_count: int = Field(description="Approximate number of rows")


class QueryResult(BaseModel):
    columns: list[str] = Field(description="Column names in result order")
    rows: list[list[Any]] = Field(description="Data rows")
    row_count: int = Field(description="Number of rows returned")
    truncated: bool = Field(description="Whether results were truncated to the limit")


# --- JSON Models ---

class JSONFileInfo(BaseModel):
    path: str = Field(description="Absolute path to the JSON file")
    size_bytes: int = Field(description="File size in bytes")
    top_level_type: str = Field(description="Type of the top-level JSON value (object, array, etc.)")
    top_level_keys: list[str] = Field(
        description="Top-level keys if object, or first N indices if array"
    )


class JSONQueryResult(BaseModel):
    file_path: str = Field(description="Absolute path to the queried file")
    query_path: str = Field(description="The dot-path that was queried")
    value: Any = Field(description="The resolved value at the query path")
    value_type: str = Field(description="Type of the resolved value")
    truncated: bool = Field(description="Whether the result was truncated (for lists)")


# --- Blockchain Models ---

class WalletInfo(BaseModel):
    address: str = Field(description="Wallet address (public)")
    chain_id: int = Field(description="Chain ID")
    network_name: str = Field(description="Network name (e.g., Monad Testnet)")
    balance_eth: float = Field(description="ETH balance")
    balance_wei: int = Field(description="Balance in wei")
    rpc_url: str = Field(description="RPC endpoint URL")


class BalanceResult(BaseModel):
    address: str = Field(description="Address queried")
    balance_eth: float = Field(description="ETH balance")
    balance_wei: int = Field(description="Balance in wei")


class GasEstimate(BaseModel):
    gas_units: int = Field(description="Estimated gas units")
    gas_price_gwei: float = Field(description="Current gas price in Gwei")
    estimated_cost_eth: float = Field(description="Estimated total cost in ETH")
    estimated_cost_gwei: int = Field(description="Estimated total cost in Gwei")


class TransactionResult(BaseModel):
    success: bool = Field(description="Whether the transaction was submitted")
    tx_hash: str | None = Field(description="Transaction hash")
    from_address: str = Field(description="Sender address")
    to_address: str = Field(description="Recipient address")
    amount_eth: float = Field(description="Amount sent in ETH")
    chain_id: int = Field(description="Chain ID")
    block_explorer_url: str | None = Field(description="Link to view on block explorer")
    error: str | None = Field(description="Error message if failed")
