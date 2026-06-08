"""CLI: daffodil-kit pair | start | status"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

import httpx

from . import __version__
from .connector import connect_to_api
from .daemon import run_daemon
from .security import (
    get_device_secret,
    get_or_create_device_id,
    load_config,
    store_pairing,
)


def cmd_pair(args: argparse.Namespace) -> int:
    api_url = args.api.rstrip("/")
    code = args.code.strip()
    device_id = get_or_create_device_id()
    try:
        resp = httpx.post(
            f"{api_url}/api/kit/pair/confirm",
            json={"code": code, "device_id": device_id, "device_name": args.name or "desktop"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        store_pairing(
            device_secret=data["device_secret"],
            api_url=api_url,
            user_id=data["user_id"],
            allowed_roots=args.roots.split(",") if args.roots else None,
        )
        print(f"Paired successfully. Device ID: {device_id}")
        return 0
    except httpx.HTTPError as e:
        print(f"Pairing failed: {e}", file=sys.stderr)
        return 1


def cmd_start(args: argparse.Namespace) -> int:
    cfg = load_config()
    if not cfg.get("device_secret") and not args.dev:
        print("Not paired. Run: daffodil-kit pair --api URL --code CODE", file=sys.stderr)
        return 1
    try:
        if args.mode == "local":
            asyncio.run(run_daemon(host=args.host, port=args.port))
        else:
            asyncio.run(connect_to_api())
    except KeyboardInterrupt:
        return 0
    return 0


def _vault_set(args: argparse.Namespace) -> int:
    from .vault import set_system_password
    r = set_system_password(args.password, args.label)
    print(json.dumps(r, indent=2))
    return 0


def _vault_status() -> int:
    from .vault import vault_status
    print(json.dumps(vault_status(), indent=2))
    return 0


def cmd_status(_args: argparse.Namespace) -> int:
    cfg = load_config()
    print(json.dumps({
        "device_id": cfg.get("device_id"),
        "paired": bool(cfg.get("device_secret")),
        "api_url": cfg.get("api_url"),
        "user_id": cfg.get("user_id"),
        "allowed_roots": cfg.get("allowed_roots"),
    }, indent=2))
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="daffodil-kit", description="Daffodil desktop kit daemon")
    sub = parser.add_subparsers(dest="command", required=True)

    pair_p = sub.add_parser("pair", help="Pair with Daffodil API")
    pair_p.add_argument("--api", required=True, help="API base URL")
    pair_p.add_argument("--code", required=True, help="6-digit pairing code")
    pair_p.add_argument("--name", default="desktop", help="Device display name")
    pair_p.add_argument("--roots", help="Comma-separated allowed file roots")
    pair_p.set_defaults(func=cmd_pair)

    start_p = sub.add_parser("start", help="Start local daemon")
    start_p.add_argument("--host", default="127.0.0.1")
    start_p.add_argument("--port", type=int, default=9477)
    start_p.add_argument("--dev", action="store_true", help="Allow unpaired dev mode")
    start_p.add_argument("--mode", choices=["cloud", "local"], default="cloud", help="cloud=connect to API, local=standalone WS")
    start_p.set_defaults(func=cmd_start)

    status_p = sub.add_parser("status", help="Show pairing status")
    status_p.set_defaults(func=cmd_status)

    ver_p = sub.add_parser("version", help="Show installed CopyCat Kit version")
    ver_p.set_defaults(func=lambda _: (print(__version__), 0)[1])

    vault_p = sub.add_parser("vault", help="Local automation password (never sent to cloud)")
    vault_sub = vault_p.add_subparsers(dest="vault_cmd", required=True)
    vset = vault_sub.add_parser("set", help="Store system password locally")
    vset.add_argument("password", help="Password for sudo/UAC prompts during CopyCat replay")
    vset.add_argument("--label", default="sudo")
    vset.set_defaults(func=lambda a: _vault_set(a))
    vstat = vault_sub.add_parser("status", help="Vault status")
    vstat.set_defaults(func=lambda _: _vault_status())

    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
