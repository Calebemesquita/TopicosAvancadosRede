#!/usr/bin/env python3
"""Entrada alternativa exigida na entrega.

A topologia real fica em ../topo.py para manter compatibilidade com o fluxo
que ja estava funcionando no projeto.
"""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from topo import run


if __name__ == "__main__":
    run(with_r5="--with-r5" in sys.argv)
