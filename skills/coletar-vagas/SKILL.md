---
name: coletar-vagas
description: Busca vagas em fontes com API pública (Remotive, RemoteOK, Arbeitnow, Arbeitsagentur, Adzuna, quadros Greenhouse/Lever/Ashby) e extrai uma vaga específica a partir de um link colado, normalizando tudo para o formato que os skills de score, adaptação e preparação consomem. Use sempre que o usuário colar o link de uma vaga, pedir "procura vagas de X em Y", quiser montar uma lista de vagas para triagem, perguntar onde procurar vagas no exterior, ou quiser automatizar um radar diário de oportunidades.
---

# Coleta de vagas

Duas portas de entrada, mesmo formato de saída (`vaga.json`, ver `../match-score-vaga/references/formato-vaga.md`):

1. **Link colado** — o caminho mais comum. `scripts/vaga_de_url.py`.
2. **Busca por fonte** — para montar lista e triar em lote. `scripts/buscar_vagas.py`.

Em ambos, os scripts trazem os dados brutos; **classificar requisitos, pesos e eliminatórios é trabalho do modelo**, com julgamento, seguindo as regras do formato de vaga.

## Vaga por link

```bash
python scripts/vaga_de_url.py "https://boards.greenhouse.io/empresa/jobs/123" --saida vaga.json
```

O script tenta, nesta ordem: endpoint JSON do ATS (quando reconhece Greenhouse, Lever ou Ashby na URL) → JSON-LD `schema.org/JobPosting` embutido na página → texto limpo da página.

O JSON-LD funciona com alta taxa de acerto porque quem quer aparecer no Google for Jobs precisa publicá-lo — o que cobre a maioria dos ATS. Quando ele existe, vêm título, empresa, local, datas, faixa salarial e descrição já estruturados.

Quando falha (login obrigatório, página só em JavaScript, bloqueio a acesso automatizado), o comportamento correto é **pedir ao usuário que cole o texto do anúncio**. Não tente contornar bloqueio, resolver captcha ou usar credencial de terceiro: além de violar os termos de uso do site, é o tipo de coisa que faz a conta do usuário ser suspensa justamente na plataforma onde ele está se candidatando.

LinkedIn e Indeed entram por aqui: **colando o texto**. Nenhum dos dois tem API pública de busca para este uso, e raspar os dois é violação de termos.

## Busca por fonte

```bash
# remoto/tech, sem chave nenhuma
python scripts/buscar_vagas.py --termo "fraud data scientist" --fontes remotive,remoteok

# Holanda via Adzuna (precisa de app_id/app_key gratuitos)
python scripts/buscar_vagas.py --termo "data scientist" --fontes adzuna --pais nl --paginas 2

# quadro de empresas específicas — a fonte mais limpa que existe
python scripts/buscar_vagas.py --fontes greenhouse,lever --empresas adyen,mollie,bolt

# radar diário, só anúncios das últimas 2 semanas
python scripts/buscar_vagas.py --termo "risk" --fontes todas --min-dias 14 --saida vagas/
```

Detalhes de cada fonte (cobertura, chave, limite, termos de uso) em `references/fontes-e-apis.md`. Leia antes de sugerir uma fonte ao usuário — recomendar a fonte errada para o mercado dele desperdiça o esforço todo.

A saída é deduplicada por `sha1(empresa|título|local)`, o que resolve o problema real de agregadores: a mesma vaga aparece em quatro sites com títulos ligeiramente diferentes.

## Estratégia: vá até a fonte, não até o agregador

Agregador é bom para descobrir empresas; é ruim para se candidatar. O anúncio costuma estar desatualizado, o link redireciona e a candidatura passa por camadas extras.

O fluxo que funciona melhor para busca internacional:

1. Use agregadores (Adzuna, Remotive, Arbeitnow) para **mapear quais empresas contratam o seu perfil** no país-alvo.
2. Monte uma lista de 30–60 empresas-alvo e descubra qual ATS cada uma usa (o domínio do botão "apply" entrega: `boards.greenhouse.io`, `jobs.lever.co`, `jobs.ashbyhq.com`, `myworkdayjobs.com`).
3. Consulte **direto o quadro delas** com `--fontes greenhouse,lever,ashby --empresas ...`. As vagas aparecem ali primeiro, com descrição completa, e a candidatura é direta.

Isso troca "aplicar em 50 vagas por dia em agregador" por "aplicar em 10 vagas na fonte, com currículo adaptado" — que é o que muda a taxa de resposta.

## Radar automático

Para monitoramento contínuo, o padrão é: cron diário → `buscar_vagas.py` → `match_score.py` contra o perfil base → notificar só o que passou de um limiar (ex.: ≥ 65). Persista os ids já vistos, senão a primeira execução dispara um alerta com o backlog inteiro e as seguintes repetem as mesmas vagas por semanas. Implementação no `PLANO_IMPLEMENTACAO.md` do projeto.

## Higiene ao usar as APIs

- Respeite `robots.txt` e os termos de cada fonte; algumas exigem atribuição e link de volta (Remotive é explícita quanto a isso).
- Mantenha a pausa entre chamadas que já está nos scripts. Volume agressivo derruba a chave e não acelera nada.
- Guarde `data_publicacao` e descarte anúncio velho: vaga com mais de 30 dias frequentemente já tem candidato escolhido.
- Nunca armazene dados pessoais de terceiros (nome de recrutador, contatos) coletados dessas fontes.

## Arquivos deste skill

- `scripts/vaga_de_url.py` — extração por link (ATS API → JSON-LD → texto)
- `scripts/buscar_vagas.py` — busca multi-fonte, normalização e dedup
- `references/fontes-e-apis.md` — cobertura, autenticação, limites e termos de cada fonte
