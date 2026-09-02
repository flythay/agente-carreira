# Agente de Carreira — Plano de Implementação

Agente que transforma linguagem natural em currículo ATS/Harvard, adapta o documento por vaga, mede aderência, monta plano de preparação e alimenta tudo com vagas coletadas de fontes oficiais.

Este documento é o plano de construção. As cinco skills em `skills/` são a inteligência do sistema — elas funcionam sozinhas dentro do Claude (Claude.ai, Claude Code ou Cowork) e também são o "cérebro" do serviço quando ele virar aplicação.

---

## 1. Escopo

### O que o agente faz

| # | Capacidade | Skill correspondente |
|---|---|---|
| 1 | Currículo do zero ou reescrito, a partir de conversa, com entrevista de enriquecimento | `curriculo-ats-harvard` |
| 2 | Adaptação por vaga sem inventar informação | `adaptar-curriculo-vaga` |
| 3 | Score de aderência 0–100, explicável, com gaps priorizados | `match-score-vaga` |
| 4 | Plano de preparação com cronograma, banco de perguntas e simulação | `plano-preparacao-vaga` |
| 5 | Vagas por link e por busca em APIs oficiais | `coletar-vagas` |

### O que fica de fora (decisão consciente)

- Candidatura automática em massa. Viola termos de vários sistemas e produz candidatura ruim — o gargalo não é volume, é aderência.
- Raspagem de LinkedIn/Indeed. Ver `skills/coletar-vagas/references/fontes-e-apis.md`.
- Geração de PDF pelo LLM. O modelo escreve conteúdo; layout é código.
- Qualquer invenção de experiência. É regra de negócio, não preferência de estilo.

### Princípio de arquitetura

**LLM para julgamento, código para o que precisa ser reproduzível.** Extrair requisitos de um anúncio exige interpretação → LLM. Calcular o score, renderizar DOCX, deduplicar vagas, alocar horas de estudo → código determinístico. Isso é o que permite comparar duas vagas no mesmo critério e explicar cada número.

---

## 2. Arquitetura

```
                     ┌──────────────────────────────┐
   texto livre  ───► │  1. Coletor / Estruturador   │ ──► perfil.json
   CV antigo         │     (LLM + entrevista)       │      (fonte da verdade)
                     └──────────────────────────────┘
                                    │
   link de vaga ─┐                  ▼
   busca API   ──┼──► ┌──────────────────────────────┐
                 └──► │  2. Coletor de vagas         │ ──► vaga.json
                      │  (scripts + LLM classifica)  │
                      └──────────────────────────────┘
                                    │
                                    ▼
                      ┌──────────────────────────────┐
                      │  3. Score de aderência       │ ──► score.json
                      │     (Python determinístico)  │      (+ gaps)
                      └──────────────────────────────┘
                            │                    │
                            ▼                    ▼
        ┌───────────────────────────┐  ┌───────────────────────────┐
        │ 4. Adaptador por vaga     │  │ 5. Plano de preparação    │
        │    (LLM, sem inventar)    │  │    (script + LLM)         │
        └───────────────────────────┘  └───────────────────────────┘
                    │                              │
                    ▼                              ▼
            CV .docx/.pdf + carta          plano.md + simulação
```

`perfil.json` e `vaga.json` são os dois contratos do sistema (schemas em `skills/curriculo-ats-harvard/assets/perfil.schema.json` e `skills/match-score-vaga/references/formato-vaga.md`). Qualquer módulo novo se pluga neles sem tocar no resto.

### Duas formas de rodar

**A. Como skills dentro do Claude** — copiar `skills/` para o ambiente (Claude.ai via upload do `.skill`, Claude Code em `.claude/skills/`, ou Cowork). Zero infraestrutura, uso imediato, interface é a conversa. É o caminho recomendado para uso pessoal e para validar o produto.

**B. Como serviço** — API própria que chama o modelo, com banco, fila e interface web. Necessário quando houver outros usuários, radar automático rodando sozinho e histórico persistente. Ver `DEPLOY.md`.

O plano abaixo constrói B reaproveitando integralmente o conteúdo de A: os arquivos `SKILL.md` viram os *system prompts* de cada módulo, e os scripts viram funções chamadas pelo backend.

---

## 3. Modelo de dados

SQLite no começo (um arquivo, backup por cópia); Postgres quando houver mais de um usuário ou escrita concorrente.

