#!/usr/bin/python3
import json
import os
from mininet.net import Mininet
from mininet.node import OVSBridge
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from jinja2 import Environment, FileSystemLoader

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def gerar_configs_jinja():
    info("*** [1] Lendo o JSON do NetBox e Gerando Configs com Jinja2...\n")
    json_path = os.path.join(BASE_DIR, 'netbox_dados_jinja.json')
    with open(json_path, 'r') as f:
        dados = json.load(f)

    env = Environment(loader=FileSystemLoader(BASE_DIR))
    template = env.get_template('bgp.j2')

    for roteador in dados['roteadores']:
        hostname = roteador['hostname']
        config_renderizada = template.render(roteador)
        dir_roteador = os.path.join(BASE_DIR, 'configs', hostname)
        os.makedirs(dir_roteador, exist_ok=True)
        
        caminho_arquivo = os.path.join(dir_roteador, 'bgpd.conf')
        with open(caminho_arquivo, 'w') as f:
            f.write(config_renderizada)
        
        info(f"    - Configuração gerada: {caminho_arquivo}\n")

def iniciar_topologia():
    info("*** [2] Iniciando o Mininet...\n")
    net = Mininet(controller=None, switch=OVSBridge)

    info("*** Adicionando o Switch S1...\n")
    s1 = net.addSwitch('s1')

    info("*** Adicionando os Roteadores com Pastas Privadas (Isolamento)...\n")
    diretorios_privados = ['/etc/frr', '/var/run/frr']
    
    r1 = net.addHost('r1', ip='10.0.0.1/24', privateDirs=diretorios_privados)
    r2 = net.addHost('r2', ip='10.0.0.2/24', privateDirs=diretorios_privados)
    r3 = net.addHost('r3', ip='10.0.0.3/24', privateDirs=diretorios_privados)
    r4 = net.addHost('r4', ip='10.0.0.4/24', privateDirs=diretorios_privados)

    info("*** Passando os Cabos (Links)...\n")
    net.addLink(r1, s1)
    net.addLink(r2, s1)
    net.addLink(r3, s1)
    net.addLink(r4, s1)

    info("*** [3] Ligando a energia da Rede...\n")
    net.start()

    info("*** [4] Iniciando os Daemons do FRRouting (BGP)...\n")
    roteadores = [r1, r2, r3, r4]
    for r in roteadores:
        hostname = r.name
        config_dir = os.path.join(BASE_DIR, 'configs', hostname)
        
        r.cmd('sysctl -w net.ipv4.ip_forward=1')
        
        num = hostname.replace('r', '')
        r.cmd(f'ip addr add 192.168.{num}.1/24 dev lo')
        r.cmd('ip link set lo up')
        r.cmd(f'cp {config_dir}/bgpd.conf /etc/frr/bgpd.conf')
        r.cmd('touch /etc/frr/zebra.conf') 
        r.cmd('touch /etc/frr/vtysh.conf')
        r.cmd('chown -R frr:frrvty /etc/frr')
        r.cmd('chown -R frr:frrvty /var/run/frr')
        r.cmd('chmod 775 /var/run/frr')
        r.cmd('/usr/lib/frr/zebra -f /etc/frr/zebra.conf -d -z /var/run/frr/zserv.api -i /var/run/frr/zebra.pid')
        r.cmd('sleep 1')
        r.cmd('/usr/lib/frr/bgpd -f /etc/frr/bgpd.conf -d -z /var/run/frr/zserv.api -i /var/run/frr/bgpd.pid')

    info("*** [5] Rede BGP 100% Operacional! Abrindo Terminal do Mininet...\n")
    CLI(net)

    info("*** [6] Desligando tudo e limpando...\n")
    for r in roteadores:
        r.cmd('kill `cat /var/run/frr/bgpd.pid` 2>/dev/null')
        r.cmd('kill `cat /var/run/frr/zebra.pid` 2>/dev/null')
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    gerar_configs_jinja() 
    iniciar_topologia()