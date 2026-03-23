"""CLI wrapper for RustChain SDK — rustchain CLI command."""

import argparse
import sys
from rustchain import Client, AsyncClient


def cmd_health(args):
    with Client() as client:
        h = client.health()
        print(f"Node version : {h.version}")
        print(f"Healthy      : {h.is_healthy()}")
        print(f"Uptime       : {h.uptime_s:.0f}s")
        print(f"DB RW        : {h.db_rw}")
        print(f"Tip age slots: {h.tip_age_slots}")


def cmd_epoch(args):
    with Client() as client:
        ep = client.epoch()
        print(f"Epoch             : {ep.epoch}")
        print(f"Slot              : {ep.slot}")
        print(f"Blocks per epoch  : {ep.blocks_per_epoch}")
        print(f"Enrolled miners  : {ep.enrolled_miners}")
        print(f"Total supply      : {ep.total_supply_rtc} RTC")
        print(f"Epoch pot         : {ep.epoch_pot} RTC")


def cmd_balance(args):
    with Client() as client:
        bal = client.balance(args.wallet)
        print(f"Wallet : {bal.miner_id}")
        print(f"Balance: {bal.amount_rtc} RTC")


def cmd_miners(args):
    with Client() as client:
        miners = client.miners()
        print(f"Total miners: {len(miners)}\n")
        for m in miners:
            active = "✓" if m.is_active() else "✗"
            print(f"  [{active}] {m.miner}")
            print(f"       {m.hardware_type} | arch={m.device_arch} | {m.antiquity_multiplier}x antiquity")


def cmd_miner(args):
    with Client() as client:
        m = client.miner(args.miner_id)
        if m is None:
            print(f"Miner '{args.miner_id}' not found.")
            sys.exit(1)
        print(f"Miner: {m.miner}")
        print(f"Hardware: {m.hardware_type}")
        print(f"Architecture: {m.device_arch}")
        print(f"Family: {m.device_family}")
        print(f"Antiquity multiplier: {m.antiquity_multiplier}x")
        print(f"Entropy score: {m.entropy_score}")
        print(f"Active: {m.is_active()}")
        if m.first_attest:
            from datetime import datetime
            print(f"First attest: {datetime.fromtimestamp(m.first_attest)}")
        if m.last_attest:
            from datetime import datetime
            print(f"Last attest:  {datetime.fromtimestamp(m.last_attest)}")


def cmd_attestation(args):
    with Client() as client:
        s = client.attestation_status(args.miner_id)
        if s is None:
            print(f"No attestation data for '{args.miner_id}'.")
            sys.exit(1)
        print(f"Miner ID: {s.miner_id}")
        print(f"Enrolled: {s.enrolled}")
        print(f"Antiquity multiplier: {s.antiquity_multiplier}x")
        print(f"Device arch: {s.device_arch}")


def main():
    parser = argparse.ArgumentParser(prog="rustchain", description="RustChain CLI")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("health", help="Show node health")
    sub.add_parser("epoch", help="Show current epoch info")

    p_balance = sub.add_parser("balance", help="Check wallet balance")
    p_balance.add_argument("wallet", help="Wallet / miner ID")

    sub.add_parser("miners", help="List all enrolled miners")

    p_miner = sub.add_parser("miner", help="Show a specific miner")
    p_miner.add_argument("miner_id", help="Miner ID")

    p_attest = sub.add_parser("attestation", help="Check attestation status")
    p_attest.add_argument("miner_id", help="Miner ID")

    args = parser.parse_args()

    commands = {
        "health": cmd_health,
        "epoch": cmd_epoch,
        "balance": cmd_balance,
        "miners": cmd_miners,
        "miner": cmd_miner,
        "attestation": cmd_attestation,
    }

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    try:
        commands[args.command](args)
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
