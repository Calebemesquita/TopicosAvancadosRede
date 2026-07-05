#!/usr/bin/env python3
"""Testes leves dos templates Jinja2."""

from scripts.common import load_local_hosts, render_device_config


def test_render_all_devices_contains_bgp_process():
    hosts = load_local_hosts()
    assert set(hosts) == {"r1", "r2", "r3", "r4"}

    for hostname, host_entry in hosts.items():
        config = render_device_config(hostname, host_entry)
        asn = host_entry["data"]["asn"]
        router_id = host_entry["data"]["router_id"]

        assert f"router bgp {asn}" in config
        assert f"bgp router-id {router_id}" in config
        assert "address-family ipv4 unicast" in config
        assert "password tp3senha" in config


def test_r2_has_required_bgp_policies():
    config = render_device_config("r2", load_local_hosts()["r2"])

    assert "neighbor 203.0.23.2 route-map RM_R3_IN in" in config
    assert "neighbor 203.0.24.2 route-map RM_R4_IN in" in config
    assert "set local-preference 200" in config
    assert "set as-path prepend 65001 65001" in config
    assert "ip prefix-list PL_BOGONS" in config
