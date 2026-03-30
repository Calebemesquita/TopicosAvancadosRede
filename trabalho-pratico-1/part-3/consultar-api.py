import pynetbox
import os
import json

TOKEN = os.getenv("NETBOX_TOKEN", "nbt_X7AWjlq61u31.p41nkaxHIfDuW4eBwJjLYpQmUtK5ozi9Einj8i5L")
NETBOX_URL = os.getenv("NETBOX_URL", "http://localhost:8000")

nb = pynetbox.api(url=NETBOX_URL, token=TOKEN)

try:
    print("Conectando ao NetBox")
    
    roteadores = nb.dcim.devices.filter(role="router")
    
    dados_jinja2 = {"roteadores": []}
    
    for roteador in roteadores:
        hostname = roteador.name.lower()
        
        asn = roteador.config_context.get('asn', 'N/A')
        router_id = roteador.config_context.get('router_id', 'N/A')
        
        ips_recordset = nb.ipam.ip_addresses.filter(device=roteador.name)
        ips_lista = list(ips_recordset) 
        ip_limpo = str(ips_lista[0]).split('/')[0] if ips_lista else "Sem IP"
        
        vizinhos_raw = roteador.custom_fields.get('vizinhos_bgp')
        vizinhos_lista = []
        if vizinhos_raw:
            vizinhos_lista = json.loads(vizinhos_raw)
            
        print(f"Lido: {hostname.upper()} | ASN: {asn} | IP: {ip_limpo} | Vizinhos: {len(vizinhos_lista)}")
        
        dados_jinja2["roteadores"].append({
            "hostname": hostname,
            "asn": asn,
            "router_id": router_id,
            "network": f"192.168.{hostname[1]}.0/24", 
            "neighbors": vizinhos_lista
        })
        
    with open('netbox_dados_jinja.json', 'w') as arquivo:
        json.dump(dados_jinja2, arquivo, indent=4)
        
    print("\n Sucesso 'netbox_dados_jinja.json' gerado.")

except Exception as e:
    print(f"Erro {e}")