```sql
CREATE TABLE usuario (
  id            TEXT PRIMARY KEY,
  nome          TEXT NOT NULL,
  email         TEXT UNIQUE NOT NULL,
  criado_em     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Versionado: nunca sobrescrever, sempre nova versão
CREATE TABLE perfil (
  id            TEXT PRIMARY KEY,
  usuario_id    TEXT REFERENCES usuario(id) ON DELETE CASCADE,
  versao        INTEGER NOT NULL,
  json          TEXT NOT NULL,           -- perfil.json completo
  idioma        TEXT,
  criado_em     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (usuario_id, versao)
);

CREATE TABLE vaga (
  id            TEXT PRIMARY KEY,        -- sha1(empresa|titulo|local)
  titulo        TEXT, empresa TEXT, local TEXT, modalidade TEXT,
  url           TEXT, fonte TEXT,
  data_publicacao DATE,
  json          TEXT NOT NULL,           -- vaga.json completo
  capturado_em  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE candidatura (
  id            TEXT PRIMARY KEY,
  usuario_id    TEXT REFERENCES usuario(id) ON DELETE CASCADE,
  vaga_id       TEXT REFERENCES vaga(id),
  perfil_id     TEXT REFERENCES perfil(id),   -- qual versão foi enviada
  score         REAL,
  score_json    TEXT,
  status        TEXT,   -- triagem|aplicada|resposta|entrevista|oferta|recusada
  aplicada_em   DATE,
  arquivo_cv    TEXT,
  notas         TEXT
);

CREATE TABLE evento_processo (          -- histórico da candidatura
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  candidatura_id TEXT REFERENCES candidatura(id) ON DELETE CASCADE,
  data          DATE, tipo TEXT, descricao TEXT
);

CREATE TABLE chamada_llm (              -- custo e depuração
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  usuario_id    TEXT, modulo TEXT, modelo TEXT,
  tokens_entrada INTEGER, tokens_saida INTEGER, tokens_cache INTEGER,
  custo_usd     REAL, latencia_ms INTEGER, erro TEXT,
  criado_em     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

`candidatura` + `evento_processo` são o que resolve o problema invisível de quem aplica em volume: descobrir **em que etapa** as candidaturas morrem. Se 40 aplicações viraram 3 triagens, o problema é o currículo; se 8 triagens viraram 0 ofertas, o problema é a entrevista. Sem esse registro, a pessoa refaz o currículo quando devia treinar entrevista.

---

## 4. Modelos e custo

Modelos atuais da API (IDs: `claude-opus-5`, `claude-sonnet-5`, `claude-haiku-4-5-20251001`). Preços por milhão de tokens mudam — confirme em https://docs.claude.com antes de fechar orçamento.

| Módulo | Modelo sugerido | Por quê |
|---|---|---|
| Estruturar perfil / extrair requisitos da vaga | Haiku 4.5 ou Sonnet 5 | Extração para JSON com schema fixo; tarefa barata e de alto volume |
| Gerar e adaptar currículo | Sonnet 5 | Qualidade de escrita e obediência a instruções longas; é o coração do produto |
| Plano de preparação e simulação de entrevista | Sonnet 5 | Diálogo longo; Opus 5 só se quiser feedback técnico mais profundo |
| Triagem em lote (dezenas de vagas/dia) | Haiku 4.5 + Batch API | Batch corta ~50%; a triagem tolera latência |

**Controles de custo que valem mais que a escolha do modelo:**
- *Prompt caching* no `perfil.json` e no texto da vaga — eles se repetem em várias chamadas (adaptar, pontuar, preparar) e cache reduz drasticamente o custo de entrada.
- `max_tokens` por módulo (currículo não precisa de 8.000 tokens de saída).
- Batch API para o radar noturno.
- Registrar toda chamada na tabela `chamada_llm`. Sem isso, custo vira surpresa.

Ordem de grandeza para uso pessoal intenso (uma pessoa, ~20 vagas/dia processadas): poucos dólares por mês. O custo relevante do projeto é o servidor, não o modelo.

---

## 5. Componentes a implementar

### 5.1 Saída estruturada confiável

Toda chamada que devolve JSON precisa de: schema no prompt, instrução explícita de "só JSON, sem markdown", `try/except` no parse, e **uma retentativa** enviando o erro de volta ao modelo. Sem a retentativa, ~1 em cada 50 chamadas quebra o fluxo por uma vírgula.

```python
def json_do_modelo(system, mensagens, tentativas=2):
    for i in range(tentativas):
        bruto = chamar(system, mensagens)
        texto = re.sub(r"^```(?:json)?|```$", "", bruto.strip(), flags=re.M).strip()
        try:
            return json.loads(texto)
        except json.JSONDecodeError as e:
            if i == tentativas - 1:
                raise
            mensagens = mensagens + [
                {"role": "assistant", "content": bruto},
                {"role": "user", "content": f"JSON inválido: {e}. Responda apenas o JSON corrigido."},
            ]
