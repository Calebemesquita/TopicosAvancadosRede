import json

# r de read
# arquivo variavel que damos ao arquivo aberto
with open('netbox_dados_jinja.json', 'r') as arquivo:
    dados = json.load(arquivo)

print("Tipo dos dados:", type(dados))         
print("Chaves do dicionário:", dados.keys()) 