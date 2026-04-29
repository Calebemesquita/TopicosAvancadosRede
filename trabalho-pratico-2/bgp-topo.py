#!/usr/bin/python3

"""
================================================================================
LABORATÓRIO DE REDES: EMULAÇÃO BGP COM MININET E FRROUTING (FRR)
================================================================================

Este script automatiza a criação de um ambiente de rede para testes de protocolos
de roteamento dinâmico. Abaixo, uma breve introdução sobre as ferramentas:

1. O QUE É O MININET?
   O Mininet é um emulador de redes que cria uma rede virtual de hosts, switches,
   controladores e links em um único kernel Linux. Ele utiliza "Network Namespaces"
   para que cada host/roteador pareça uma máquina real com sua própria tabela de
   interfaces e rotas, permitindo testar topologias complexas em um PC comum.

2. O QUE É O FRROUTING (FRR)?
   O FRR é uma suíte de protocolos de roteamento IP para plataformas Unix e Linux.
   Ele é um "fork" do antigo projeto Quagga e implementa protocolos como BGP, 
   OSPF, RIP e IS-IS. No contexto deste script, o FRR transforma um nó comum do 
   Mininet em um roteador robusto capaz de trocar rotas dinamicamente.

3. CENÁRIO DESTE SCRIPT:
   Criamos dois Sistemas Autônomos (AS 65001 e AS 65002). O protocolo BGP é usado
   para que o Roteador 1 "anuncie" sua rede local para o Roteador 2, e vice-versa,
   estabelecendo conectividade fim-a-fim entre os hosts H1 e H2.
================================================================================
"""

from mininet.net import Mininet
from mininet.node import Node
from mininet.topo import Topo
from mininet.cli import CLI
from mininet.log import setLogLevel

# ---------------------------------------------------------
# CONFIGURAÇÃO DOS DAEMONS E AMBIENTE DO FRR
# ---------------------------------------------------------

# Arquivo 'daemons': define quais serviços do FRR serão iniciados.
# Precisamos do 'zebra' (núcleo) e 'bgpd' (protocolo BGP).
daemons = """
zebra=yes
bgpd=yes

vtysh_enable=yes
zebra_options=" -s 90000000 --daemon -A 127.0.0.1"
bgpd_options=" --daemon -A 127.0.0.1"
"""
# Configuração base do terminal interativo (vtysh)
vtysh = """
hostname {name}
service integrated-vtysh-config
"""

class FRR(Node):
    """
    Classe customizada para criar nós que rodam o FRRouting.
    Estende a classe 'Node' original do Mininet.
    """
    # Diretórios que precisam ser isolados para cada roteador
    PrivateDirs = ["/etc/frr", "/var/run/frr"]

    def __init__(self, name, inNamespace=True, **params):
        params.setdefault("privateDirs", [])
        params["privateDirs"].extend(self.PrivateDirs)
        super().__init__(name, inNamespace=inNamespace, **params)

    def config(self, **params):
        """Aplica configurações de sistema ao iniciar o nó."""
        super().config(**params)
        # Habilita o encaminhamento de pacotes IP (essencial para roteadores)
        self.cmd("sysctl -w net.ipv4.ip_forward=1")
        self.start_frr()

    def start_frr(self):
        """Gera os arquivos de config e inicia os serviços do FRR."""
        self.set_conf("/etc/frr/daemons", daemons)
        self.set_conf("/etc/frr/vtysh.conf", vtysh.format(name=self.name))
        # Executa o script de inicialização padrão do FRR
        print(self.cmd("/usr/lib/frr/frrinit.sh start"))

    def set_conf(self, file, content):
        """Método auxiliar para escrever arquivos dentro do nó."""
        self.cmd(f"cat << 'EOF' > {file}\n{content}\nEOF")

    def vtysh_cmd(self, cmd):
        """Envia comandos de rede diretamente para o VTYSH do roteador."""
        full = "vtysh"
        for c in cmd.split("\n"): # Ignora linhas vazias
            full += f" -c \"{c}\""
        return self.cmd(full)


# ---------------------------------------------------------
# COMANDOS DE CONFIGURAÇÃO BGP (Sintaxe Cisco-like)
# ---------------------------------------------------------

# Configuração para o Roteador 1 (AS 65001)
r1_conf = """\
enable
configure terminal
# COMPLETE AQUI
"""

# Configuração para o Roteador 2 (AS 65002)
r2_conf = """\
enable
configure terminal
# COMPLETE AQUI
"""

# ---------------------------------------------------------
# DEFINIÇÃO DA TOPOLOGIA
# ---------------------------------------------------------

class SimpleTopo(Topo):
    """
    Define a estrutura da rede:
    H1 --- S1 --- R1 --- R2 --- S2 --- H2
    """
    def build(self):

        # 1. Criar Roteadores FRR
        r1 = self.addHost('r1', cls=FRR, ip=None)
        r2 = self.addHost('r2', cls=FRR, ip=None)

        # 2. Adicionar Switches (atuam como camada 2 simples)
        s1 = self.addSwitch('s1', failMode='standalone')
        s2 = self.addSwitch('s2', failMode='standalone')

        # 3. Conectar Switches aos Roteadores (Redes Locais)
        # Interface r1-eth1 conectada à rede 10.0.1.0/24
        self.addLink(s1,
                     r1,
                     intfName2='r1-eth1',
                     params2={'ip': '10.0.1.1/24'})

        # Interface r2-eth1 conectada à rede 10.0.2.0/24
        self.addLink(s2,
                     r2,
                     intfName2='r2-eth1',
                     params2={'ip': '10.0.2.1/24'})

        # 4. Conectar Roteador ao Roteador (Link Ponto-a-Ponto)
        # Rede 10.0.12.0/24 usada para o tráfego BGP entre R1 e R2
        self.addLink(r1,
                     r2,
                     intfName1='r1-eth2',
                     intfName2='r2-eth2',
                     params1={'ip': '10.0.12.1/24'},
                     params2={'ip': '10.0.12.2/24'})

        # 5. Criar Hosts Finais
        # Configurados com o gateway padrão apontando para seus respectivos roteadores
        h1 = self.addHost('h1', ip='10.0.1.100/24', defaultRoute='via 10.0.1.1')
        h2 = self.addHost('h2', ip='10.0.2.100/24', defaultRoute='via 10.0.2.1')

        # 6. Conectar Hosts aos seus Switches
        self.addLink(h1, s1)
        self.addLink(h2, s2)


# ---------------------------------------------------------
# EXECUÇÃO DO SCRIPT
# ---------------------------------------------------------

def run():
    # Define o nível de log para ver o progresso no terminal
    setLogLevel("info")

    topo = SimpleTopo()
    # Criamos a rede sem controlador SDN externo (usaremos roteamento tradicional)
    net = Mininet(topo=topo, controller=None)
    net.start()

    # Recupera os objetos dos roteadores para injetar a configuração BGP
    r1 = net.get('r1')
    r2 = net.get('r2')

    # Aplicar as strings de configuração BGP via VTYSH
    print("\n*** Configurando BGP nos roteadores...")
    r1.vtysh_cmd(r1_conf)
    r2.vtysh_cmd(r2_conf)

    print("\n*** Topologia pronta!")
    print("*** Aguarde alguns segundos para a convergência do BGP.")
    print("*** Teste: h1 ping 10.0.2.100")

    # Abre o console interativo do Mininet
    CLI(net)

    # Para a rede ao sair do CLI
    net.stop()


if __name__ == "__main__":
    run()