# Deploy — como colocar o agente num servidor

Três caminhos, do menor para o maior esforço. Escolha pelo número de usuários e pela necessidade de rodar sozinho.

| Caminho | Quando | Custo/mês | Esforço |
|---|---|---|---|
| **A. Sem servidor** — skills dentro do Claude | uso pessoal, sem automação | 0 (além da assinatura) | minutos |
| **B. VPS com Docker** — Streamlit ou FastAPI + Postgres + cron | uso pessoal com radar automático, ou poucos usuários | US$ 5–15 | uma tarde |
| **C. PaaS gerenciado** — Fly.io / Railway / Render | quer evitar administrar servidor | US$ 5–25 | 1–2 horas |

Recomendação prática: comece em A, vá para B quando quiser o radar diário rodando sem você. C é atalho legítimo se administrar Linux não te interessa.

---

## A. Sem servidor

Copie a pasta `skills/` para onde o Claude a enxergue:

- **Claude.ai** — empacote cada skill em `.skill` e instale pelo cartão de arquivo.
- **Claude Code** — `cp -r skills/* ~/.claude/skills/` (global) ou `.claude/skills/` no projeto.
- **Cowork** — mesma estrutura de pastas.

Os scripts rodam com Python 3.10+; só o `render_cv.py` precisa de dependência (`pip install python-docx`).

Vantagem além do custo: a interface é a conversa, e é justamente ali que a entrevista de enriquecimento funciona melhor.

---

## B. VPS com Docker (recomendado)

### B.1 Servidor

Qualquer VPS de 2 vCPU / 2–4 GB serve — a carga é I/O de rede, não CPU. Hetzner, DigitalOcean, Vultr e Contabo ficam na faixa de US$ 5–15. Se a maior parte dos usuários for do Brasil, escolha região São Paulo pela latência.

Preparação inicial (Ubuntu 24.04):

```bash
adduser agente && usermod -aG sudo agente
# copie sua chave SSH para o novo usuário, depois:
sudo sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/;s/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart ssh
sudo ufw allow OpenSSH && sudo ufw allow 80,443/tcp && sudo ufw enable
sudo apt update && sudo apt install -y docker.io docker-compose-plugin
sudo usermod -aG docker agente
sudo apt install -y unattended-upgrades   # correções de segurança automáticas
```

Desabilitar login de root e senha é o que evita 99% das tentativas automatizadas. Não pule.

### B.2 Estrutura do projeto

```
agente-carreira/
├── docker-compose.yml
├── Caddyfile
├── .env                    # NUNCA no git
├── app/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py             # FastAPI ou app.py (Streamlit)
│   ├── modulos/            # wrappers dos SKILL.md como system prompts
│   └── skills/             # copiada deste repositório
├── dados/                  # volume: SQLite/arquivos gerados
└── backups/
```

### B.3 `docker-compose.yml`

```yaml
services:
  app:
    build: ./app
    restart: unless-stopped
    env_file: .env
    volumes:
      - ./dados:/dados
    expose: ["8000"]
    depends_on: [db]

  db:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: agente
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: agente
    volumes:
      - pgdata:/var/lib/postgresql/data

  radar:
    build: ./app
    restart: unless-stopped
    env_file: .env
    volumes:
      - ./dados:/dados
    command: python -m app.radar --loop --hora 06:00
    depends_on: [db]

  caddy:
    image: caddy:2-alpine
    restart: unless-stopped
    ports: ["80:80", "443:443"]
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddydata:/data
    depends_on: [app]

volumes:
  pgdata:
  caddydata:
```

### B.4 `Caddyfile` — HTTPS automático

```
agente.seudominio.com {
    encode gzip
    reverse_proxy app:8000
    basicauth {
        # gere com: docker run --rm caddy caddy hash-password
        thay $2a$14$hash_gerado_aqui
    }
}
```

O Caddy emite e renova o certificado Let's Encrypt sozinho — só aponte o DNS para o IP do servidor antes de subir. O `basicauth` é uma trava de uma linha, suficiente enquanto o sistema for pessoal; ao abrir para outras pessoas, troque por autenticação de verdade.

