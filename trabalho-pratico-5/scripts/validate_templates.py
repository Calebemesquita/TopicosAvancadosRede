#!/usr/bin/env python3
"""Valida templates Jinja2, sintaxe Python e conectividade opcional ao NetBox."""

from __future__ import annotations

import py_compile
import sys

from common import ROOT, TEMPLATE_DIR, netbox_env, template_env, iter_python_files


def validate_jinja():
    env = template_env()
    templates = sorted(path.name for path in TEMPLATE_DIR.glob("*.j2"))
    if not templates:
        raise RuntimeError("Nenhum template .j2 encontrado em templates/")

    for name in templates:
        env.get_template(name)
        print(f"OK template: {name}")


def validate_python():
    for path in iter_python_files():
        py_compile.compile(str(path), doraise=True)
        print(f"OK python: {path.relative_to(ROOT)}")


def validate_netbox_if_configured():
    cfg = netbox_env()
    if not cfg["url"] or not cfg["token"]:
        print("SKIP netbox: defina NETBOX_URL e NETBOX_TOKEN no GitLab para validar API")
        return

    import requests

    response = requests.get(
        f"{cfg['url']}/api/dcim/devices/",
        headers={"Authorization": f"Token {cfg['token']}", "Accept": "application/json"},
        timeout=10,
    )
    response.raise_for_status()
    devices = response.json().get("results", [])
    names = sorted(device.get("name") for device in devices)
    expected = {"r1", "r2", "r3", "r4"}
    missing = expected.difference(names)
    if missing:
        raise RuntimeError(f"NetBox respondeu, mas faltam dispositivos: {sorted(missing)}")
    print(f"OK netbox: dispositivos encontrados {', '.join(sorted(expected))}")


def main():
    try:
        validate_jinja()
        validate_python()
        validate_netbox_if_configured()
    except Exception as exc:
        print(f"ERRO validate: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
