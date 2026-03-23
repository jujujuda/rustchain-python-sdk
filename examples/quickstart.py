#!/usr/bin/env python3
"""RustChain SDK — Quickstart example."""

import rustchain

def main():
    print("=" * 50)
    print("RustChain Python SDK — Quickstart")
    print("=" * 50)

    # Note: The primary node uses a self-signed cert.
    # For production, use the public domain or configure certs.
    with rustchain.Client(verify=False) as client:
        # Health check
        health = client.health()
        print(f"\n✓ Connected to node: {health.version}")
        print(f"  Uptime: {health.uptime_s:.0f}s")
        print(f"  Healthy: {health.is_healthy()}")

        # Epoch info
        epoch = client.epoch()
        print(f"\n✓ Epoch {epoch.epoch} / Slot {epoch.slot}")
        print(f"  Total miners: {epoch.enrolled_miners}")
        print(f"  Blocks/epoch: {epoch.blocks_per_epoch}")

        # List miners
        miners = client.miners()
        print(f"\n✓ {len(miners)} miners enrolled:")
        for m in miners[:5]:
            print(f"  - {m.miner[:30]:<30} {m.hardware_type[:25]:<25} {m.antiquity_multiplier}x")
        if len(miners) > 5:
            print(f"  ... and {len(miners) - 5} more")

        # Check balance (test wallet)
        balance = client.balance("RTC2fe3c33c77666ff76a1cd0999fd4466ee81250ff")
        print(f"\n✓ Bounty wallet balance: {balance.amount_rtc} RTC")

    print("\n✓ Done!")


if __name__ == "__main__":
    main()
