# 🕵️ NetProbe

**Point it at any IP or MAC address and it unwraps the "network onion" in plain English.**

Every message your computer sends is a letter inside **4 envelopes**, one inside the other:

| Envelope | Real name | The question it answers |
|----------|-----------|--------------------------|
| 📮 The wire | **Link layer** (MAC) | "Which machine right next to me gets this?" |
| 🏙️ The city map | **Internet layer** (IP + subnet) | "Which neighborhood, and how do I leave mine?" |
| 🚚 The delivery style | **Transport layer** (TCP/UDP) | "Careful or fast?" |
| 💬 The words | **Application layer** (HTTP/DNS) | "What does the message actually say?" |

NetProbe reads the first two envelopes for you — the ones that decide *who can talk to whom* — and explains what it finds like you're brand new to it.

---

## What it does

```bash
# Map a subnet (the "neighborhood")
python -m netprobe ip 172.24.26.77/20

# Read a MAC address (the factory name-tag) — including who made the card
python -m netprobe mac 00:15:5D:EA:FB:73

# Peek at this machine's own info
python -m netprobe me

# Measure your connection and diagnose WHY it feels slow
python -m netprobe doctor
```

### 1. `ip` — unwrap a subnet
Give it a house number **and** a neighborhood (`/prefix`) and it works out:
- the **network address** (the neighborhood's name) and **broadcast** (shout to everyone),
- the **range of usable houses** and how many there are,
- whether *this* address is the network, the broadcast, the **gateway** (front gate), or a normal machine,
- whether the address is **private** (inside a home/office) or **public** (out on the open internet).

<details>
<summary>Example output</summary>

```
🕵️  IP report for 172.24.26.77
  Family        : IPv4
  Scope         : private (inside a home/office)
  Subnet        : /20  (mask 255.255.240.0)

  The neighborhood 🏙️
    Network name    : 172.24.16.0
    Broadcast (all) : 172.24.31.255
    Houses run from : 172.24.16.1  →  172.24.31.254
    Usable houses   : 4,094

  This address 📍
    172.24.26.77 is a normal host inside the neighborhood
```
</details>

### 2. `mac` — read the factory name-tag
The first 3 bytes of a MAC address name the **company that made the card**. NetProbe:
- looks up the **vendor** and flags **virtual machines** (Hyper-V, VMware, VirtualBox, QEMU…), so you instantly know *"this is a fake NIC in a VM, not real hardware."*
- reads the **two secret bits** in the first byte — *multicast?* and *locally-administered?* (a randomized phone Wi-Fi MAC has this on).
- rebuilds the MAC's hidden **IPv6 link-local twin** using the **EUI-64** trick, so you can *see your MAC baked right inside an IPv6 address* — proof the layers stack on each other.

<details>
<summary>Example output</summary>

```
🕵️  MAC report for 00:15:5d:ea:fb:73
  Vendor block (OUI): 00:15:5D
  Made by           : Microsoft (Hyper-V / WSL)   🖥️  VIRTUAL

  The two secret bits 🔑
    Unicast/Multicast : unicast (one machine)
    Factory/Local     : factory-burned (a real vendor)

  Hidden IPv6 twin 👯 (EUI-64)
    fe80::215:5dff:feea:fb73
```
</details>

Add `--json` to `ip` or `mac` for machine-readable output you can pipe into other tools.

### 3. `doctor` — measure your connection (the honest "speed booster")
No software can make your internet faster — that's the physical pipe your ISP sells you. What a real tool *can* do is **measure the pipe and tell you why it feels slow**. `doctor` runs three checks and gives plain-English advice:

- ⏱️ **Latency** — round-trip delay to Cloudflare/Google/Quad9 ("is it laggy?")
- 🔍 **DNS** — how long name-lookups take (slow DNS → pages hang before loading → try `1.1.1.1`)
- 📊 **Download speed** — real throughput in Mbps, compared to what your plan promises

```bash
python -m netprobe doctor            # full check (~10 MB of data for the speed test)
python -m netprobe doctor --quick    # latency + DNS only, uses no data
python -m netprobe doctor --size 5   # smaller speed test
```

> ⚠️ Any app that claims to "add GB" or "boost speed" is a scam — often malware. This tool is the honest opposite: it diagnoses, it doesn't lie.

---

## Why this is a security tool, not just a calculator

- **"Same subnet?" = "can these two talk directly?"** — the first question in any network attack or defense. `same_subnet()` answers it.
- **Spotting virtual NICs** is real reconnaissance: it's how you tell a sandbox/VM apart from a physical host.
- **Reading MAC vendor OUIs** is how defenders fingerprint what's actually on a network.

This is the foundation the rest of the toolkit stands on: *a network is just structured messages moving through layers.*

---

## Run it

No installs needed — pure Python standard library (3.8+).

```bash
git clone https://github.com/Abbe11/netprobe.git
cd netprobe
python -m netprobe ip 192.168.1.10/24
```

### Tests
```bash
pip install pytest
pytest -q          # 11 tests, including the real /20 case and EUI-64 math
```

---

## How it's built

```
netprobe/
├── core.py     # the brains: subnet math (via `ipaddress`) + MAC bit-twiddling + EUI-64
├── oui.py      # a curated mini-database of MAC vendors (virtual + real + network gear)
├── cli.py      # the friendly command-line front door
└── __main__.py # lets you run `python -m netprobe`
tests/          # pytest suite
```

Built as project **#1** in a ground-up cybersecurity → AI-security learning series.

## License
MIT — see [LICENSE](LICENSE).
