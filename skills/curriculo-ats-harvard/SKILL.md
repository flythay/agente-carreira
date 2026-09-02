---
name: curriculo-ats-harvard
description: Constrói ou reescreve um currículo profissional no formato Harvard e otimizado para ATS, a partir de conversa em linguagem natural (PT ou EN), entrevistando o usuário para preencher lacunas e quantificar resultados antes de gerar o arquivo. Use sempre que o usuário falar em currículo, CV, resume, "melhorar meu currículo", "meu currículo não passa nos filtros", ATS, palavras-chave de currículo, ou quando ele contar a trajetória profissional dele e pedir para transformar isso num documento — inclusive quando ele já colar um currículo antigo pedindo revisão.
---

# Currículo ATS + formato Harvard

Um currículo tem dois leitores: um parser automático (ATS) que decide se ele chega até um humano, e um recrutador que decide em 20 segundos se vale a entrevista. O formato Harvard resolve o segundo (bullets orientados a resultado, ordem reversa, uma página densa); as regras de ATS resolvem o primeiro (layout linear, sem tabelas, palavras-chave literais). Este skill produz um documento que atende aos dois ao mesmo tempo.

A regra que não se quebra: **nunca inventar experiência, ferramenta, número ou certificação.** Se falta informação, pergunte. Um currículo com um número inventado destrói a credibilidade na entrevista, e é exatamente ali que a pessoa perde a vaga.

## Fluxo

1. **Coletar** — receba o relato livre, o currículo antigo (PDF/DOCX) ou os dois.
2. **Estruturar** — converta para o JSON de perfil (`assets/perfil.schema.json`). Campos sem informação ficam vazios, nunca preenchidos por dedução.
3. **Entrevistar as lacunas** — veja "Entrevista de enriquecimento" abaixo. Esta é a etapa que gera valor real; pular ela produz um currículo genérico.
4. **Escrever** — aplique `references/formato-harvard.md` e `references/ats-regras.md`.
5. **Renderizar** — `scripts/render_cv.py` gera Markdown + DOCX com layout ATS-safe. Não desenhe o layout manualmente e não peça ao modelo para "produzir o PDF".
6. **Revisar** — rode o checklist final com o usuário.

## Entrevista de enriquecimento

Antes de perguntar qualquer coisa, escreva um rascunho mental do currículo e localize onde ele fica fraco. Perguntas boas nascem de uma lacuna concreta, não de um formulário.

Priorize nesta ordem:

1. **Resultado sem número** — "reduzi fraude" precisa virar "reduzi chargeback de 1,8% para 0,7% em 6 meses".
2. **Escala ausente** — volume de dados, tamanho do time, número de clientes, valor transacionado, quantidade de modelos em produção.
3. **Ambiguidade de papel** — a pessoa liderou, participou ou executou sozinha? Recrutador pergunta isso na entrevista.
4. **Datas e lacunas de tempo** — buracos no histórico precisam de explicação (estudo, sabática, freelance) mesmo que não entrem no documento.
5. **Stack literal** — a vaga vai buscar "PySpark", não "processamento distribuído".

Formato das perguntas: **no máximo 4 por vez**, numeradas, cada uma com uma opção de resposta aproximada para destravar quem não lembra. Exemplo:

> 3. No projeto de detecção de fraude no e-commerce, qual era o volume aproximado de transações avaliadas por dia?
>    (chute uma ordem de grandeza: ~10 mil / ~100 mil / ~1 milhão)

Quando o usuário disser "não lembro", use a **escada de quantificação** em vez de desistir:
- ordem de grandeza ("dezenas de milhares por dia") — sempre melhor que nada;
- antes/depois relativo ("caiu cerca de um terço");
- proxy verificável ("cobria os 4 maiores clientes da carteira");
- se nada disso existir, reescreva o bullet em torno da **decisão técnica e do escopo**, não do impacto. Bullet sem número é aceitável; bullet com número falso, não.

Pergunte também, uma vez só, o que muda tudo no resto do documento:
- **Mercado-alvo** (Brasil, EU, UK, US, remoto internacional) — muda foto, dados pessoais, formato de data, ortografia e até o nome do documento.
- **Idioma de saída** — independente do idioma em que a pessoa falou com você.
- **Cargo-alvo em uma linha** — sem isso não existe resumo profissional decente.

