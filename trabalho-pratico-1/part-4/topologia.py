#!/usr/bin/python3
import json
import os
from mininet.net import Mininet
from mininet.node import Controller, OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from jinja2 import Environment, FileSystemLoader

def gerar_configs_jinja():
    info("***  Lendo o JSON do NetBox e Gerando Configs com Jinja2\n")
    
    with open('netbox_dados_jinja.json', 'r') as f:
        dados = json.load(f)

    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('bgpd.j2') 

    for roteador in dados['roteadores']:
        hostname = roteador['hostname']
        config_renderizada = template.render(roteador)
        
        
        caminho_arquivo = f"configs/{hostname}/bgpd.conf"
        with open(caminho_arquivo, 'w') as f:
            f.write(config_renderizada)
        
        os.system(f"touch configs/{hostname}/zebra.conf")
        os.system(f"chown mininet:mininet configs/{hostname}/* 2>/dev/null") 
        
        info(f"    - Configuração gerada para {hostname.upper()}\n")

def iniciar_topologia():
    info("***  Iniciando o Mininet\n")
    net = Mininet(controller=Controller, switch=OVSKernelSwitch)

    info("*** Adicionando o Switch S1 \n")
    s1 = net.addSwitch('s1')

    info("*** Adicionando os Roteadores e IPs...\n")
    r1 = net.addHost('r1', ip='10.0.0.1/24')
    r2 = net.addHost('r2', ip='10.0.0.2/24')
    r3 = net.addHost('r3', ip='10.0.0.3/24')
    r4 = net.addHost('r4', ip='10.0.0.4/24')

    info("*** Passando os Cabos (Links)\n")
    net.addLink(r1, s1)
    net.addLink(r2, s1)
    net.addLink(r3, s1)
    net.addLink(r4, s1)

    info("*** Ligando a energia da Rede\n")
    net.start()

    info("*** Iniciando os Daemons do FRRouting (BGP)\n")
    roteadores = [r1, r2, r3, r4]
    for r in roteadores:
        hostname = r.name
        
        r.cmd('sysctl -w net.ipv4.ip_forward=1')
        
        dir_atual = os.getcwd()
        config_dir = f"{dir_atual}/configs/{hostname}"
        
        r.cmd(f'/usr/lib/frr/zebra -f {config_dir}/zebra.conf -d -i /tmp/zebra-{hostname}.pid')
        
        r.cmd(f'/usr/lib/frr/bgpd -f {config_dir}/bgpd.conf -d -i /tmp/bgpd-{hostname}.pid')

    info("*** Abrindo Terminal do Mininet \n")
    CLI(net)

    info("*** Desligando tudo e limpando \n")
    for r in roteadores:
        r.cmd(f'kill `cat /tmp/bgpd-{r.name}.pid` 2>/dev/null')
        r.cmd(f'kill `cat /tmp/zebra-{r.name}.pid` 2>/dev/null')
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    
    gerar_configs_jinja()
    
    iniciar_topologia()