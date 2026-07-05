#!/usr/bin/env python3
"""Gera um ZIP de entrega com os nomes pedidos nas instrucoes."""

from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from common import ROOT


OUTPUT = ROOT / "entrega_tp5.zip"


FILES = {
    "Mininet/topology.py": ROOT / "Mininet" / "topology.py",
    "Mininet/setup.sh": ROOT / "setup.sh",
    "FRR_Configurations/r1_config.txt": ROOT / "configs" / "r1.cfg",
    "FRR_Configurations/r2_config.txt": ROOT / "configs" / "r2.cfg",
    "FRR_Configurations/r3_config.txt": ROOT / "configs" / "r3.cfg",
    "FRR_Configurations/r4_config.txt": ROOT / "configs" / "r4.cfg",
    "FRR_Configurations/README_CONFIGS.md": ROOT / "configs" / "README_CONFIGS.md",
    "Repositorio/README.md": ROOT / "README.md",
    "Repositorio/.gitlab-ci.yml": ROOT / ".gitlab-ci.yml",
    "Repositorio/requirements.txt": ROOT / "requirements.txt",
    "Repositorio/GITLAB_REPO.txt": ROOT / "GITLAB_REPO.txt",
}


DIRS = ["templates", "scripts", "docs", "examples", "inventory", "tests"]


def add_tree(zip_file, directory):
    root = ROOT / directory
    if not root.exists():
        return
    for path in sorted(root.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts:
            zip_file.write(path, f"Repositorio/{path.relative_to(ROOT)}")


def main():
    with ZipFile(OUTPUT, "w", ZIP_DEFLATED) as zip_file:
        for archive_name, source in FILES.items():
            if source.exists():
                zip_file.write(source, archive_name)
        for directory in DIRS:
            add_tree(zip_file, directory)

    print(f"ZIP gerado: {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
