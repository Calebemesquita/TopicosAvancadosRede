# Scripts GitOps

- `validate_templates.py`: valida templates, sintaxe Python e, se `NETBOX_URL`/`NETBOX_TOKEN` existirem, testa a API do NetBox.
- `dry_run.py`: renderiza todas as configuracoes e salva `artifacts/dry_run_output.txt` com diff.
- `deploy.py`: job manual; aplica configs via SSH/vtysh nos roteadores Mininet.
- `check_ssh.py`: testa login SSH root/root em `r1-r4` nas portas `2201-2204`.
- `rollback.py`: reaplica backups salvos em `backups/`.

Fluxo local:

```bash
python3 scripts/validate_templates.py
python3 scripts/dry_run.py
python3 scripts/deploy.py
```
