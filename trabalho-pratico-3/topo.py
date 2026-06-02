#!/usr/bin/python3

import os
import subprocess
import time
from mininet.net import Mininet
from mininet.node import Node
from mininet.topo import Topo
from mininet.cli import CLI
from mininet.log import setLogLevel


#topologia mininet 

# 1. TEMPLATES BÁSICOS DO FRR (Apenas ativa os daemons, não configura rotas)
DAEMONS = """
zebra=yes
bgpd=yes
vtysh_enable=yes
zebra_options=" -s 90000000 --daemon -A 127.0.0.1"
bgpd_options=" --daemon -A 127.0.0.1"
"""

VTYSH_CONF = """
hostname {name}
service integrated-vtysh-config
"""

#cria servidor ssh para cada roteador
def enable_ssh(net):
    print("\n*** Configurando SSH nos roteadores...")

    os.system("pkill -f 'socat TCP-LISTEN' >/dev/null 2>&1")
    os.system("rm -rf /tmp/r*")

    routers = [h for h in net.hosts if h.name.startswith("r")]

    for r in routers:
        num = int(r.name[1:])   
        port = 2200 + num
        base = f"/tmp/{r.name}" 

        r.cmd(f"mkdir -p {base}/ssh {base}/run")

        r.cmd(f"ssh-keygen -t rsa -f {base}/ssh/ssh_host_rsa_key -N '' >/dev/null 2>&1")

        #aceitar root com senha
        sshd_conf = f"Port {port}\nPermitRootLogin yes\nPasswordAuthentication yes\nPidFile {base}/run/sshd.pid\nHostKey {base}/ssh/ssh_host_rsa_key"
        
        r.cmd(f'echo "{sshd_conf}" > {base}/sshd_config')
        r.cmd("echo 'root:root' | chpasswd")

        r.cmd(f"/usr/sbin/sshd -f {base}/sshd_config")


        pid = r.pid
        # abre porta no socat qnd alguem acha ele direciona ao sshd usnado namepsace do roteador 
        subprocess.Popen(f"socat TCP-LISTEN:{port},fork EXEC:\"nsenter -t {pid} -n nc 127.0.0.1 {port}\"", shell=True)

    print("\n*** SSH habilitado nas portas 2201 a 2204 (Senha: root)")



class FRR(Node):
    PrivateDirs = ["/etc/frr", "/var/run/frr"]

    def __init__(self, name, **params):
        params.setdefault("privateDirs", []).extend(self.PrivateDirs)
        super().__init__(name, inNamespace=True, **params)

    def config(self, **params):
        super().config(**params)

        self.cmd("sysctl -w net.ipv4.ip_forward=1")
        self.cmd("ip link set lo up")
        
        self.cmd(f"printf '%s' '{DAEMONS}' > /etc/frr/daemons")
        self.cmd(f"printf '%s' '{VTYSH_CONF.format(name=self.name)}' > /etc/frr/vtysh.conf")
        self.cmd("chown -R frr:frr /etc/frr/ 2>/dev/null || true")
        self.cmd("/usr/lib/frr/frrinit.sh start")

class SimpleTopo(Topo):
    def build(self):
        r1 = self.addHost("r1", cls=FRR, ip=None)
        r2 = self.addHost("r2", cls=FRR, ip=None)
        r3 = self.addHost("r3", cls=FRR, ip=None)
        r4 = self.addHost("r4", cls=FRR, ip=None)
        s1 = self.addSwitch("s1", failMode="standalone")
        s2 = self.addSwitch("s2", failMode="standalone")

        self.addLink(s1, r1, intfName2="r1-eth1", params2={"ip": "203.0.1.1/24"})
        self.addLink(s2, r2, intfName2="r2-eth1", params2={"ip": "203.0.2.1/24"})
        self.addLink(r1, r2, intfName1="r1-eth2", intfName2="r2-eth2", params1={"ip": "203.0.12.1/30"}, params2={"ip": "203.0.12.2/30"})
        self.addLink(r2, r3, intfName1="r2-eth3", intfName2="r3-eth1", params1={"ip": "203.0.23.1/30"}, params2={"ip": "203.0.23.2/30"})
        self.addLink(r2, r4, intfName1="r2-eth4", intfName2="r4-eth1", params1={"ip": "203.0.24.1/30"}, params2={"ip": "203.0.24.2/30"})

        h1 = self.addHost("h1", ip="203.0.1.100/24", defaultRoute="via 203.0.1.1")
        h2 = self.addHost("h2", ip="203.0.2.100/24", defaultRoute="via 203.0.2.1")
        self.addLink(h1, s1)
        self.addLink(h2, s2)



def run():
    setLogLevel("info")
    net = Mininet(topo=SimpleTopo(), controller=None)
    
    net.start()
    # Chama a nossa função para abrir as portas
    enable_ssh(net) 
    
    print("\n Aguardando FRR inicializar  5s...")
    time.sleep(5)
    
    print("\n Topologia OK Rode o Nornir em outro terminal.")
    CLI(net) # Abre o terminal interativo do Mininet
    
    # Quando o usuário digitar 'exit' no Mininet, o código continua e limpa tudo
    os.system("pkill -f 'socat TCP-LISTEN' >/dev/null 2>&1")
    net.stop()

if __name__ == "__main__":
    run()