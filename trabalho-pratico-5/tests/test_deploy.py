#!/usr/bin/env python3
"""Testes de inventario usados antes do deploy."""

from scripts.common import load_local_hosts


def test_ssh_ports_match_mininet_routers():
    hosts = load_local_hosts()

    assert hosts["r1"]["port"] == 2201
    assert hosts["r2"]["port"] == 2202
    assert hosts["r3"]["port"] == 2203
    assert hosts["r4"]["port"] == 2204


def test_neighbors_are_symmetric():
    hosts = load_local_hosts()
    neighbor_names = {
        host: {peer["peer_name"] for peer in data["data"]["bgp_neighbors"]}
        for host, data in hosts.items()
    }

    assert "r2" in neighbor_names["r1"]
    assert "r1" in neighbor_names["r2"]
    assert "r3" in neighbor_names["r2"]
    assert "r4" in neighbor_names["r2"]
    assert "r2" in neighbor_names["r3"]
    assert "r2" in neighbor_names["r4"]
