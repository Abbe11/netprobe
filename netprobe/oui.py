"""A tiny built-in database of MAC-address vendors (OUIs).

The first 3 bytes of a MAC address are the OUI (Organizationally Unique
Identifier) — they name the company that made the network card. The full
official list has ~35,000 entries; here we bundle a curated set of the
ones you actually run into on a laptop, plus every common *virtual*
machine vendor, because spotting "this is a fake/virtual NIC" is the
detective trick that matters most.

Keys are the OUI as 6 uppercase hex chars, no separators.
"""

OUI_DB = {
    # ---- Virtual machines / hypervisors (the fun ones to catch) ----
    "00155D": ("Microsoft (Hyper-V / WSL)", "virtual"),
    "000C29": ("VMware", "virtual"),
    "005056": ("VMware", "virtual"),
    "001C14": ("VMware", "virtual"),
    "000569": ("VMware", "virtual"),
    "080027": ("Oracle VirtualBox", "virtual"),
    "0A0027": ("Oracle VirtualBox (host-only)", "virtual"),
    "525400": ("QEMU / KVM", "virtual"),
    "00163E": ("Xen", "virtual"),
    "001C42": ("Parallels", "virtual"),
    "0003FF": ("Microsoft (Virtual PC / Azure)", "virtual"),

    # ---- Real hardware you meet all the time ----
    "F0189E": ("Apple", "hardware"),
    "3C0754": ("Apple", "hardware"),
    "A45E60": ("Apple", "hardware"),
    "ACBC32": ("Apple", "hardware"),
    "D0817A": ("Apple", "hardware"),
    "B827EB": ("Raspberry Pi Foundation", "hardware"),
    "DCA632": ("Raspberry Pi (Trading) Ltd", "hardware"),
    "E45F01": ("Raspberry Pi", "hardware"),
    "001A11": ("Google", "hardware"),
    "3C5AB4": ("Google", "hardware"),
    "F4F5E8": ("Google", "hardware"),
    "001132": ("Synology", "hardware"),
    "9C305B": ("Hewlett Packard (HP)", "hardware"),
    "3863BB": ("Hewlett Packard (HP)", "hardware"),
    "A0D3C1": ("Hewlett Packard (HP)", "hardware"),
    "001560": ("Hewlett Packard (HP)", "hardware"),
    "F48E38": ("Dell", "hardware"),
    "18DBF2": ("Dell", "hardware"),
    "D89EF3": ("Dell", "hardware"),
    "001A2B": ("Ayecom / Lenovo", "hardware"),
    "E4E749": ("Hewlett Packard (HP)", "hardware"),
    "001B63": ("Apple", "hardware"),
    "0018DE": ("Intel", "hardware"),
    "001E67": ("Intel", "hardware"),
    "3C970E": ("Intel", "hardware"),
    "A0A8CD": ("Intel", "hardware"),
    "7C7A91": ("Intel", "hardware"),
    "00E04C": ("Realtek", "hardware"),
    "52544C": ("Realtek", "hardware"),
    "001DD8": ("Microsoft", "hardware"),
    "C83A35": ("Tenda", "hardware"),
    "001018": ("Broadcom", "hardware"),

    # ---- Routers / networking gear (often your gateway) ----
    "F81A67": ("TP-Link", "network-gear"),
    "50C7BF": ("TP-Link", "network-gear"),
    "AC84C6": ("TP-Link", "network-gear"),
    "C46E1F": ("TP-Link", "network-gear"),
    "0018E7": ("Cameo / Netgear", "network-gear"),
    "2C3033": ("Netgear", "network-gear"),
    "A040A0": ("Netgear", "network-gear"),
    "001F33": ("Netgear", "network-gear"),
    "18E829": ("Ubiquiti", "network-gear"),
    "FCECDA": ("Ubiquiti", "network-gear"),
    "245A4C": ("Ubiquiti", "network-gear"),
    "00259C": ("Cisco-Linksys", "network-gear"),
    "68BDAB": ("Cisco", "network-gear"),
    "00000C": ("Cisco", "network-gear"),
    "E0286D": ("AVM (FRITZ!Box)", "network-gear"),
    "84D47E": ("Aruba / HPE Networking", "network-gear"),
    "D017C2": ("Safaricom / Huawei", "network-gear"),
    "00259E": ("Huawei", "network-gear"),
    "48AD08": ("Huawei", "network-gear"),
    "20F3A3": ("Huawei", "network-gear"),
    "MikroTik": ("MikroTik", "network-gear"),
    "4C5E0C": ("MikroTik", "network-gear"),
    "6C3B6B": ("MikroTik", "network-gear"),
}


def lookup(oui6: str):
    """Return (vendor_name, category) for a 6-hex-char OUI, or (None, None)."""
    return OUI_DB.get(oui6.upper(), (None, None))