## Escrita das seções

Ordem padrão (ajuste em `references/formato-harvard.md` conforme senioridade):

```
Nome
Contato (cidade/país | e-mail | telefone | LinkedIn | GitHub)
Resumo profissional
Experiência profissional
Formação acadêmica
Competências técnicas
Idiomas
Certificações / Publicações (se houver)
```

**Resumo profissional** — 2 a 3 linhas. Fórmula: `[cargo-alvo] com [X anos] em [domínio], especializado em [2-3 competências que a vaga busca], com histórico de [resultado mais forte quantificado]`. Sem adjetivos de autoelogio ("proativo", "apaixonado por dados").

**Bullets de experiência** — fórmula Harvard: **verbo de ação forte + o que foi feito + como foi medido + com qual meio/tecnologia**. 3 a 5 bullets por cargo recente, 1 a 2 para cargos antigos. Comece pelo resultado quando ele for forte.

Exemplo de reescrita:

Antes: *"Responsável por modelos de machine learning para detecção de fraude usando Python."*
Depois: *"Desenvolvi e coloquei em produção modelo de detecção de fraude em LightGBM sobre ~800 mil transações/dia, elevando o recall de 0,62 para 0,81 sem aumento de falso positivo (AUC 0,94)."*

O que mudou: verbo forte, escala, métrica antes/depois, restrição respeitada, ferramenta literal.

**Competências técnicas** — agrupe por categoria (Linguagens, ML, Dados/Cloud, Ferramentas) e escreva os termos como a vaga escreve. Nada de barras de proficiência ou estrelinhas: o parser não lê e o recrutador não acredita.

## Renderização

```bash
python scripts/render_cv.py perfil.json --idioma pt --saida ./out --nome-arquivo "Nome_Sobrenome_CV"
```

Gera `.md` (para revisão e diff) e `.docx` (entrega). O DOCX sai em coluna única, sem tabelas, sem caixas de texto, sem cabeçalho/rodapé — as três coisas que mais quebram parser de ATS. Se o usuário pedir PDF, gere a partir do DOCX (LibreOffice/Word), nunca redesenhando o conteúdo.

Nome do arquivo importa: `Thayse_Oliveira_Data_Scientist_CV.pdf` é encontrável na caixa do recrutador; `curriculo_final_v3.pdf` não é.

## Iteração

Depois de entregar, ofereça edições cirúrgicas em vez de regerar tudo: "deixar o resumo mais curto", "tirar a experiência de 2015", "puxar o projeto X para o topo". Mantenha o JSON do perfil como fonte da verdade e regere o documento a partir dele — assim as versões por vaga (ver skill `adaptar-curriculo-vaga`) nunca divergem do original.

## Checklist final

- [ ] Cabe em 1 página (até ~8 anos de carreira) ou 2 (acima disso); nunca 1,5
- [ ] Todo bullet começa com verbo de ação; nenhum começa com "Responsável por"
- [ ] Pelo menos 60% dos bullets têm número, escala ou métrica
- [ ] Nenhuma informação que o usuário não confirmou
- [ ] Datas no padrão do mercado-alvo, sem buracos inexplicados
- [ ] Sem foto, idade, estado civil ou CPF quando o alvo é EU/UK/US
- [ ] Termos técnicos escritos como o mercado escreve (verificar contra 2-3 vagas reais)
- [ ] Arquivo nomeado com nome + cargo
- [ ] DOCX abre e o texto é selecionável na ordem correta de leitura

## Arquivos deste skill

- `references/formato-harvard.md` — estrutura, ordem das seções, fórmula de bullet, variações por senioridade e por mercado
- `references/ats-regras.md` — o que quebra parser, palavras-chave, formatos de arquivo
- `references/perguntas-enriquecimento.md` — banco de perguntas por tipo de lacuna e por área
- `assets/perfil.schema.json` — schema do perfil estruturado (contrato com os outros skills)
- `scripts/render_cv.py` — Markdown + DOCX a partir do JSON
