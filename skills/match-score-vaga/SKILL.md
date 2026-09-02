---
name: match-score-vaga
description: Calcula um score de aderência (0–100) entre um currículo e uma vaga, com evidência requisito por requisito, gaps priorizados e critérios eliminatórios. Use sempre que o usuário perguntar se vale a pena aplicar, "qual meu match com essa vaga", "meu currículo bate com isso?", quiser comparar várias vagas para decidir onde investir tempo, ou colar uma descrição de vaga junto com o currículo. Também é a etapa de medição antes e depois de adaptar um currículo — rode antes para achar os gaps e depois para provar que a adaptação funcionou.
---

# Score de aderência currículo × vaga

O número por si só não vale nada; o que vale é **onde** a aderência quebra. Este skill produz um score explicável: cada requisito da vaga recebe um status com a evidência exata que o justifica, e os gaps saem ordenados por peso — que é exatamente a entrada dos skills `adaptar-curriculo-vaga` e `plano-preparacao-vaga`.

O cálculo é determinístico e roda em Python (sem chamada de LLM, sem dependência externa). O trabalho do modelo é só a etapa de extração: transformar o anúncio em requisitos estruturados. Isso importa porque um score gerado "no olho" por um LLM não é reproduzível — pede duas vezes, dá dois números.

## Fluxo

1. **Extrair a vaga** para JSON (formato em `references/formato-vaga.md`). Se a vaga veio de link ou de busca, use o skill `coletar-vagas` — ele já devolve nesse formato.
2. **Rodar o cálculo**:
   ```bash
   python scripts/match_score.py perfil.json vaga.json
   python scripts/match_score.py perfil.json vaga.json --json --saida score.json
   ```
3. **Interpretar** com o usuário, sempre nesta ordem: eliminatórios → gaps de maior peso → o que já está forte.

## Como extrair requisitos (a parte que exige julgamento)

Anúncio não vem organizado. Ao converter, decida três coisas:

**Obrigatório × desejável.** Sinais de obrigatório: "required", "must have", "obrigatório", aparece no título da vaga, ou é repetido em seções diferentes. Sinais de desejável: "nice to have", "plus", "differential", "bonus", "familiarity with". Na dúvida entre os dois, classifique como obrigatório com peso menor — errar para o lado conservador evita otimismo falso.

**Peso (1 a 3).** 3 = está no título ou é o núcleo da função ("fraud detection" numa vaga de fraude). 2 = requisito técnico citado com ênfase. 1 = ferramenta periférica, mencionada de passagem. Peso não é dificuldade, é **quanto aquilo decide a contratação**.

**Granularidade.** Quebre requisitos compostos: "experiência com Python, Spark e Airflow em ambiente cloud" vira quatro termos. Um requisito composto casa parcialmente e distorce o score.

Registre também `anos_minimos`, `senioridade` e os **eliminatórios** (visto, idioma, localização, formação obrigatória). Eliminatório nunca zera o score em silêncio: ele aparece como alerta separado, porque a decisão de aplicar mesmo assim é do usuário — muita gente é contratada com um eliminatório em aberto quando o resto é forte.

## Como o score é composto

| Componente | Peso | O que mede |
|---|---|---|
| Cobertura de obrigatórios | 55% | soma ponderada dos requisitos obrigatórios cobertos |
| Cobertura de desejáveis | 15% | idem, para os "nice to have" |
| Similaridade lexical | 15% | cosseno sobre tf (uni + bigramas) entre o texto do CV e o do anúncio — proxy do que um ATS de palavra-chave vê |
| Senioridade | 15% | anos de experiência calculados (intervalos unidos, sem dupla contagem) ÷ anos exigidos, teto em 100% |

Componentes sem dado na vaga são descartados e os pesos renormalizados — uma vaga sem `anos_minimos` não é penalizada.

Cada requisito recebe um de três status, e essa distinção é o coração do método:

- **demonstrado** — o termo aparece na experiência, num projeto ou na formação. Vale 100% do peso.
- **declarado** — aparece só na lista de competências ou numa certificação. Vale 60%. É a diferença entre "sei SQL" e "usei SQL para resolver X e o resultado foi Y". Recrutador desconta exatamente isso.
- **ausente** — vale 0.

O casamento usa três camadas: literal (com normalização de acento/caixa), sinônimos (`assets/sinonimos.json`, editável — "LightGBM" casa com "gradient boosting", "monitoramento em produção" com "model monitoring") e aproximado por similaridade de string ≥ 0,90 para erros de digitação. Se o usuário trabalha num nicho que o dicionário não cobre, adicione os grupos ali em vez de forçar o texto do currículo.

A similaridade lexical é calibrada por um teto de 0,35 de cosseno bruto — currículo e anúncio têm vocabulário e tamanho muito diferentes, e sem calibração esse componente puxaria todos os scores para baixo igualmente, virando ruído. O valor bruto continua no JSON de saída para inspeção.

## Faixas

| Score | Leitura |
|---|---|
| 80–100 | Forte. Aplicar e priorizar; vale escrever carta de apresentação. |
| 65–79 | Boa. Aplicar com currículo adaptado — a adaptação costuma valer 5 a 15 pontos. |
| 50–64 | Média. Aplicar só se a vaga interessa de verdade; endereçar os gaps explicitamente. |
| < 50 | Baixa. Provavelmente não passa da triagem. Vale mais investir o tempo em outra vaga ou fechar o gap primeiro. |

Diga isso ao usuário sem suavizar. Uma pessoa aplicando para dezenas de vagas por semana precisa de um filtro honesto, não de encorajamento — o custo de uma candidatura mal escolhida é o tempo que não foi para a vaga certa.

## Limites que você deve declarar

O score mede **aderência textual do currículo à descrição**, não probabilidade de contratação. Ele não enxerga: reputação da empresa, indicação interna, quantidade de candidatos, orçamento da vaga, nem se o anúncio já tem candidato escolhido. Um score 85 numa vaga com 900 candidatos vale menos que um 65 com indicação. Quando o usuário tratar o número como previsão, corrija.

Também não meça duas vagas de senioridades diferentes e conclua que uma é "melhor": compare vagas comparáveis.

## Uso em lote

Para triagem de muitas vagas (o caso de quem aplica em volume), rode o script sobre um diretório de vagas e ordene por score. Isso transforma "aplicar em 50 vagas por dia" em "aplicar em 12 vagas com score ≥ 65 e currículo adaptado", que converte muito melhor:

```bash
for v in vagas/*.json; do
  python scripts/match_score.py perfil.json "$v" --json --saida "scores/$(basename "$v")"
done
```

## Arquivos deste skill

- `scripts/match_score.py` — cálculo, relatório em texto e saída JSON
- `assets/sinonimos.json` — grupos de sinônimos técnicos PT/EN (editar conforme o nicho)
- `references/formato-vaga.md` — schema de `vaga.json` e como classificar requisitos
