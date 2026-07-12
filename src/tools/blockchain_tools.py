"""Blockchain tools: wallet info, balance check, gas estimate, send ETH."""

from mcp.server.fastmcp import FastMCP

from src.adapters.blockchain import (
    get_blockchain_adapter,
    BlockchainNotConfiguredError,
    TransactionLimitError,
)
from src.models import WalletInfo, BalanceResult, GasEstimate, TransactionResult


def register_blockchain_tools(mcp: FastMCP) -> None:
    """Register blockchain tools on the FastMCP instance."""

    adapter = get_blockchain_adapter()

    @mcp.tool()
    def get_wallet_info() -> WalletInfo:
        """获取当前配置的钱包信息：地址、链 ID、网络名称、ETH 余额。

        This is read-only — no private key is ever exposed.
        Use this to check your wallet status on Monad testnet.
        """
        try:
            balance_wei = adapter.get_balance_wei()
            balance_eth = adapter.get_balance_eth()
        except BlockchainNotConfiguredError:
            balance_wei = 0
            balance_eth = 0.0

        return WalletInfo(
            address=adapter.wallet_address or "NOT_CONFIGURED",
            chain_id=adapter.chain_id,
            network_name=adapter.get_network_name(),
            balance_eth=balance_eth,
            balance_wei=balance_wei,
            rpc_url=adapter.w3.provider.endpoint_uri or "unknown",
        )

    @mcp.tool()
    def check_balance(address: str = "") -> BalanceResult:
        """查询 Monad 测试网上任意地址的 ETH 余额。

        If no address is provided, checks the configured wallet's balance.

        Args:
            address: Ethereum address to check. Leave empty to check your wallet.
        """
        addr = address or adapter.wallet_address
        if not addr:
            return BalanceResult(
                address="NO_WALLET",
                balance_eth=0.0,
                balance_wei=0,
            )

        balance_wei = adapter.get_balance_wei(addr)
        balance_eth = adapter.get_balance_eth(addr)

        return BalanceResult(
            address=adapter.w3.to_checksum_address(addr),
            balance_eth=balance_eth,
            balance_wei=balance_wei,
        )

    @mcp.tool()
    def estimate_gas(to_address: str, amount_eth: float) -> GasEstimate:
        """估算在 Monad 测试网上发送 ETH 的 Gas 费用。

        Use this before calling send_transaction to see the estimated cost.

        Args:
            to_address: Recipient Ethereum address
            amount_eth: Amount of ETH to send
        """
        try:
            result = adapter.estimate_gas(to_address, amount_eth)
            return GasEstimate(
                gas_units=result["gas_units"],
                gas_price_gwei=result["gas_price_gwei"],
                estimated_cost_eth=result["estimated_cost_eth"],
                estimated_cost_gwei=result["estimated_cost_wei"],
            )
        except (BlockchainNotConfiguredError, TransactionLimitError) as e:
            return GasEstimate(
                gas_units=0,
                gas_price_gwei=0.0,
                estimated_cost_eth=0.0,
                estimated_cost_gwei=0,
            )

    @mcp.tool()
    def send_transaction(
        to_address: str,
        amount_eth: float,
        reason: str,
        confirmation: str,
    ) -> TransactionResult:
        """在 Monad 测试网上发送 ETH 交易。

        **IMPORTANT: This tool requires explicit user confirmation.**
        The `confirmation` parameter MUST equal the literal string "CONFIRM".
        Before calling this tool, you MUST:
        1. Explain to the user what you're about to do (amount, recipient, reason)
        2. Get explicit approval from the user
        3. Only then call this tool with confirmation="CONFIRM"

        Args:
            to_address: Recipient Ethereum address (must be a valid 0x... address)
            amount_eth: Amount of ETH to send (max 0.1 by default)
            reason: Human-readable explanation of why this transaction is being sent
            confirmation: Must be exactly "CONFIRM" — acts as a safety guard
        """
        if confirmation != "CONFIRM":
            return TransactionResult(
                success=False,
                tx_hash=None,
                from_address=adapter.wallet_address or "NO_WALLET",
                to_address=to_address,
                amount_eth=amount_eth,
                chain_id=adapter.chain_id,
                block_explorer_url=None,
                error=(
                    "Confirmation required. You must ask the user to approve "
                    "this transaction, then call send_transaction again with "
                    "confirmation='CONFIRM'."
                ),
            )

        try:
            result = adapter.send_transaction(to_address, amount_eth)
            return TransactionResult(**result)
        except (BlockchainNotConfiguredError, TransactionLimitError) as e:
            return TransactionResult(
                success=False,
                tx_hash=None,
                from_address=adapter.wallet_address or "NO_WALLET",
                to_address=to_address,
                amount_eth=amount_eth,
                chain_id=adapter.chain_id,
                block_explorer_url=None,
                error=str(e),
            )
