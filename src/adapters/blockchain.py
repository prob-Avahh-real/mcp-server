"""Blockchain adapter: Web3 provider and wallet management."""

from web3 import Web3
from src.config import settings


class BlockchainNotConfiguredError(Exception):
    """Raised when the blockchain adapter is not configured (no private key)."""


class TransactionLimitError(Exception):
    """Raised when a transaction exceeds safety limits."""


class BlockchainAdapter:
    """Manages Web3 connection and wallet for Monad testnet."""

    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(settings.monad_rpc_url))
        self._wallet = None
        self._tx_count = 0

        if settings.has_wallet:
            self._wallet = self.w3.eth.account.from_key(settings.private_key)

    @property
    def is_ready(self) -> bool:
        """Whether the adapter is ready for transactions."""
        return self._wallet is not None and self.w3.is_connected()

    @property
    def wallet_address(self) -> str | None:
        """The wallet address (public key), or None if not configured."""
        return self._wallet.address if self._wallet else None

    @property
    def chain_id(self) -> int:
        return settings.monad_chain_id

    def get_network_name(self) -> str:
        """Return a human-readable network name."""
        # Monad testnet
        if settings.monad_chain_id == 10143:
            return "Monad Testnet"
        return f"Chain {settings.monad_chain_id}"

    def get_balance_wei(self, address: str | None = None) -> int:
        """Get the ETH balance of an address in wei."""
        addr = address or self.wallet_address
        if not addr:
            raise BlockchainNotConfiguredError("No wallet address configured")
        return self.w3.eth.get_balance(self.w3.to_checksum_address(addr))

    def get_balance_eth(self, address: str | None = None) -> float:
        """Get the ETH balance as a float."""
        return float(self.w3.from_wei(self.get_balance_wei(address), "ether"))

    def validate_transaction(self, to_address: str, amount_eth: float) -> None:
        """Validate a transaction against safety limits.

        Raises TransactionLimitError if limits are exceeded.
        """
        if not self.is_ready:
            raise BlockchainNotConfiguredError(
                "Wallet not configured. Set PRIVATE_KEY env variable."
            )

        if amount_eth <= 0:
            raise TransactionLimitError("Amount must be greater than 0")

        if amount_eth > settings.max_single_tx_eth:
            raise TransactionLimitError(
                f"Amount {amount_eth} ETH exceeds max single tx "
                f"{settings.max_single_tx_eth} ETH"
            )

        if self._tx_count >= settings.max_daily_tx_count:
            raise TransactionLimitError(
                f"Daily transaction limit of {settings.max_daily_tx_count} reached"
            )

        # Validate address format
        if not self.w3.is_address(to_address):
            raise TransactionLimitError(f"Invalid address: {to_address}")

    def estimate_gas(self, to_address: str, amount_eth: float) -> dict:
        """Estimate gas for a simple ETH transfer.

        Returns dict with gas_units, gas_price_gwei, estimated_cost_eth.
        """
        if not self.is_ready:
            raise BlockchainNotConfiguredError("Wallet not configured")

        amount_wei = self.w3.to_wei(amount_eth, "ether")
        tx = {
            "from": self._wallet.address,
            "to": self.w3.to_checksum_address(to_address),
            "value": amount_wei,
            "chainId": settings.monad_chain_id,
        }

        gas_units = self.w3.eth.estimate_gas(tx)
        gas_price_wei = self.w3.eth.gas_price
        gas_price_gwei = float(self.w3.from_wei(gas_price_wei, "gwei"))
        cost_wei = gas_units * gas_price_wei
        cost_eth = float(self.w3.from_wei(cost_wei, "ether"))

        return {
            "gas_units": gas_units,
            "gas_price_gwei": gas_price_gwei,
            "estimated_cost_eth": cost_eth,
            "estimated_cost_wei": cost_wei,
        }

    def send_transaction(self, to_address: str, amount_eth: float) -> dict:
        """Send an ETH transaction on Monad testnet.

        Returns dict with success, tx_hash, from_address, to_address, etc.
        """
        self.validate_transaction(to_address, amount_eth)

        amount_wei = self.w3.to_wei(amount_eth, "ether")
        nonce = self.w3.eth.get_transaction_count(self._wallet.address)

        tx = {
            "from": self._wallet.address,
            "to": self.w3.to_checksum_address(to_address),
            "value": amount_wei,
            "gas": self.w3.eth.estimate_gas(
                {
                    "from": self._wallet.address,
                    "to": self.w3.to_checksum_address(to_address),
                    "value": amount_wei,
                }
            ),
            "gasPrice": self.w3.eth.gas_price,
            "nonce": nonce,
            "chainId": settings.monad_chain_id,
        }

        signed = self._wallet.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)

        self._tx_count += 1

        return {
            "success": True,
            "tx_hash": tx_hash.hex(),
            "from_address": self._wallet.address,
            "to_address": self.w3.to_checksum_address(to_address),
            "amount_eth": amount_eth,
            "chain_id": settings.monad_chain_id,
            "block_explorer_url": f"https://testnet.monadexplorer.com/tx/{tx_hash.hex()}",
            "error": None,
        }


# Singleton adapter instance
_blockchain_adapter: BlockchainAdapter | None = None


def get_blockchain_adapter() -> BlockchainAdapter:
    """Get or create the blockchain adapter singleton."""
    global _blockchain_adapter
    if _blockchain_adapter is None:
        _blockchain_adapter = BlockchainAdapter()
    return _blockchain_adapter
