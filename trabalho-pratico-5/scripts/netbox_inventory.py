#!/usr/bin/env python3
"""
Busca dados no NetBox (via API REST / pynetbox) e monta um dicionário de
hosts no MESMO formato que inventory/hosts.yaml, para o Nornir usar.

Isso resolve a Atividade 7.2 (Nornir lendo do NetBox) e destrava as
Atividades 9 e 11: mudar dado no NetBox passa a mudar a config renderizada,
sem tocar em template nenhum.

Modelagem usada no NetBox (Custom Fields no objeto Device):
- cf_asn            (Integer)  -> ASN do roteador
- cf_router_id      (Text)     -> IP do loopback / Router-ID
- cf_networks       (Text)     -> prefixos anunciados, separados por vírgula
                                   ex: "203.0.1.0/24" ou "203.101.0.0/24,192.168.100.0/24"
- cf_bgp_neighbors  (JSON)     -> lista de vizinhos BGP, ex:
    [
      {"peer_ip": "203.0.12.2", "peer_asn": 65001, "peer_name": "r2",
       "description": "iBGP para r2"}
    ]

Interfaces e IPs vêm dos objetos nativos do NetBox:
- /api/dcim/interfaces/?device=<nome>
- /api/ipam/ip-addresses/?device_id=<id>

Cada roteador continua precisando de hostname/porta SSH do laboratório
Mininet -- isso não é "dado de rede" do NetBox, então fica em SSH_PORTS
abaixo (mesma convenção do topo.py: 2200 + numero do roteador).
"""

from __future__ import annotations

import os
import re

import requests

SSH_PORTS = {
    "r1": 2201,
    "r2": 2202,
    "r3": 2203,
    "r4": 2204,
    "r5": 2205,
}


def _netbox_get(url, token, path, params=None):
    resp = requests.get(
        f"{url}/api/{path}",
        headers={"Authorization": f"Token {token}", "Accept": "application/json"},
        params=params or {},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    results = data.get("results", [])
    # segue paginação, caso existam mais paginas
    while data.get("next"):
        resp = requests.get(
            data["next"],
            headers={"Authorization": f"Token {token}", "Accept": "application/json"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        results.extend(data.get("results", []))
    return results


def _split_networks(raw):
    if not raw:
        return []
    return [item.strip() for item in re.split(r"[,\s]+", raw) if item.strip()]


def fetch_hosts_from_netbox(url, token):
    """Retorna um dict no formato de inventory/hosts.yaml, montado com dados do NetBox."""

    url = url.rstrip("/")
    devices = _netbox_get(url, token, "dcim/devices/")

    hosts = {}
    for device in devices:
        name = device["name"]
        cf = device.get("custom_fields", {}) or {}

        asn = cf.get("cf_asn")
        router_id = cf.get("cf_router_id")
        if asn is None or not router_id:
            # dispositivo sem os custom fields preenchidos: pula (ex: switches/hosts)
            continue

        networks = _split_networks(cf.get("cf_networks"))
        bgp_neighbors = cf.get("cf_bgp_neighbors") or []

        interfaces_raw = _netbox_get(
            url, token, "dcim/interfaces/", params={"device": name}
        )
        ip_addrs = _netbox_get(
            url, token, "ipam/ip-addresses/", params={"device_id": device["id"]}
        )
        # mapa interface_id -> "ip/prefix"
        ip_by_intf = {}
        for ip in ip_addrs:
            intf = (ip.get("assigned_object") or {}).get("id")
            if intf:
                ip_by_intf[intf] = ip["address"]  # ex "203.0.1.1/24"

        interfaces = []
        loopback_ip = router_id
        for intf in interfaces_raw:
            if intf["name"] in ("lo", "loopback0"):
                addr = ip_by_intf.get(intf["id"])
                if addr:
                    loopback_ip = addr.split("/")[0]
                continue
            addr = ip_by_intf.get(intf["id"])
            if not addr:
                continue
            ip, prefix = addr.split("/")
            interfaces.append(
                {
                    "name": intf["name"],
                    "ip": ip,
                    "prefix": prefix,
                    "description": intf.get("description") or "",
                }
            )

        hosts[name] = {
            "hostname": "127.0.0.1",
            "port": SSH_PORTS.get(name, 2200),
            "groups": ["routers"],
            "data": {
                "router_id": loopback_ip,
                "asn": int(asn),
                "loopback": f"{loopback_ip}/32",
                "interfaces": interfaces,
                "bgp_neighbors": bgp_neighbors,
                "networks": networks,
            },
        }

    if not hosts:
        raise RuntimeError(
            "NetBox respondeu, mas nenhum device tinha cf_asn/cf_router_id "
            "preenchidos. Confira os Custom Fields em Devices -> <roteador>."
        )

    return hosts


def netbox_configured():
    return bool(os.getenv("NETBOX_URL")) and bool(os.getenv("NETBOX_TOKEN"))


def fetch_hosts_from_env():
    return fetch_hosts_from_netbox(os.environ["NETBOX_URL"], os.environ["NETBOX_TOKEN"])