### B.5 `.env`

```env
ANTHROPIC_API_KEY=sk-ant-...
ADZUNA_APP_ID=...
ADZUNA_APP_KEY=...
POSTGRES_PASSWORD=...
DATABASE_URL=postgresql://agente:${POSTGRES_PASSWORD}@db:5432/agente
LIMITE_CUSTO_DIARIO_USD=2.00
EMAIL_DESTINO=voce@email.com
SMTP_HOST=...
SMTP_USER=...
SMTP_PASS=...
```

`chmod 600 .env` e `.env` na primeira linha do `.gitignore`. Chave de API vazada em repositório público é minerada em minutos.

### B.6 Subir

```bash
docker compose up -d --build
docker compose logs -f app
```

### B.7 Radar agendado

Duas opções. Dentro do container (como no compose acima), com um laço que dorme até a hora marcada — mais simples de mover entre servidores. Ou no host, com cron:

```cron
0 6 * * * cd /home/agente/agente-carreira && docker compose run --rm app python -m app.radar >> /var/log/radar.log 2>&1
```

Cron no host é mais fácil de depurar; agendador no container é mais portátil. Para um projeto pessoal, cron resolve.

### B.8 Backup

```bash
#!/bin/bash
# /home/agente/backup.sh — diário às 3h
set -euo pipefail
D=$(date +%F)
cd /home/agente/agente-carreira
docker compose exec -T db pg_dump -U agente agente | gzip > backups/db_$D.sql.gz
tar czf backups/arquivos_$D.tar.gz dados/
gpg --batch --yes --passphrase-file ~/.backup_pass -c backups/db_$D.sql.gz
find backups/ -name '*.gz*' -mtime +30 -delete
# envie para armazenamento externo (rclone, S3, Backblaze)
```

Backup criptografado porque o conteúdo é dado pessoal. E **teste a restauração pelo menos uma vez** — backup nunca testado costuma não existir.

### B.9 Operação

- **Logs**: `docker compose logs --tail=100 -f app`. Estruture em JSON e registre módulo, tokens, latência e erro — nunca o conteúdo do currículo.
- **Monitoramento**: um endpoint `/health` e um monitor externo gratuito (UptimeRobot, Healthchecks.io) que avisa quando o radar não roda.
- **Teto de custo**: some `custo_usd` do dia antes de cada chamada; ao passar de `LIMITE_CUSTO_DIARIO_USD`, pare e avise. Um laço com bug pode gastar em uma noite o orçamento do mês.
- **Atualização**: `git pull && docker compose up -d --build`. Faça backup antes.

---

## C. PaaS gerenciado

**Fly.io** — bom encaixe: um `fly.toml`, `fly deploy`, Postgres gerenciado, `fly secrets set` para as chaves, e máquinas que hibernam quando ociosas (o uso é intermitente por natureza). Cron via *scheduled machines*.

**Railway / Render** — deploy direto do repositório, TLS e Postgres inclusos, cron job nativo. Mais caro conforme escala, mas zero administração de servidor.

**Streamlit Community Cloud** — grátis, mas o app é público por padrão e não há banco persistente. Serve para demonstração, **não** para dados pessoais reais.

Em qualquer PaaS: segredos no gerenciador da plataforma (nunca no repositório), volume persistente configurado (senão o SQLite some no redeploy) e backup próprio — o plano gratuito raramente inclui backup útil.

---

## Checklist de produção

- [ ] Login por chave SSH; root e senha desabilitados; firewall ativo
- [ ] HTTPS funcionando com renovação automática
- [ ] Segredos fora do repositório, `.env` com `chmod 600`
- [ ] Volume persistente para banco e arquivos gerados
- [ ] Backup diário criptografado, com cópia fora do servidor, restauração testada
- [ ] Atualizações de segurança automáticas
- [ ] Teto de custo diário de API implementado
- [ ] Monitoramento externo com alerta
- [ ] Política de retenção de dados escrita e implementada (LGPD/GDPR)
- [ ] Rotina de exclusão total de um usuário testada
- [ ] Logs sem conteúdo de currículo