```

### 5.2 Guarda anti-invenção (o controle de qualidade mais importante)

Depois de adaptar um currículo, valide **por código** que nada novo apareceu:

```python
def termos_novos(perfil_base, perfil_adaptado):
    """Devolve termos técnicos presentes no adaptado e ausentes no base."""
    base = set(tokens(texto_perfil(perfil_base)))
    novo = set(tokens(texto_perfil(perfil_adaptado)))
    return sorted(novo - base)
```

Qualquer termo novo vai para revisão humana antes de gerar o arquivo. Isso transforma "pedimos ao modelo para não inventar" em uma garantia verificável — e é a diferença entre um brinquedo e algo em que se confia para enviar a um recrutador.

### 5.3 Pipeline do radar diário

```
cron 06:00 → buscar_vagas.py (fontes configuradas, --min-dias 14)
           → filtrar ids já vistos (tabela vaga)
           → LLM extrai requisitos (Haiku, batch)
           → match_score.py contra perfil base
           → gravar; notificar por e-mail só score ≥ limiar
```

Detalhes que decidem se o radar é útil ou irritante: semear a lista de "já vistos" na primeira execução (senão o primeiro e-mail traz o backlog inteiro), limitar a 10 vagas por notificação, e incluir score + os 3 gaps no corpo do e-mail para a decisão de aplicar acontecer sem abrir o sistema.

### 5.4 Interface

| Fase | Interface | Esforço |
|---|---|---|
| 0 | Skills dentro do Claude (sem código próprio) | horas |
| 1 | CLI + Streamlit (upload, chat, download do DOCX) | dias |
| 2 | FastAPI + front simples, autenticação, banco | semanas |
| 3 | Multiusuário, fila, cobrança | mês+ |

Não pule a fase 0. Ela responde de graça a pergunta mais cara do projeto: os prompts produzem currículo bom o suficiente para você enviar?

---

## 6. Roadmap

| Fase | Entrega | Critério de pronto |
|---|---|---|
| **0. Validação** (1 semana) | Skills instaladas no Claude; rodar com 3 vagas reais | Um currículo gerado que você enviaria de verdade |
| **1. Núcleo** (1–2 semanas) | Projeto Python, `perfil.json`, scripts de score/render, wrappers de API, logging | `entrada → CV.docx` roda pelo terminal ponta a ponta |
| **2. Vagas** (1 semana) | `vaga_de_url.py` + `buscar_vagas.py` integrados, banco SQLite | 20 vagas coletadas, pontuadas e ordenadas |
| **3. Interface** (1 semana) | Streamlit: perfil, vagas, score, download | Usável sem terminal |
| **4. Servidor** (2–3 dias) | Docker + VPS + HTTPS + backup | Acessível de fora, com TLS |
| **5. Radar** (3 dias) | Cron + e-mail com top vagas do dia | Um e-mail por dia, sem repetição |
| **6. Preparação** (1 semana) | Plano + simulação com histórico | Simulação completa com feedback |
| **7. Refino** | Ajuste de prompts com casos reais; painel de conversão por etapa | Métrica de funil visível |

Fases 0–3 já entregam a maior parte do valor. Fases 4–5 existem porque automação só compensa quando roda sem você.

---

## 7. Qualidade

Sem um conjunto fixo de casos, "melhorar o prompt" vira opinião. Monte um **golden set**: 10 vagas reais (5 do seu alvo, 3 adjacentes, 2 claramente fora) e 2 perfis (o seu e um sintético de outra área).

O que medir a cada mudança de prompt:

| Métrica | Como | Meta |
|---|---|---|
| Fidelidade | termos técnicos no CV adaptado ausentes no perfil base | **zero** |
| Ordenação do score | vagas fora do alvo pontuam abaixo das do alvo | 100% de acerto na ordem grosseira |
| Estabilidade | mesma vaga extraída 3× → mesmos requisitos obrigatórios | ≥ 80% de sobreposição |
| Parse | JSON válido na primeira tentativa | ≥ 95% |
| Cobertura ATS | requisitos obrigatórios literais no CV adaptado | ≥ 75% |
| Formato | CV cabe em 1–2 páginas, texto extraível na ordem certa | 100% |

E a única métrica que decide de verdade: **taxa de resposta por candidatura**, comparada antes e depois. Registre em `candidatura.status`.

---

## 8. Segurança e privacidade

Currículo é dado pessoal, e o banco vai conter e-mail, telefone, histórico profissional e às vezes pretensão salarial. LGPD (e GDPR, se houver usuário europeu) se aplicam.

- **Segredos** em variável de ambiente ou gerenciador de segredos. Nunca no código, nunca no repositório. `.env` no `.gitignore` desde o primeiro commit.
- **Criptografia**: TLS em trânsito (Caddy/Let's Encrypt resolve), disco criptografado no servidor, backup criptografado.
- **Minimização**: não guarde o que não usa. Documento antigo com CPF/RG deve ser descartado depois da extração.
- **Retenção**: política explícita (ex.: 12 meses de inatividade → apagar) e rotina que a execute.
- **Exclusão**: `DELETE CASCADE` já no schema, mais um endpoint/rotina que apague os arquivos gerados.
- **Isolamento**: se houver mais de um usuário, toda consulta filtra por `usuario_id`. Testar isso explicitamente — vazamento entre usuários num sistema de currículos é incidente grave.
- **Logs**: registre tokens e latência, não o conteúdo do currículo.
- **Terceiros**: dados vão para a API do modelo. Se o serviço for para outras pessoas, isso precisa estar na política de privacidade.

---

## 9. Riscos

| Risco | Mitigação |
|---|---|
| Modelo inventa experiência | Guarda anti-invenção por código (5.2) + revisão humana antes do envio |
| Fonte de vagas muda ou cai | Cada fonte é um adaptador isolado; falha de uma não derruba a busca |
| Página de vaga bloqueia acesso automatizado | Fallback para texto colado; nunca contornar bloqueio |
| Custo de API cresce sem controle | `chamada_llm` + alerta de teto diário + Haiku/batch na triagem |
| CV bonito que não passa no ATS | Renderização testada pelo copiar-e-colar (`ats-regras.md`, seção 6) |
| Score vira superstição | Documentar limites no output: mede aderência textual, não chance de contratação |

---

## 10. Anexo — mapeamento orientado a objetos

Modelagem do mesmo sistema em POO, útil se o agente for implementado em Java/Python OO (e diretamente aproveitável como referência de modelagem para exercícios de Programação Orientada a Objetos):

```
                    «interface» ModuloAgente
                    + executar(Contexto): Resultado
                              ▲
      ┌───────────┬───────────┼───────────┬────────────┐
 Estruturador  Gerador   Adaptador   Pontuador   Preparador
                                          │
                                    «interface» EstrategiaScore
                                     + pontuar(Perfil, Vaga): Score
                                          ▲
                              ┌───────────┴───────────┐
                        ScorePorPalavraChave    ScoreSemantico

  Pessoa
   ├─ 1..* Experiencia ──1..* Realizacao (texto, metrica, tecnologias)
   ├─ 1..* Formacao
   └─ 1..* Competencia
  Curriculo (abstrata) ◄── CurriculoBase, CurriculoAdaptado
   + renderizar(Renderizador)
  «interface» Renderizador ◄── RenderizadorDocx, RenderizadorMarkdown, RenderizadorPdf
  «interface» FonteDeVagas ◄── FonteAdzuna, FonteGreenhouse, FonteLink
  Vaga ──1..* Requisito (termo, peso, obrigatorio)
  Candidatura ──1..* EventoProcesso
```

Os pontos que o modelo ilustra bem: **herança** em `Curriculo`, **polimorfismo** em `Renderizador` e `FonteDeVagas` (adicionar uma fonte nova não altera o orquestrador), **composição** em `Pessoa`/`Experiencia`/`Realizacao`, e **baixo acoplamento** via `EstrategiaScore` — trocar o algoritmo de pontuação não toca em nenhuma outra classe.

---

## 11. Próximos passos imediatos

1. Instalar as skills e rodar a fase 0 com 3 vagas reais.
2. Preencher o `perfil.json` uma vez, com calma, respondendo às perguntas de enriquecimento — ele é o ativo que alimenta tudo.
3. Pegar `app_id`/`app_key` gratuitos da Adzuna e listar 30 empresas-alvo com seus ATS.
4. Só então decidir se vale construir o serviço (`DEPLOY.md`) ou se o uso dentro do Claude já resolve.
