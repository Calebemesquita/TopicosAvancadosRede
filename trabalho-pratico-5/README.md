# Trabalho Pratico 5 - BGP, FRR, Nornir e GitOps

Este repositorio ja deixa pronta a base do trabalho:

- Topologia Mininet com `r1`, `r2`, `r3`, `r4`, `s1`, `s2`, `h1` e `h2`.
- FRR/BGP com MD5, TTL security, AS-PATH prepend, local-pref, filtros de bogons e communities.
- Automacao com Nornir + Jinja2.
- Scripts GitOps: validacao, dry-run, deploy manual e rollback.
- Pipeline GitLab CI/CD em `.gitlab-ci.yml`.
- Documentacao para NetBox, GitLab e deploy em `docs/`.

## Executar local

Terminal 1:

```bash
sudo python3 topo.py
```

Terminal 2:

```bash
python3 scripts/validate_templates.py
python3 scripts/dry_run.py
python3 scripts/deploy.py
```

Por padrao os scripts usam `inventory/hosts.yaml` com `r1-r4`. Quando
`NETBOX_URL` e `NETBOX_TOKEN` estiverem definidos, os scripts passam a buscar
dispositivos, interfaces, IPs e vizinhos no NetBox. Para a Atividade 11, suba
`sudo python3 topo.py --with-r5` e use o exemplo `inventory/hosts_with_r5.yaml`
como referencia para cadastrar o `r5` no NetBox.

Testes:

```bash
python3 -m pytest -q
```

Fluxo antigo tambem continua funcionando:

```bash
python3 main.py --step all
```

## Sua parte

1. Criar o projeto no GitLab e fazer push deste repositorio.
2. Cadastrar os dados no NetBox seguindo `docs/NETBOX_SETUP.md` e `examples/netbox_import.json`.
3. No GitLab, configurar as variaveis `NETBOX_URL` e `NETBOX_TOKEN`.
4. Abrir Merge Request, conferir pipeline `validate -> dry-run -> deploy` e executar `deploy` manualmente.
5. Guardar screenshots/logs para o relatorio.

## Gerar ZIP de entrega

```bash
python3 scripts/package_delivery.py
```

## Evidencias uteis

```bash
r2 vtysh -c "show bgp summary"
r2 vtysh -c "show ip bgp 203.100.2.0/24"
r3 vtysh -c "show ip bgp 203.0.1.0/24"
r4 vtysh -c "show ip bgp 203.0.2.0/24"
r2 vtysh -c "show ip bgp 192.168.100.0/24"
```
