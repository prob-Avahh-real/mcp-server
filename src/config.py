"""Configuration loaded from environment variables."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def _parse_path_list(env_val: str) -> list[str]:
    """Parse a comma-separated list of absolute paths."""
    if not env_val:
        return []
    return [p.strip() for p in env_val.split(",") if p.strip()]


class Settings:
    # --- Blockchain ---
    private_key: str = os.getenv("PRIVATE_KEY", "")
    monad_rpc_url: str = os.getenv(
        "MONAD_RPC_URL", "https://testnet-rpc.monad.xyz"
    )
    monad_chain_id: int = int(os.getenv("MONAD_CHAIN_ID", "10143"))

    # --- Security Limits ---
    max_single_tx_eth: float = float(os.getenv("MAX_SINGLE_TX_ETH", "0.1"))
    max_daily_tx_count: int = int(os.getenv("MAX_DAILY_TX_COUNT", "5"))

    # --- Allowed Paths ---
    allowed_sqlite_paths: list[str] = _parse_path_list(
        os.getenv("ALLOWED_SQLITE_PATHS", "")
    )
    allowed_json_paths: list[str] = _parse_path_list(
        os.getenv("ALLOWED_JSON_PATHS", "")
    )

    @property
    def has_wallet(self) -> bool:
        """Whether a private key is configured."""
        return bool(self.private_key and self.private_key != "your_testnet_private_key_here")


settings = Settings()
