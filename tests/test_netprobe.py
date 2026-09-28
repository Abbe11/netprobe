"""Tests for NetProbe. Run with:  pytest -q"""
import pytest

from netprobe import core, doctor


# --- IP / subnet ----------------------------------------------------------- #
def test_the_classic_slash20():
    """The exact case from the learning notes: 172.24.26.77/20."""
    r = core.analyze_ip("172.24.26.77/20")
    assert r.version == 4
    assert r.is_private is True
    assert r.network_address == "172.24.16.0"
    assert r.broadcast_address == "172.24.31.255"
    assert r.first_host == "172.24.16.1"
    assert r.last_host == "172.24.31.254"
    assert r.num_usable_hosts == 4094


def test_gateway_is_first_host():
    r = core.analyze_ip("172.24.16.1/20")
    assert "gateway" in r.role_of_address


def test_network_and_broadcast_flagged():
    assert "network address" in core.analyze_ip("10.0.0.0/24").role_of_address
    assert "broadcast" in core.analyze_ip("10.0.0.255/24").role_of_address


def test_public_vs_private():
    assert core.analyze_ip("8.8.8.8/24").is_private is False
    assert core.analyze_ip("192.168.1.5/24").is_private is True


def test_host_only_has_no_subnet():
    r = core.analyze_ip("10.0.0.5")
    assert r.kind == "host-only"
    assert r.network_address is None


def test_same_subnet():
    assert core.same_subnet("172.24.26.77", "172.24.16.1", "20") is True
    assert core.same_subnet("172.24.26.77", "10.0.0.1", "20") is False


# --- MAC ------------------------------------------------------------------- #
def test_hyperv_mac_detected_as_virtual():
    r = core.analyze_mac("00:15:5D:EA:FB:73")
    assert r.vendor and "Hyper-V" in r.vendor
    assert r.category == "virtual"
    assert r.is_multicast is False


def test_eui64_link_local_matches_known_value():
    # The notes' own example: 00:15:5d:ea:fb:73 -> fe80::215:5dff:feea:fb73
    r = core.analyze_mac("00:15:5d:ea:fb:73")
    assert r.ipv6_link_local == "fe80::215:5dff:feea:fb73"


def test_local_and_multicast_bits():
    # x2 = ...0010 -> local bit set; x1 = ...0001 -> multicast bit set
    assert core.analyze_mac("02:00:00:00:00:01").is_local is True
    assert core.analyze_mac("01:00:5e:00:00:01").is_multicast is True
    assert core.analyze_mac("00:15:5d:ea:fb:73").is_local is False


def test_mac_accepts_dash_and_dot_formats():
    a = core.analyze_mac("00-15-5D-EA-FB-73")
    b = core.analyze_mac("0015.5dea.fb73")
    assert a.normalized == b.normalized == "00:15:5d:ea:fb:73"


def test_bad_mac_raises():
    with pytest.raises(ValueError):
        core.analyze_mac("not-a-mac")
    with pytest.raises(ValueError):
        core.analyze_mac("00:15:5D")


# --- doctor grading logic -------------------------------------------------- #
def test_grade_lower_is_better():
    # latency-style: small numbers are good
    assert "excellent" in doctor._grade(10, 40, 120)
    assert "okay" in doctor._grade(80, 40, 120)
    assert "slow" in doctor._grade(300, 40, 120)


def test_grade_higher_is_better():
    # speed-style: big numbers are good
    assert "excellent" in doctor._grade(50, 25, 5, lower_is_better=False)
    assert "okay" in doctor._grade(10, 25, 5, lower_is_better=False)
    assert "slow" in doctor._grade(2, 25, 5, lower_is_better=False)


def test_grade_handles_unreachable():
    assert "unreachable" in doctor._grade(None, 40, 120)
