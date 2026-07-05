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

# Remove os encaminhamentos antigos antes de subir uma nova topologia.
def cleanup_ssh():
    os.system("pkill -f 'socat TCP-LISTEN' >/dev/null 2>&1")
    os.system("rm -rf /tmp/r*")


# Cria servidor SSH para cada roteador e expõe via portas 2201, 2202...
def enable_ssh(net):
    print("\n*** Configurando SSH nos roteadores...")

    cleanup_ssh()

    routers = sorted(
        [h for h in net.hosts if h.name.startswith("r")],
        key=lambda host: int(host.name[1:]),
    )

    for r in routers:
        name = r.name
        num = int(name[1:])
        port = 2200 + num
        base = f"/tmp/{name}"

        print(f" -> Configurando {name} (porta {port})")

        r.cmd(f"mkdir -p {base}/ssh {base}/run")

        r.cmd(f"ssh-keygen -t rsa -f {base}/ssh/ssh_host_rsa_key -N '' >/dev/null 2>&1")
        r.cmd(f"ssh-keygen -t ecdsa -f {base}/ssh/ssh_host_ecdsa_key -N '' >/dev/null 2>&1")
        r.cmd(f"ssh-keygen -t ed25519 -f {base}/ssh/ssh_host_ed25519_key -N '' >/dev/null 2>&1")

        sshd_conf = f"""
Port {port}
Protocol 2
PermitRootLogin yes
PasswordAuthentication yes
UsePAM no
Subsystem sftp internal-sftp
PidFile {base}/run/sshd.pid
HostKey {base}/ssh/ssh_host_rsa_key
HostKey {base}/ssh/ssh_host_ecdsa_key
HostKey {base}/ssh/ssh_host_ed25519_key
"""

        r.cmd(f"cat > {base}/sshd_config <<'EOF'\n{sshd_conf}\nEOF")
        r.cmd("echo 'root:root' | chpasswd")
        r.cmd(f"/usr/sbin/sshd -f {base}/sshd_config")

        pid = r.pid
        socat_cmd = (
            f"socat TCP-LISTEN:{port},fork "
            f"EXEC:\"nsenter -t {pid} -n nc 127.0.0.1 {port}\""
        )
        subprocess.Popen(socat_cmd, shell=True)

    print("\n*** SSH habilitado! Acesse com senha root/root:")
    for r in routers:
        port = 2200 + int(r.name[1:])
        print(f"    ssh -p {port} root@127.0.0.1   # {r.name}")



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
    def build(self, with_r5=False):
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

        # Atividade 11 (GitOps E2E): novo roteador r5, AS 65030, eBGP com r2.
        # Ligar com: sudo python3 topo.py --with-r5
        if with_r5:
            r5 = self.addHost("r5", cls=FRR, ip=None)
            self.addLink(
                r2, r5,
                intfName1="r2-eth5", intfName2="r5-eth1",
                params1={"ip": "203.0.25.1/30"}, params2={"ip": "203.0.25.2/30"},
            )



def run(with_r5=False):
    setLogLevel("info")
    net = Mininet(topo=SimpleTopo(with_r5=with_r5), controller=None)
    
    net.start()
    # Chama a nossa função para abrir as portas
    enable_ssh(net) 
    
    print("\n Aguardando FRR inicializar  5s...")
    time.sleep(5)
    
    print("\n Topologia OK Rode o Nornir em outro terminal.")
    CLI(net) # Abre o terminal interativo do Mininet
    
    # Quando o usuário digitar 'exit' no Mininet, o código continua e limpa tudo
    cleanup_ssh()
    net.stop()

if __name__ == "__main__":
    import sys
    run(with_r5="--with-r5" in sys.argv)
