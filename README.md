# Agente de Carreira — pacote completo

Currículo ATS/Harvard a partir de conversa, adaptação por vaga, score de aderência, plano de preparação e coleta de vagas.

## Conteúdo

| Arquivo | O que é |
|---|---|
| `PLANO_IMPLEMENTACAO.md` | Arquitetura, modelo de dados, modelos de LLM e custo, roadmap por fases, qualidade, privacidade, riscos e mapeamento OO |
| `DEPLOY.md` | Três caminhos de servidor (sem servidor / VPS Docker / PaaS), com compose, HTTPS, backup, cron e checklist |
| `skills/` | As cinco skills, prontas para instalar |
| `*.skill` | Cada skill empacotada para instalação direta no Claude |

## As cinco skills

| Skill | Faz | Scripts inclusos |
|---|---|---|
| `curriculo-ats-harvard` | Currículo do zero a partir de linguagem natural, com entrevista de enriquecimento; formato Harvard + regras de ATS | `render_cv.py` (JSON → Markdown + DOCX ATS-safe) |
| `adaptar-curriculo-vaga` | Reescreve o currículo para uma vaga sem inventar nada; trata os gaps | — |
| `match-score-vaga` | Score 0–100 com evidência por requisito e gaps priorizados | `match_score.py` (determinístico, sem dependências) |
| `plano-preparacao-vaga` | Cronograma de estudo, banco de perguntas com respostas ancoradas, simulação | `gerar_plano.py` |
| `coletar-vagas` | Vaga por link (JSON-LD/ATS) e busca em APIs oficiais | `vaga_de_url.py`, `buscar_vagas.py` |

## Como instalar

**Claude.ai** — abra cada arquivo `.skill` e use "Save skill".

**Claude Code / Cowork** — `cp -r skills/* ~/.claude/skills/`

Dependências: Python 3.10+. Só `render_cv.py` precisa de biblioteca externa (`pip install python-docx`); os demais usam apenas a biblioteca padrão.

## Fluxo típico

```bash
# 1. Vaga por link
python skills/coletar-vagas/scripts/vaga_de_url.py "https://..." --saida vaga.json
#    (o Claude classifica requisitos, pesos e eliminatórios no vaga.json)

# 2. Aderência
python skills/match-score-vaga/scripts/match_score.py perfil.json vaga.json \
       --json --saida score.json

# 3. Adaptar (com o Claude) e renderizar
python skills/curriculo-ats-harvard/scripts/render_cv.py perfil_adaptado.json \
       --idioma en --saida vagas/empresa/

# 4. Preparação
python skills/plano-preparacao-vaga/scripts/gerar_plano.py score.json \
       --data-entrevista 2026-09-15 --horas-dia 2 --saida plano.md
```

## Contratos de dados

Dois arquivos ligam tudo:

- `perfil.json` — schema em `skills/curriculo-ats-harvard/assets/perfil.schema.json`
- `vaga.json` — schema em `skills/match-score-vaga/references/formato-vaga.md`

Qualquer módulo novo se conecta a esses dois formatos sem alterar o resto.

## Regra que atravessa todo o sistema

Nada de inventar experiência, ferramenta, número ou certificação. O que falta vira gap declarado, e gap vira plano de estudo — não texto no currículo.
