import os
import time
from nornir.core.task import Result
from nornir_utils.plugins.tasks.files import write_file
from nornir_jinja2.plugins.tasks import template_file
from nornir_paramiko.plugins.tasks import paramiko_command

# função que fala com cada roteador usando vtysh via SSH para rodar comandos ou enviar configuração
def run_vtysh(task, commands):

    # pega texto gigante de comanodos e transforma em uma linha só formatada pra passar pro vtysh 
    # usando -c "comando1" -c "comando2" -c "comando3"
    lines = [linha.strip() for linha in commands.splitlines() if linha.strip()]
    args = " ".join(f'-c "{l}"' for l in lines)
    
    # task.run (executa esse comando nohhost do nornir usando paramiko para ss)
    # passa os argumento vtysh {-c "conf t" -c "router bgp 65001"}
    resultado = task.run(task=paramiko_command, command=f"vtysh {args}")
    return resultado.result


def wait_for_frr(task):
    # tentamos 10 vezes a cada 3 segundos para ver se o FRR respondeu, rodando um show version
    for tentativa in range(10):
        try:
            saida = run_vtysh(task, "show version") #roda comadno ne mn nkk
            if "FRRouting" in saida: #FRRouting 8.x
                return Result(host=task.host, result="FRR Pronto!", changed=False) # ai podemos continuar
        except Exception:
            pass
        time.sleep(3) 
        
    return Result(host=task.host, result="Erro: FRR não respondeu", failed=True) 




def render_config(task, template_dir="templates"):
    # Pega os dados deste host específico do hosts.yaml
    dados = task.host.data

    # Renderiza o template mesclando com os dados
    # pega template do ffr_bgp.j2 e passa os dados do host pra ele gerar o texto da configuração
    render = task.run(
        task=template_file,
        template="frr_bgp.j2",
        path=template_dir,
        **dados  # Desempacota todas as variáveis do YAML direto pro Jinja2
    )
    # pega config pronta agr como string
    config_texto = render.result
    



    # Cria pasta configs, se existir ja deixa queto kk
    os.makedirs("configs", exist_ok=True)
    # salva o texto da configuração em um arquivo local pra cada host
    task.run(task=write_file, filename=f"configs/{task.host.name}.cfg", content=config_texto)
    # config gerada, mas so criou o arquivo local
    return Result(host=task.host, result=config_texto, changed=False)



# pega config
# task -> roteador
# config -> texto gerado pelo render
def apply_config(task, config):
    # executa toda a configuraçã
    saida = run_vtysh(task, config)
    # se a saída tiver "Invalid command" ou "Error", falhou
    if "Invalid command" in saida or "Error" in saida:
        return Result(host=task.host, result="Erro ao aplicar configuração", failed=True)
    
    return Result(host=task.host, result="Configuração Aplicada", changed=True)


#show ip bgp summary
# show ip bgp neighbors {{ bgp_neighbors[0] }}
# verificar se a tabela bgp subiu, rodando show ip bgp e confirmando que tem vizinhos up e rotas aprendidas
def verify_bgp(task, template_dir="templates"):
    render = task.run(
        task=template_file, 
        template="verify_bgp.j2", 
        path=template_dir, 
        bgp_neighbors=task.host.data["bgp_neighbors"]
    )
    saida = run_vtysh(task, render.result)
    return Result(host=task.host, result=saida, changed=False)





def ping_neighbors(task):
    #puxa os vizinho do roteador do hosts.yaml
    vizinhos = task.host.data.get("bgp_neighbors", [])
    relatorio = ""

    for vizinho in vizinhos:
        ip = vizinho["peer_ip"]
        # Roda o ping no shell do Linux 
        ping = task.run(task=paramiko_command, command=f"ping -c 3 -W 1 {ip}")
        
        if "3 received" in ping.result:
            relatorio += f"[{ip}] Ping OK \n"
        else:
            relatorio += f"[{ip}] Ping FALHOU \n"

    return Result(host=task.host, result=relatorio, changed=False)



# salva configuração atual do roteador em um arquivo local, rodando show running-config e salvando a saída
def backup_running_config(task):
    saida = run_vtysh(task, "show running-config") # executando com vtysh
    
    os.makedirs("backups", exist_ok=True)
    with open(f"backups/{task.host.name}_running.cfg", "w") as arquivo:
        arquivo.write(saida)
        
    return Result(host=task.host, result="Backup Concluído", changed=False)