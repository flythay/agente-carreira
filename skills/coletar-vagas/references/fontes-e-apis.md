# Fontes de vagas — cobertura, acesso e limites

Verifique termos e limites na documentação oficial antes de usar em produção; eles mudam.

## Fontes com API pública

| Fonte | Cobertura | Autenticação | Endpoint | Observações |
|---|---|---|---|---|
| **Adzuna** | ~20 países (br, nl, de, gb, us, fr, ca, au…) | `app_id` + `app_key` grátis em developer.adzuna.com | `https://api.adzuna.com/v1/api/jobs/{pais}/search/{pagina}` | Melhor cobertura geográfica do conjunto. Descrição vem truncada e o salário costuma ser estimado (`salary_is_predicted`). Cota gratuita modesta (ordem de ~1.000 chamadas/mês) — gaste em descoberta, não em polling. |
| **Remotive** | Remoto, tech, global | nenhuma | `https://remotive.com/api/remote-jobs?search=` | Descrição completa. Os termos pedem link de volta e atribuição, e proíbem repassar as vagas para outros agregadores. |
| **RemoteOK** | Remoto, tech, global | nenhuma (exige `User-Agent`) | `https://remoteok.com/api` | Primeiro item do array é aviso legal, não vaga. As tags são pouco confiáveis para filtro — filtre por título e empresa. |
| **Arbeitnow** | Europa, forte na Alemanha | nenhuma | `https://www.arbeitnow.com/api/job-board-api` | Inclui presencial; filtre pelo booleano `remote` se quiser só remoto. |
| **Bundesagentur für Arbeit (Jobsuche)** | Alemanha, base pública federal | header `X-API-Key: jobboerse-jobsuche` | `https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs` | Maior base alemã. Interface documentada pela comunidade (bundesAPI/jobsuche-api); a busca traz resumo e a descrição completa exige uma segunda chamada de detalhe pela `refnr`. Versões da rota mudam (v4/v6) — confira a doc atual. |

## Quadros de empresa (ATS) — a fonte mais limpa

Muitas empresas expõem o próprio quadro de vagas em JSON, sem chave. Descubra o ATS pelo domínio do botão "apply".

| ATS | Endpoint | Como achar o slug |
|---|---|---|
| **Greenhouse** | `https://boards-api.greenhouse.io/v1/boards/{empresa}/jobs?content=true` | `boards.greenhouse.io/{empresa}` |
| **Lever** | `https://api.lever.co/v0/postings/{empresa}?mode=json` | `jobs.lever.co/{empresa}` |
| **Ashby** | `https://api.ashbyhq.com/posting-api/job-board/{empresa}` | `jobs.ashbyhq.com/{empresa}` |
| **Workable** | `https://apply.workable.com/api/v1/widget/accounts/{conta}?details=true` | `apply.workable.com/{conta}` |
| **SmartRecruiters** | `https://api.smartrecruiters.com/v1/companies/{empresa}/postings` | `jobs.smartrecruiters.com/{empresa}` |
| **Recruitee** | `https://{empresa}.recruitee.com/api/offers/` | `{empresa}.recruitee.com` |

Workday (`*.myworkdayjobs.com`) usa uma API interna que muda com frequência e não é destinada a consumo externo — para essas, use link + JSON-LD, ou copie o texto.

Vantagens: descrição íntegra, publicação em primeira mão, sem duplicata, sem redirecionamento. Montar uma lista de 30–60 empresas-alvo e varrer os quadros delas costuma render mais que qualquer agregador.

## Fontes que exigem cuidado

| Fonte | Situação |
|---|---|
| **LinkedIn** | Sem API pública de busca para este uso. Raspar viola os termos e pode custar a conta — que é justamente o ativo de quem procura emprego. Fluxo correto: encontrar manualmente e colar o link/texto no agente. |
| **Indeed** | O programa público de publishers foi descontinuado; hoje o acesso é comercial. Mesmo tratamento do LinkedIn. |
| **Glassdoor** | Sem API pública de vagas. Útil como pesquisa de empresa, manualmente. |
| **Google for Jobs** | Não é API; é resultado de busca. Acesso programático só via serviços pagos de SERP. |
| **EURES (UE)** | Portal público europeu com acesso a dados para parceiros; consulte a documentação atual antes de integrar. |
| **APIs "de agregação" em marketplaces (RapidAPI e similares)** | Funcionam e cobrem LinkedIn/Indeed indiretamente, mas são pagas e a procedência dos dados varia. Avalie o termo de uso antes de depender delas. |

## Regras de higiene

1. Respeite `robots.txt`, os termos de cada fonte e as exigências de atribuição.
2. Mantenha pausa entre chamadas e cache local; polling agressivo derruba a chave e não traz vaga nova mais rápido — anúncios não aparecem de minuto em minuto.
3. Guarde `data_publicacao` e descarte o que passou de ~30 dias.
4. Deduplique por `sha1(empresa|título|local)` normalizado; a mesma vaga aparece em várias fontes.
5. Não armazene dados pessoais de recrutadores. O que interessa é o anúncio.
6. Se o objetivo for um produto para terceiros (e não uso pessoal), revise licenciamento de conteúdo com cuidado: reexibir descrições completas de vagas de agregadores geralmente não é permitido.

## Cobertura por mercado-alvo

| Mercado | Combinação recomendada |
|---|---|
| Holanda | Adzuna (`nl`) + quadros Greenhouse/Lever de empresas de tech/fintech locais |
| Alemanha | Arbeitsagentur + Arbeitnow + Adzuna (`de`) |
| Reino Unido | Adzuna (`gb`) + quadros de ATS |
| Remoto internacional | Remotive + RemoteOK + quadros de empresas remote-first |
| Brasil | Adzuna (`br`) + quadros de ATS (Gupy publica JSON-LD nas páginas de vaga) |
