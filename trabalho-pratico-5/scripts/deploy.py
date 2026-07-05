#!/usr/bin/env python3
"""Deploy manual: renderiza, aplica via SSH/vtysh e verifica BGP."""

from __future__ import annotations

import time

from nornir_utils.plugins.functions import print_result

from common import init_nornir
from tasks.frr_tasks import (
    apply_config,
    backup_running_config,
    ping_neighbors,
    render_config,
    verify_bgp,
    wait_for_frr,
)


def main():
    nr = init_nornir()

    print("Esperando FRR responder nos roteadores")
    wait_result = nr.run(task=wait_for_frr)
    print_result(wait_result)
    if wait_result.failed:
        return 1

    print("Renderizando configuracoes")
    render_result = nr.run(task=render_config, template_dir="templates")
    print_result(render_result)
    if render_result.failed:
        return 1

    for hostname, result in render_result.items():
        if result.failed:
            continue
        config = result[0].result
        print(f"Aplicando configuracao em {hostname}")
        deploy_result = nr.filter(name=hostname).run(task=apply_config, config=config)
        print_result(deploy_result)
        if deploy_result.failed:
            return 1

    print("Aguardando convergencia BGP")
    time.sleep(20)

    print("Verificando BGP, pings e backups")
    verify_result = nr.run(task=verify_bgp, template_dir="templates")
    ping_result = nr.run(task=ping_neighbors)
    backup_result = nr.run(task=backup_running_config)
    print_result(verify_result)
    print_result(ping_result)
    print_result(backup_result)
    return 1 if verify_result.failed or ping_result.failed or backup_result.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
