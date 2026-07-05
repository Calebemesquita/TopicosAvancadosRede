#!/usr/bin/env python3
"""Rollback simples reaplicando arquivos em backups/ quando existirem."""

from __future__ import annotations

from nornir_utils.plugins.functions import print_result

from common import ROOT, init_nornir
from tasks.frr_tasks import apply_config


def main():
    nr = init_nornir()
    missing = []

    for host in sorted(nr.inventory.hosts):
        backup_file = ROOT / "backups" / f"{host}_running.cfg"
        if not backup_file.exists():
            missing.append(str(backup_file.relative_to(ROOT)))
            continue

        config = backup_file.read_text(encoding="utf-8")
        print(f"Reaplicando backup em {host}")
        print_result(nr.filter(name=host).run(task=apply_config, config=config))

    if missing:
        print("Backups ausentes: " + ", ".join(missing))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
