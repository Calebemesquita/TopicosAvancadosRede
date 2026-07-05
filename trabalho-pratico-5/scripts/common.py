#!/usr/bin/env python3
"""Funcoes compartilhadas pelos scripts GitOps."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
TEMPLATE_DIR = ROOT / "templates"
ARTIFACT_DIR = ROOT / "artifacts"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))


def init_nornir():
    """Inicializa Nornir.

    Com NETBOX_URL/NETBOX_TOKEN, gera inventario a partir do NetBox.
    Sem essas variaveis, usa o YAML local para testes rapidos no Mininet.
    """
    from nornir import InitNornir

    host_file = ROOT / "inventory" / "hosts.yaml"
    if netbox_env()["url"] and netbox_env()["token"]:
        from netbox_inventory import fetch_hosts_from_env

        ARTIFACT_DIR.mkdir(exist_ok=True)
        host_file = ARTIFACT_DIR / "netbox_hosts.yaml"
        host_file.write_text(yaml.safe_dump(fetch_hosts_from_env(), sort_keys=True), encoding="utf-8")

    return InitNornir(
        runner={"plugin": "threaded", "options": {"num_workers": 4}},
        inventory={
            "plugin": "SimpleInventory",
            "options": {
                "host_file": str(host_file),
                "group_file": str(ROOT / "inventory" / "groups.yaml"),
                "defaults_file": str(ROOT / "inventory" / "defaults.yaml"),
            },
        },
    )


def load_local_hosts():
    if netbox_env()["url"] and netbox_env()["token"]:
        from netbox_inventory import fetch_hosts_from_env

        return fetch_hosts_from_env()

    with (ROOT / "inventory" / "hosts.yaml").open() as file:
        return yaml.safe_load(file) or {}


def template_env():
    return Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        undefined=StrictUndefined,
        trim_blocks=False,
        lstrip_blocks=False,
    )


def render_device_config(hostname, host_entry, template_name="frr_bgp.j2"):
    data = dict(host_entry.get("data", {}))
    data["host"] = {"name": hostname}
    return template_env().get_template(template_name).render(**data)


def iter_python_files():
    ignored_dirs = {".git", ".venv", "venv", "__pycache__"}
    for path in ROOT.rglob("*.py"):
        if ignored_dirs.intersection(path.parts):
            continue
        yield path


def netbox_env():
    return {
        "url": os.getenv("NETBOX_URL", "").rstrip("/"),
        "token": os.getenv("NETBOX_TOKEN", ""),
    }
