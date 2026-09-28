"""NetProbe — command-line front door.

Usage:
    python -m netprobe ip  172.24.26.77/20
    python -m netprobe mac 00:15:5D:EA:FB:73
    python -m netprobe me           # best-effort: read this machine's own info
    python -m netprobe ip 10.0.0.5/24 --json
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import socket
import sys

from . import core, doctor
from .ui import bold, cyan, green, rule, yellow


# --------------------------------------------------------------------------- #
def print_ip(r: core.IPReport):
    rule()
    print(bold(f"🕵️  IP report for {r.address}"))
    rule()
    fam = "IPv4" if r.version == 4 else "IPv6"
    scope = "private (inside a home/office)" if r.is_private else "public (out on the open internet)"
    if r.is_loopback:
        scope = "loopback (the machine talking to itself)"
    print(f"  Family        : {fam}")
    print(f"  Scope         : {scope}")

    if r.kind == "host-only":
        print(yellow(
            "\n  You gave me only a house number, no neighborhood (/prefix).\n"
            "  Add one — e.g. '172.24.26.77/20' — and I'll map the whole street."
        ))
        return

    print(f"  Subnet        : /{r.prefixlen}  (mask {r.netmask})")
    print()
    print(bold("  The neighborhood 🏙️"))
    print(f"    Network name    : {r.network_address}")
    if r.broadcast_address:
        print(f"    Broadcast (all) : {r.broadcast_address}")
    if r.first_host:
        print(f"    Houses run from : {r.first_host}  →  {r.last_host}")
    if r.num_usable_hosts is not None:
        print(f"    Usable houses   : {r.num_usable_hosts:,}")
    print()
    print(bold("  This address 📍"))
    print(f"    {r.address} is {green(r.role_of_address)}")


def print_mac(r: core.MACReport):
    rule()
    print(bold(f"🕵️  MAC report for {r.normalized}"))
    rule()
    print(f"  Vendor block (OUI): {r.oui.upper()}")
    if r.vendor:
        tag = {"virtual": "🖥️  VIRTUAL", "network-gear": "📡 NETWORK GEAR",
               "hardware": "🔩 REAL HARDWARE"}.get(r.category, "")
        print(f"  Made by           : {green(r.vendor)}   {tag}")
    else:
        print(f"  Made by           : {yellow('unknown (not in mini-database)')}")
    print()
    print(bold("  The two secret bits 🔑"))
    print(f"    Unicast/Multicast : {'MULTICAST (a group shout)' if r.is_multicast else 'unicast (one machine)'}")
    print(f"    Factory/Local     : {'LOCAL (software-made / randomized)' if r.is_local else 'factory-burned (a real vendor)'}")
    print()
    print(bold("  Hidden IPv6 twin 👯 (EUI-64)"))
    print(f"    {r.ipv6_link_local}")
    print(yellow("    ^ notice your MAC is literally baked inside it — proof the"))
    print(yellow("      network layers are built on top of each other."))
    if r.notes:
        print()
        print(bold("  Detective notes 🗒️"))
        for n in r.notes:
            print(f"    • {n}")


def _local_ipv4():
    """Best-effort: figure out this machine's own outward-facing IPv4."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))   # no packet actually sent for UDP connect
        return s.getsockname()[0]
    except OSError:
        return None
    finally:
        s.close()


def cmd_me():
    print(bold("🕵️  Looking at THIS machine..."))
    ip = _local_ipv4()
    host = socket.gethostname()
    print(f"  Hostname : {host}")
    if ip:
        print(f"  My IPv4  : {ip}")
        print(yellow(
            "\n  Tip: I can't always see your subnet mask from inside a sandbox.\n"
            f"  Run:  python -m netprobe ip {ip}/24   (swap /24 for your real prefix\n"
            "        from `ip addr` on Linux or `ipconfig` on Windows)."
        ))
    else:
        print(yellow("  Couldn't read an outward IP (no network in this sandbox)."))


def build_parser():
    p = argparse.ArgumentParser(
        prog="netprobe",
        description="NetProbe — unwrap IP and MAC addresses in plain English.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    p_ip = sub.add_parser("ip", help="analyze an IP address / subnet, e.g. 172.24.26.77/20")
    p_ip.add_argument("value")
    p_ip.add_argument("--json", action="store_true", help="machine-readable output")

    p_mac = sub.add_parser("mac", help="analyze a MAC address, e.g. 00:15:5D:EA:FB:73")
    p_mac.add_argument("value")
    p_mac.add_argument("--json", action="store_true", help="machine-readable output")

    sub.add_parser("me", help="peek at this machine's own network info")

    p_doc = sub.add_parser("doctor", help="measure your connection and diagnose slowness")
    p_doc.add_argument("--quick", action="store_true",
                       help="skip the download test (uses no data)")
    p_doc.add_argument("--size", type=float, default=10.0, metavar="MB",
                       help="how many MB to download for the speed test (default 10)")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.command == "ip":
            r = core.analyze_ip(args.value)
            print(json.dumps(dataclasses.asdict(r), indent=2)) if args.json else print_ip(r)
        elif args.command == "mac":
            r = core.analyze_mac(args.value)
            print(json.dumps(dataclasses.asdict(r), indent=2)) if args.json else print_mac(r)
        elif args.command == "me":
            cmd_me()
        elif args.command == "doctor":
            doctor.run(size_mb=args.size, quick=args.quick)
    except ValueError as e:
        print(f"❌  {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
