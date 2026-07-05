#!/usr/bin/env python3
"""orquestrador bgp nornir"""

import argparse
import time
from nornir import InitNornir
from nornir_utils.plugins.functions import print_result

from tasks.frr_tasks import (
    wait_for_frr, render_config, apply_config,
    verify_bgp, ping_neighbors, backup_running_config
)



# Função para inicializar o Nornir com a configuração do inventário
# runner: Define o plugin de execução usando 4 threaded para paralelismo
# inventory: Configura o plugin de inventário para ler os arquivos YAML
def init_nornir():
    return InitNornir(
        runner={"plugin": "threaded", "options": {"num_workers": 4}},
        inventory={
            "plugin": "SimpleInventory",
            "options": {
                "host_file": "inventory/hosts.yaml",
                "group_file": "inventory/groups.yaml",
                "defaults_file": "inventory/defaults.yaml"
            }
        }
    )



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", default="all", help="all, render, deploy, verify")
    args = parser.parse_args()

    print("\n Puxamos os arquivos de inventário e inicializamos o Nornir")
    nr = init_nornir()

    if args.step == "all":
        print("\nEsperando os roteadores FRR ligar")
        resultado_espera = nr.run(task=wait_for_frr)
        print_result(resultado_espera)

    # junto o render e o deploy porque o render só gera o texto da configuração, não precisa esperar o FRR subir pra isso
    if args.step in ("all", "render", "deploy"):
        print("\n Renderizando configurações do jinja2 usando os dados do YAML")
        # gera configurações para todos os hosts do inventário
        #O resultado é um dicionário com o nome do host e o texto da configuração
        result_render = nr.run(task=render_config, template_dir="templates")
        
        print_result(result_render) 

        dicionario_configs = {}
        for host, data in result_render.items():
            if not data.failed and data[0].result:
                dicionario_configs[host] = data[0].result
                #configs = {
                #     "r1": "config gerada",
                #     "r2": "config gerada"
                # }
            

    if args.step in ("all", "deploy"):
        print("\n Aplicando configurações via SSH")
        # percorre o dicionário de configurações e aplica cada uma no host correspondente usando a tarefa apply_config
        for host_name, cfg in dicionario_configs.items():
            
            host_nr = nr.filter(name=host_name)

            # Aplica concdiguração ssh usando a tarefa apply_config
            print_result(host_nr.run(task=apply_config, config=cfg)) 
        
        print("\n Esperando a tabela BGP subir 20s")
        time.sleep(20)


    if args.step in ("all", "verify"):
        print("\n Verificando tabelas BGP e realizando Ping")
        print_result(nr.run(task=verify_bgp, template_dir="templates")) # roda show ip bgp
        print_result(nr.run(task=ping_neighbors)) # faz ping
        print_result(nr.run(task=backup_running_config)) # faz backup da configurações

if __name__ == "__main__":
    main()
