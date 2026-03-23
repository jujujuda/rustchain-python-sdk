# RustChain Python SDK

A Python SDK for interacting with RustChain nodes — the Proof-of-Antiquity blockchain.

## Features

- 🔗 Full coverage of RustChain REST API endpoints
- ⚡ Sync and async clients (httpx-based)
- 💰 Wallet balance checks, transfers, and transaction history
- ⛏️ Miner listing and attestation status
- 📊 Epoch and block explorer data
- 🛡️ Typed exceptions for error handling
- ✅ 20+ unit tests

## Installation

```bash
pip install rustchain
```

For async with HTTP/2 support:

```bash
pip install rustchain[async]
```

## Quickstart

```python
import rustchain

# Create client (defaults to primary node: https://50.28.86.131)
client = rustchain.Client()

# Check node health
health = client.health()
print(f"Node: {health.version} | Healthy: {health.is_healthy()}")

# Get current epoch
epoch = client.epoch()
print(f"Epoch {epoch.epoch}, Slot {epoch.slot}")
print(f"Total miners: {epoch.enrolled_miners}")

# Check your balance
balance = client.balance("my-wallet-name")
print(f"Balance: {balance.amount_rtc} RTC")

# List all miners
for miner in client.miners():
    print(f"  {miner.miner}: {miner.hardware_type} ({miner.antiquity_multiplier}x antiquity)")

# Check attestation status
status = client.attestation_status("my-miner")
if status:
    print(f"Attested: {status.enrolled}, multiplier: {status.antiquity_multiplier}")

client.close()
```

## Async Usage

```python
import asyncio
from rustchain import AsyncClient

async def main():
    async with AsyncClient() as client:
        health, epoch = await asyncio.gather(
            client.health(),
            client.epoch(),
        )
        print(f"Epoch {epoch.epoch} | Node {health.version}")

asyncio.run(main())
```

## API Reference

### `Client`

| Method | Description |
|--------|-------------|
| `health()` | Returns `Health` — node status, version, uptime |
| `epoch()` | Returns `Epoch` — current slot, epoch number, supply |
| `miners()` | Returns `List[Miner]` — all enrolled miners |
| `miner(miner_id)` | Returns `Miner` or `None` |
| `balance(wallet_id)` | Returns `Balance` — RTC balance for a wallet |
| `attestation_status(miner_id)` | Returns `AttestationStatus` for a miner |
| `submit_attestation(miner_id, signature)` | Submit an attestation |
| `transfer(from, to, amount, signature)` | Signed RTC transfer → `TransferResult` |
| `blocks(limit=20)` | Returns `List[Block]` — recent blocks |
| `transactions(address, limit=20)` | Returns transaction history |

### Exceptions

| Exception | When |
|-----------|------|
| `RustChainError` | Base exception |
| `APIError` | API returns an error status |
| `NodeUnavailableError` | Cannot reach the node |
| `ValidationError` | Invalid input parameters |
| `TransferError` | Transfer failed |

## CLI Wrapper

```bash
# Install with CLI extras
pip install rustchain[cli]

# Check balance
rustchain balance my-wallet

# Check epoch
rustchain epoch

# List miners
rustchain miners
```

## Wallet

My RTC wallet for bounty payouts: `RTC2fe3c33c77666ff76a1cd0999fd4466ee81250ff`

## License

MIT
