"""NetProbe — the connection `doctor`.

It CANNOT make your internet faster (no software can widen the pipe your
ISP gives you). What it does is *measure* the pipe and tell you, in plain
English, WHY it might feel slow — the honest version of a "speed booster".

Three checks, each answering a different everyday complaint:
  • Latency   -> "everything feels laggy"      (round-trip delay)
  • DNS       -> "pages hang before loading"   (name-finding delay)
  • Download  -> "downloads/videos are slow"   (actual throughput)

Pure standard library: socket + urllib. Runs on the user's own machine.
"""
from __future__ import annotations

import socket
import statistics
import time
import urllib.request

from .ui import bold, cyan, green, red, rule, yellow

# Well-known, always-on hosts we can knock on to time a round trip.
LATENCY_TARGETS = [
    ("Cloudflare", "1.1.1.1"),
    ("Google", "8.8.8.8"),
    ("Quad9", "9.9.9.9"),
]
DNS_TARGETS = ["example.com", "wikipedia.org", "github.com"]
# Public speed-test download sources, tried in order until one works.
# The first takes an exact byte count; the fallbacks are fixed-size files.
SPEED_SOURCES = [
    ("Cloudflare", lambda n: f"https://speed.cloudflare.com/__down?bytes={n}"),
    ("ThinkBroadband", lambda n: "http://ipv4.download.thinkbroadband.com/10MB.zip"),
    ("OVH", lambda n: "https://proof.ovh.net/files/10Mb.dat"),
]


# --------------------------------------------------------------------------- #
#  Measurements (each returns numbers; no printing here)
# --------------------------------------------------------------------------- #
def tcp_ping(host: str, port: int = 443, timeout: float = 2.0):
    """Time one TCP handshake to host:port, in milliseconds (None on failure).

    This is a stand-in for a classic ICMP ping. Real ping needs admin
    rights; a TCP connect doesn't, and it measures the same round trip.
    """
    start = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return (time.perf_counter() - start) * 1000.0
    except OSError:
        return None


def measure_latency(tries: int = 4):
    """Return {name: {'best': ms, 'median': ms}} for each latency target."""
    results = {}
    for name, host in LATENCY_TARGETS:
        samples = [t for _ in range(tries) if (t := tcp_ping(host)) is not None]
        if samples:
            results[name] = {"best": min(samples), "median": statistics.median(samples)}
        else:
            results[name] = None
    return results


def measure_dns():
    """Time a DNS lookup for each domain, in milliseconds (None on failure)."""
    results = {}
    for domain in DNS_TARGETS:
        start = time.perf_counter()
        try:
            socket.getaddrinfo(domain, 443)
            results[domain] = (time.perf_counter() - start) * 1000.0
        except OSError:
            results[domain] = None
    return results


def measure_download(size_bytes: int):
    """Download filler and return (mbps, bytes, seconds, source_name).

    Tries each source in SPEED_SOURCES until one succeeds, so a single
    blocked host doesn't kill the test. Raises the last error if all fail.
    """
    last_error = None
    for name, url_for in SPEED_SOURCES:
        url = url_for(size_bytes)
        req = urllib.request.Request(url, headers={"User-Agent": "netprobe/1.0"})
        total = 0
        start = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    total += len(chunk)
            elapsed = max(time.perf_counter() - start, 1e-6)
            mbps = (total * 8) / elapsed / 1_000_000  # bits/s -> Megabits/s
            return mbps, total, elapsed, name
        except Exception as e:  # noqa: BLE001 - try the next source
            last_error = e
    raise last_error if last_error else RuntimeError("no speed sources configured")


# --------------------------------------------------------------------------- #
#  Plain-English verdicts
# --------------------------------------------------------------------------- #
def _grade(value, good, ok, lower_is_better=True):
    if value is None:
        return red("unreachable")
    if lower_is_better:
        if value <= good:
            return green("excellent")
        if value <= ok:
            return yellow("okay")
        return red("slow")
    else:
        if value >= good:
            return green("excellent")
        if value >= ok:
            return yellow("okay")
        return red("slow")


def run(size_mb: float = 10.0, quick: bool = False):
    """Run the checks and print a friendly report. Returns nothing."""
    rule()
    print(bold("🩺  NetProbe — connection checkup"))
    rule()
    print(yellow("  I can't speed up your line — that's your ISP's pipe. I just"))
    print(yellow("  measure it and point at whatever's dragging. Working...\n"))

    advice = []

    # ---- 1. Latency -------------------------------------------------------- #
    print(bold("  1) Latency  ⏱️   (how 'laggy' the line feels)"))
    lat = measure_latency()
    best_overall = None
    for name, r in lat.items():
        if r is None:
            print(f"     {name:<11}: {red('unreachable')}")
            continue
        best_overall = r["best"] if best_overall is None else min(best_overall, r["best"])
        print(f"     {name:<11}: {r['median']:6.1f} ms   ({_grade(r['median'], 40, 120)})")
    if best_overall is None:
        print(red("     No servers answered — are you offline?"))
        advice.append("You appear to be offline — check Wi-Fi / cable first.")
    elif best_overall > 120:
        advice.append("High latency: you're likely far from the router or on weak "
                      "Wi-Fi. Move closer or use an Ethernet cable.")

    # ---- 2. DNS ------------------------------------------------------------ #
    print(bold("\n  2) DNS  🔍   (time to look up website names)"))
    dns = measure_dns()
    dns_vals = [v for v in dns.values() if v is not None]
    for domain, ms in dns.items():
        if ms is None:
            print(f"     {domain:<15}: {red('failed')}")
        else:
            print(f"     {domain:<15}: {ms:6.1f} ms   ({_grade(ms, 60, 200)})")
    if dns_vals and statistics.median(dns_vals) > 200:
        advice.append("Slow DNS: pages hang before loading. Try switching your DNS "
                      "to 1.1.1.1 (Cloudflare) or 8.8.8.8 (Google) in your Wi-Fi "
                      "settings — free and often a big improvement.")

    # ---- 3. Download ------------------------------------------------------- #
    if quick:
        print(bold("\n  3) Download speed  📊"))
        print(yellow("     skipped (--quick). Run without --quick to measure it."))
    else:
        size_bytes = int(size_mb * 1_000_000)
        print(bold(f"\n  3) Download speed  📊   (uses ~{size_mb:.0f} MB of data)"))
        try:
            mbps, got, secs, source = measure_download(size_bytes)
            print(f"     Got {got/1e6:.1f} MB from {source} in {secs:.1f}s  →  "
                  f"{green(f'{mbps:.1f} Mbps')}   ({_grade(mbps, 25, 5, lower_is_better=False)})")
            print(yellow(f"     Compare that to the speed your ISP plan promises."))
            if mbps < 5:
                advice.append("Low download speed. If your plan promises more, reboot "
                              "the router, test on a cable, and check nobody else is "
                              "streaming/downloading at the same time.")
        except Exception as e:
            print(red(f"     Couldn't run the speed test: {e}"))

    # ---- Diagnosis --------------------------------------------------------- #
    print(bold("\n  🩺  Diagnosis"))
    if not advice:
        print(green("     Everything looks healthy. If it still feels slow, the "
                    "bottleneck is probably your ISP plan itself (buy more speed)."))
    else:
        for tip in advice:
            print(f"     {yellow('•')} {tip}")
    print()
    print(cyan("  Remember: no app can add data or widen the pipe. Anything that"))
    print(cyan("  claims to 'boost speed' or 'add GB' is a scam (often malware)."))
