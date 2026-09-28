"""NetProbe — the brains.

Two jobs:
  1. analyze_ip()  -> unwrap an IP address + subnet (the "neighborhood").
  2. analyze_mac() -> unwrap a MAC address (the factory name-tag), including
     who made the card and the hidden EUI-64 IPv6 trick.

Pure Python standard library. No installs, runs anywhere.
"""
from __future__ import annotations

import ipaddress
from dataclasses import dataclass, field
from typing import Optional

from .oui import lookup


# --------------------------------------------------------------------------- #
#  IP / subnet analysis
# --------------------------------------------------------------------------- #
@dataclass
class IPReport:
    raw: str
    version: int
    is_private: bool
    is_loopback: bool
    kind: str                       # "host+subnet" or "host-only"
    address: str
    prefixlen: Optional[int] = None
    netmask: Optional[str] = None
    network_address: Optional[str] = None
    broadcast_address: Optional[str] = None
    first_host: Optional[str] = None
    last_host: Optional[str] = None
    num_usable_hosts: Optional[int] = None
    role_of_address: Optional[str] = None   # where THIS address sits in the block


def analyze_ip(text: str) -> IPReport:
    """Accept '172.24.26.77/20', '10.0.0.5', or a bare '2001:db8::1/64'."""
    text = text.strip()

    if "/" in text:
        iface = ipaddress.ip_interface(text)      # keeps the host bits
        net = iface.network                        # the surrounding block
        addr = iface.ip
        version = addr.version

        first_host = last_host = broadcast = None
        num_usable = net.num_addresses
        if version == 4 and net.prefixlen <= 30:
            broadcast = str(net.broadcast_address)
            hosts = list(_bounded_hosts(net))
            if hosts:
                first_host, last_host = str(hosts[0]), str(hosts[1])
            num_usable = max(net.num_addresses - 2, 0)   # minus network + broadcast

        role = _role_of(addr, net)

        return IPReport(
            raw=text,
            version=version,
            is_private=addr.is_private,
            is_loopback=addr.is_loopback,
            kind="host+subnet",
            address=str(addr),
            prefixlen=net.prefixlen,
            netmask=str(net.netmask),
            network_address=str(net.network_address),
            broadcast_address=broadcast,
            first_host=first_host,
            last_host=last_host,
            num_usable_hosts=num_usable,
            role_of_address=role,
        )

    addr = ipaddress.ip_address(text)
    return IPReport(
        raw=text,
        version=addr.version,
        is_private=addr.is_private,
        is_loopback=addr.is_loopback,
        kind="host-only",
        address=str(addr),
    )


def _bounded_hosts(net):
    """First and last usable host without materialising a /8 (16M addrs)."""
    first = net.network_address + 1
    last = net.broadcast_address - 1
    return first, last


def _role_of(addr, net) -> str:
    if addr == net.network_address:
        return "the network address (names the whole neighborhood — not a real house)"
    if net.version == 4 and addr == net.broadcast_address:
        return "the broadcast address (shouts to EVERY house at once — not a real house)"
    if addr == net.network_address + 1:
        return "the first usable host (very often the router / gateway — the front gate)"
    return "a normal host inside the neighborhood"


def same_subnet(a: str, b: str, cidr: str) -> bool:
    """Are two addresses in the same block? (Answers 'can they talk directly?')"""
    net = ipaddress.ip_interface(f"{a}/{cidr}").network
    return ipaddress.ip_address(b) in net


# --------------------------------------------------------------------------- #
#  MAC analysis
# --------------------------------------------------------------------------- #
@dataclass
class MACReport:
    raw: str
    normalized: str
    oui: str
    vendor: Optional[str]
    category: Optional[str]          # virtual / hardware / network-gear / None
    is_multicast: bool
    is_local: bool                   # locally administered (randomized/virtual)
    ipv6_link_local: str
    notes: list = field(default_factory=list)


def _hexbytes(mac: str):
    cleaned = mac.replace(":", "").replace("-", "").replace(".", "").strip()
    if len(cleaned) != 12 or any(c not in "0123456789abcdefABCDEF" for c in cleaned):
        raise ValueError(f"'{mac}' is not a valid 48-bit MAC address")
    return [int(cleaned[i : i + 2], 16) for i in range(0, 12, 2)]


def analyze_mac(mac: str) -> MACReport:
    b = _hexbytes(mac)
    normalized = ":".join(f"{x:02x}" for x in b)
    oui6 = "".join(f"{x:02X}" for x in b[:3])

    vendor, category = lookup(oui6)

    # The two secret bits live in the very first byte:
    #   bit 0 (value 1) -> multicast if set, unicast if clear
    #   bit 1 (value 2) -> locally-administered if set, factory-burned if clear
    is_multicast = bool(b[0] & 0b0000_0001)
    is_local = bool(b[0] & 0b0000_0010)

    notes = []
    if is_local and not vendor:
        notes.append(
            "The 'locally administered' bit is ON — this address was made up by "
            "software (a randomized phone Wi-Fi MAC, or a virtual machine), so "
            "there's no real factory vendor to look up."
        )
    if is_multicast:
        notes.append(
            "The 'multicast' bit is ON — this isn't one machine's card, it's a "
            "'shout to a group' address."
        )
    if category == "virtual":
        notes.append(
            "Vendor is a VIRTUAL-machine maker — you're looking at a fake NIC "
            "inside a VM/hypervisor, not a physical card. (This is exactly how "
            "you tell 'I'm on WSL' from 'I'm on my real home Wi-Fi'.)"
        )

    return MACReport(
        raw=mac,
        normalized=normalized,
        oui=":".join(f"{x:02x}" for x in b[:3]),
        vendor=vendor,
        category=category,
        is_multicast=is_multicast,
        is_local=is_local,
        ipv6_link_local=eui64_link_local(b),
        notes=notes,
    )


def eui64_link_local(b) -> str:
    """Turn a 48-bit MAC into its fe80:: IPv6 link-local address (EUI-64).

    The recipe (this is the 'proof the layers build on each other' moment):
      1. split the MAC in half,
      2. shove FF:FE in the middle -> now 64 bits,
      3. flip the 7th bit (the U/L bit) of the first byte,
      4. glue it onto fe80::/64.
    """
    eui = [b[0] ^ 0b0000_0010, b[1], b[2], 0xFF, 0xFE, b[3], b[4], b[5]]
    # Build each 16-bit hextet, then drop leading zeros (canonical IPv6 form).
    hextets = [
        (eui[0] << 8) | eui[1],
        (eui[2] << 8) | eui[3],
        (eui[4] << 8) | eui[5],
        (eui[6] << 8) | eui[7],
    ]
    return "fe80::" + ":".join(f"{h:x}" for h in hextets)
