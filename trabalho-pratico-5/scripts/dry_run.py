#!/usr/bin/env python3
"""Renderiza configuracoes e gera diff sem aplicar nos roteadores."""

from __future__ import annotations

import difflib
from pathlib import Path

from common import ARTIFACT_DIR, ROOT, load_local_hosts, render_device_config


def diff_text(hostname, old, new):
    return "\n".join(
        difflib.unified_diff(
            old.splitlines(),
            new.splitlines(),
            fromfile=f"configs/{hostname}.cfg",
            tofile=f"rendered/{hostname}.cfg",
            lineterm="",
        )
    )


def main():
    hosts = load_local_hosts()
    rendered_dir = ARTIFACT_DIR / "rendered"
    rendered_dir.mkdir(parents=True, exist_ok=True)
    report = []

    for hostname, host_entry in sorted(hosts.items()):
        new_config = render_device_config(hostname, host_entry)
        proposed_file = rendered_dir / f"{hostname}.cfg"
        proposed_file.write_text(new_config, encoding="utf-8")

        current_file = ROOT / "configs" / f"{hostname}.cfg"
        old_config = current_file.read_text(encoding="utf-8") if current_file.exists() else ""
        diff = diff_text(hostname, old_config, new_config)

        report.append(f"### Device: {hostname}")
        report.append("")
        report.append("NEW CONFIGURATION:")
        report.append(new_config)
        report.append("")
        report.append("DIFF:")
        report.append(diff if diff else "No changes")
        report.append("")

    output = "\n".join(report)
    ARTIFACT_DIR.mkdir(exist_ok=True)
    (ARTIFACT_DIR / "dry_run_output.txt").write_text(output, encoding="utf-8")
    print(output)
    print(f"\nArtefato salvo em {Path('artifacts/dry_run_output.txt')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
