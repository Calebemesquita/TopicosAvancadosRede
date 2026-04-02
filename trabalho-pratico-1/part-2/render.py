import yaml
from jinja2 import Environment, FileSystemLoader


with open('vars.yaml', 'r') as arquivo_dados:
    dados = yaml.safe_load(arquivo_dados)

ambiente = Environment(loader=FileSystemLoader('.'))
template = ambiente.get_template('bgp.j2')

for roteador in dados['roteadores']:
    nome_arquivo = f"{roteador['hostname']}.conf"
    config_gerada = template.render(roteador)
    with open(nome_arquivo, 'w') as arquivo_saida:
        arquivo_saida.write(config_gerada)
        
    print(f"Arquivo {nome_arquivo} gerado")


print("Configurações fram um sucesso")     