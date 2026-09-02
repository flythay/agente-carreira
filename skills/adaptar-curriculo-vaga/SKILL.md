---
name: adaptar-curriculo-vaga
description: Reescreve um currículo existente para uma vaga específica — reordena experiências, reescreve o resumo profissional, alinha vocabulário técnico ao anúncio e aponta gaps — sem inventar nenhuma informação. Use sempre que o usuário colar uma descrição de vaga ou um link e pedir para "adaptar o currículo", "customizar para essa vaga", "otimizar as palavras-chave", "por que não me chamam", ou quando ele estiver aplicando para várias vagas com o mesmo documento genérico. Também use logo após o skill match-score-vaga apontar gaps que dá para fechar só com reescrita.
---

# Adaptação de currículo por vaga

Enviar o mesmo currículo para todas as vagas é o motivo mais comum de silêncio nos processos. A adaptação não é sobre escrever coisas diferentes — é sobre **fazer a informação verdadeira mais relevante subir**, usar o vocabulário que a vaga usa e assumir os gaps em vez de escondê-los.

**A regra inviolável: nunca adicionar competência, ferramenta, número, cliente, cargo ou certificação que não esteja no perfil original.** Se um requisito não tem base, ele fica como gap. Currículo que mente é descoberto na entrevista técnica, e a pessoa perde a vaga e a reputação com aquele recrutador — que costuma recrutar para várias empresas.

## Fluxo

1. **Medir antes.** Rode `match-score-vaga`. Você precisa saber o score inicial e a lista de gaps priorizados.
2. **Separar gaps em duas pilhas:**
   - *fecháveis por reescrita* — a pessoa tem a experiência, mas o currículo não diz com as palavras da vaga, ou diz enterrado no quinto bullet;
   - *reais* — a pessoa não tem. Estes vão para `plano-preparacao-vaga` e, se forem grandes, para a decisão de aplicar ou não.
3. **Adaptar** (regras abaixo), gerando um novo JSON de perfil derivado do original.
4. **Renderizar** com `curriculo-ats-harvard/scripts/render_cv.py`.
5. **Medir depois.** Rode o score novamente. Ganho típico: 5 a 15 pontos. Se não subiu, a adaptação foi cosmética — refaça olhando os gaps de maior peso.
6. **Mostrar o diff** ao usuário: o que mudou e por quê. Ele precisa reconhecer o próprio currículo, e vai precisar defender cada linha na entrevista.

## O que adaptar

**Resumo profissional — reescrever sempre.** É o campo com maior retorno. Ele deve espelhar o título da vaga e as 2–3 competências de maior peso, usando as palavras do anúncio.

Original: *"Data Scientist com 8 anos em análise preditiva e projetos de dados em diferentes setores."*
Para uma vaga sênior de fraude: *"Data Scientist com 8 anos em fraud detection e risk modeling, especializada em modelos supervisionados sobre dados transacionais de alto volume e em monitoramento de modelos em produção."*
Nada foi inventado — o foco mudou.

**Ordem das experiências.** Mantenha cronologia reversa dentro de cada bloco (quebrar isso confunde ATS e recrutador). O que se reordena são os **bullets dentro de cada cargo**: o mais relevante para a vaga vai para o topo. Se a pessoa tem trajetória em duas áreas, use blocos separados ("Experiência em Dados & Risco" antes de "Experiência em Docência") e ordene os blocos por relevância.

**Vocabulário.** Substitua descrições genéricas pelo termo literal do anúncio, quando o termo for verdadeiro:
- "processamento distribuído" → "PySpark" (só se foi PySpark mesmo)
- "modelos de árvore" → "gradient boosting (LightGBM)"
- "acompanhamento dos modelos" → "model monitoring e detecção de drift"

Se o termo do anúncio é uma sigla, escreva sigla e extenso ao menos uma vez.

**Competências técnicas.** Reordene a lista para os termos da vaga aparecerem primeiro. Remova o que é irrelevante e ocupa espaço. Não acrescente nada novo.

**Cortes.** Adaptar é tanto tirar quanto pôr. Experiências antigas e fora de escopo viram uma linha; bullets que não conversam com a vaga saem. O documento tem que continuar em 1–2 páginas.

**Idioma.** Anúncio em inglês → currículo em inglês, mesmo que a vaga seja no Brasil. É sinal de que a triagem será em inglês.

## O que fazer com os gaps reais

Nunca esconder, nunca inventar. Existem três saídas legítimas:

1. **Adjacência verdadeira** — a vaga pede Kubernetes e a pessoa fez deploy com Docker. O bullet cita Docker e a carta/entrevista faz a ponte. Não escreva "Kubernetes" no currículo.
2. **Evidência lateral** — projeto pessoal, curso concluído, disciplina lecionada. Entra em "Projetos" ou "Certificações", com a natureza clara ("projeto pessoal", "curso").
3. **Assumir na carta de apresentação** — "não tenho experiência em produção com X; tenho Y equivalente e fechei a lacuna com Z". Recrutador respeita isso e a alternativa é ser descoberto depois.

Liste os gaps para o usuário com uma recomendação por gap, e diga honestamente quando o conjunto de gaps significa que a vaga não vale a candidatura.

## Versionamento

Cada adaptação gera um arquivo derivado, nunca sobrescreve o perfil base:

```
perfil_base.json
vagas/adyen-senior-ds/vaga.json
vagas/adyen-senior-ds/perfil_adaptado.json
vagas/adyen-senior-ds/Nome_Sobrenome_CV.docx
vagas/adyen-senior-ds/score_antes.json
vagas/adyen-senior-ds/score_depois.json
vagas/adyen-senior-ds/carta.md
```

Isso resolve o problema prático de quem aplica em volume: seis meses depois, quando o recrutador liga, dá para saber exatamente qual versão do currículo aquela empresa recebeu.

## Carta de apresentação (quando pedida)

Três parágrafos: (1) por que esta empresa e esta vaga, com uma referência concreta ao que a empresa faz; (2) as duas evidências mais fortes de aderência, com número; (3) o gap principal assumido e o que já está sendo feito a respeito. Sem repetir o currículo em prosa.

## Checklist

- [ ] Nenhuma informação nova em relação ao perfil base — conferir item por item
- [ ] Resumo reescrito com o vocabulário do anúncio
- [ ] Bullets mais relevantes no topo de cada cargo
- [ ] Termos obrigatórios de peso 3 aparecendo dentro da experiência, não só na lista de skills
- [ ] Documento ainda cabe em 1–2 páginas
- [ ] Score recalculado e comparado com o inicial
- [ ] Gaps reais listados com recomendação
- [ ] Arquivo nomeado e versionado por vaga

## Depende de

- `curriculo-ats-harvard` — schema do perfil e renderização
- `match-score-vaga` — medição antes/depois e gaps priorizados
