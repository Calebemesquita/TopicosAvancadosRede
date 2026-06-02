# Trabalho Prático - BGP com Nornir e FRR

## Como executar a topologia:
1. Inicie a infraestrutura de rede (Mininet):
   sudo python3 topo.py

2. Em um segundo terminal, na mesma pasta, execute a automação BGP:
   python3 main.py --step all

3. Aguarde 15 segundos para a convergência e verifique as tabelas BGP via CLI do Mininet.
