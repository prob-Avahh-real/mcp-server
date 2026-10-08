# MCP Server: DB+Chain Bridge

让 Claude 自动读取本地数据库（SQLite / JSON）并执行链上交易（Monad 测试网）。

## Setup

```bash
cd /Users/skat/Projects/archive/devtools/mcp-server
# 兼容软链：cd /Users/skat/Projects/mcp-server
uv sync
cp .env.example .env
# Edit .env with your testnet private key
```

## Dev (MCP Inspector)

```bash
uv run mcp dev server.py
```

## Register with Claude Code

```bash
uv run mcp install server.py:mcp --name "db-chain-bridge" --env-file .env
```

## Tools

### SQLite
- `list_databases` — 列出已配置的数据库
- `list_tables` — 列出表结构和行数
- `query_database` — 执行只读 SELECT 查询

### JSON
- `list_json_files` — 列出已配置的 JSON 文件
- `query_json` — 点路径查询 JSON 数据

### Blockchain (Monad 测试网)
- `get_wallet_info` — 钱包地址和余额
- `check_balance` — 查询任意地址余额
- `estimate_gas` — 估算交易 Gas 费用
- `send_transaction` — **发送 ETH 转账**（需要用户显式确认）
