# Formato Harvard — estrutura e regras de escrita

O "modelo Harvard" (usado pelos escritórios de carreira de Harvard e adotado como padrão de facto em processos internacionais) é essencialmente: documento em coluna única, ordem cronológica reversa, sem elementos gráficos, e bullets que descrevem **impacto medido**, não atribuições de cargo.

## Ordem das seções

| Perfil | Ordem recomendada |
|---|---|
| Profissional com 3+ anos | Contato → Resumo → Experiência → Formação → Competências → Idiomas → Certificações |
| Recém-formado / troca de área | Contato → Resumo → Formação → Projetos → Experiência → Competências → Idiomas |
| Acadêmico / pesquisa | Contato → Resumo → Formação → Publicações → Experiência → Competências |
| Docente + indústria (perfil híbrido) | Contato → Resumo → Experiência (indústria) → Experiência (docência) → Formação → Competências |

Regra geral: o que sustenta a candidatura vai antes. Se a formação é o ativo mais forte, ela sobe; se é a experiência, ela sobe.

## Cabeçalho

```
NOME COMPLETO
Cidade, País · e-mail · +55 41 XXXXX-XXXX · linkedin.com/in/usuario · github.com/usuario
```

- Uma linha só de contato, separadores simples (`·` ou `|`).
- Nada de foto, data de nascimento, estado civil, nacionalidade, CPF/RG quando o alvo é EU/UK/US/Canadá — em vários desses mercados isso cria risco de viés e alguns recrutadores descartam o documento.
- Brasil aceita foto, mas ela não ajuda em processo com triagem automática. Padrão: sem foto.
- Se o alvo é outro país, informe explicitamente a disponibilidade: `Open to relocation — EU work authorization: [status]`. Recrutador europeu descarta candidato de fora quando a autorização não está clara.

## Resumo profissional

2–3 linhas, sem primeira pessoa, sem adjetivo de autoelogio.

Fórmula:
```
[Cargo-alvo] com [N] anos em [domínio], especializado em [competência 1], [competência 2] e [competência 3].
Histórico de [resultado quantificado mais forte]. [Diferencial: formação, idioma, setor].
```

Bom: *"Data Scientist com 8 anos em detecção de fraude e risco de crédito, especializado em modelos supervisionados, feature engineering transacional e monitoramento em produção. Reduziu perda por fraude em 34% em carteira de e-commerce mantendo taxa de aprovação estável."*

Ruim: *"Profissional apaixonado por dados, proativo, com facilidade de trabalhar em equipe e vontade de aprender."*

## Bullets de experiência

Estrutura de cada cargo:

```
Cargo — Empresa
Cidade, País | MM/AAAA – MM/AAAA
• bullet
• bullet
```

A fórmula de bullet: **verbo de ação + entrega + medida + meio**.

Verbos que funcionam (evite repetir o mesmo dois bullets seguidos):
- Construção: desenvolvi, implementei, projetei, automatizei, migrei, integrei
- Análise: identifiquei, diagnostiquei, modelei, validei, mensurei
- Liderança: liderei, coordenei, mentorei, priorizei, negociei
- Resultado: reduzi, aumentei, acelerei, eliminei, recuperei

Evite: "responsável por", "atuei em", "participei de", "auxiliei", "ajudei", "trabalhei com".

Quantificação — nem tudo é R$ ou %. Também contam:
- volume (transações/dia, registros, usuários, GB)
- tempo (de 4h para 20min, entrega em 6 semanas)
- escopo (3 países, 12 clientes, 5 pessoas no time)
- métrica técnica (AUC, recall, precisão, latência p95, uptime)
- frequência (relatório diário → tempo real)

Quantidade: 3–5 bullets no cargo atual, 2–4 no anterior, 1–2 nos mais antigos. Cargos com mais de 10–12 anos podem virar uma linha só em "Experiência anterior".

## Formação

```
Mestrado em [curso] — [Instituição], Cidade, País | Conclusão: AAAA
Dissertação: [título] (só se relevante para a vaga)
```

Não inclua nota/CR salvo quando excelente e quando o mercado-alvo valoriza (UK e alguns programas alemães perguntam). Não inclua ensino médio se há graduação.

## Competências técnicas

Agrupadas, em texto corrido separado por vírgula. Sem gráficos, sem "nível: avançado" arbitrário.

```
Linguagens: Python, SQL, R, C/C++, Java
ML/Estatística: scikit-learn, LightGBM, XGBoost, séries temporais, testes A/B
Dados & Cloud: Spark, Databricks, Azure, Airflow, Docker
```

Se afirmar um nível, torne verificável: `Inglês — C2 (certificado)`, `Alemão — B1 (Goethe)`.

## Variações por mercado

| Mercado | Particularidades |
|---|---|
| Brasil | 1–2 páginas, PT-BR, foto opcional (prefira sem), pode citar CLT/PJ |
| EUA / Canadá | 1 página até ~10 anos, "resume", sem foto, sem dados pessoais, ortografia americana |
| Reino Unido | "CV", até 2 páginas, ortografia britânica, seção de referências geralmente omitida ("available on request" é desnecessário) |
| Alemanha | "Lebenslauf", tolera 2 páginas e formato mais estruturado; empresas internacionais em tech aceitam o padrão anglo — mantenha sem foto se aplicar via ATS |
| Holanda | Padrão anglo, 1–2 páginas, inglês; explicite status de visto/relocação |

Datas: `MM/AAAA` no Brasil; `Mon YYYY` (`Mar 2023 – Present`) no mercado anglo. Não misture.

## Erros que mais aparecem

1. Documento em duas colunas com barra lateral — bonito, ilegível para parser.
2. Bullets que descrevem a descrição de cargo, não o que a pessoa fez.
3. Resumo genérico reaproveitado para qualquer vaga.
4. Lista de tecnologias que a pessoa não sabe defender em entrevista.
5. Mesmo currículo, sem adaptação, para 50 vagas — o motivo mais comum de não ter resposta.
