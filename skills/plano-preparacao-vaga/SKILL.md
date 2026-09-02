---
name: plano-preparacao-vaga
description: Monta um plano de preparação para um processo seletivo específico a partir dos requisitos da vaga e dos gaps do currículo — cronograma de estudo priorizado, perguntas prováveis (técnicas e comportamentais) com respostas ancoradas na experiência real do candidato, perguntas para fazer ao entrevistador e checklist de logística. Use sempre que o usuário for entrevistado, disser "tenho entrevista na semana que vem", "como me preparo para essa vaga", "o que estudar para esse processo", "me ajuda a treinar", ou logo depois de um score de aderência apontar gaps. Também cobre simulação de entrevista com feedback.
---

# Plano de preparação para a vaga

Preparação genérica ("estude algoritmos, revise seus projetos") não muda resultado. O que muda é um plano derivado de **três coisas concretas**: os gaps reais entre o perfil e a vaga, o tempo disponível até a entrevista, e o formato do processo daquela empresa.

## Entradas

Peça o que faltar, mas comece com o que já existe:

| Entrada | Origem |
|---|---|
| `vaga.json` com requisitos e pesos | skill `coletar-vagas` ou extração manual |
| `score.json` com gaps priorizados | skill `match-score-vaga` |
| `perfil.json` | skill `curriculo-ats-harvard` |
| Data da entrevista e horas/dia disponíveis | perguntar |
| Etapa do processo e formato | perguntar: triagem com RH, técnica ao vivo, take-home, system design, painel, cultural |

Se o usuário não sabe o formato, vale pesquisar o processo daquela empresa — muitas publicam as etapas na própria página de carreiras, e ex-candidatos descrevem em fóruns. Formato errado gera preparação errada: quem estuda system design para uma entrevista de case de negócio perde as duas.

## Passo 1 — classificar os gaps

Cada gap cai em uma de três categorias, e o tratamento é diferente:

- **Fechável no tempo disponível** (ex.: sintaxe de uma ferramenta, um conceito, um comando). Vale estudo direcionado. Regra prática: se dá para atingir "sei explicar e sei fazer um exemplo pequeno" no tempo que existe, é fechável.
- **Contornável com narrativa** — a pessoa tem experiência adjacente. Não se estuda, se ensaia a ponte: "não usei Kubernetes em produção; empacotei serviços com Docker e a orquestração era feita pelo time de plataforma — aqui está o que eu sei da parte que me tocava".
- **Não fechável** — anos de experiência num domínio, idioma, certificação obrigatória. Aqui a única jogada honesta é decidir: aplicar assumindo, ou não aplicar. Diga isso claramente.

Não gaste tempo do plano com o que já está forte. O erro mais comum é estudar o que se gosta em vez do que decide.

## Passo 2 — cronograma

Use o script para transformar gaps + prazo em blocos:

```bash
python scripts/gerar_plano.py score.json --data-entrevista 2026-09-15 --horas-dia 2 --saida plano.md
```

Ele aloca as horas por peso do requisito, reserva o dia anterior para revisão (não para conteúdo novo) e deixa espaço fixo para ensaio de respostas. Ajuste o resultado à realidade da pessoa em vez de entregar o output cru.

Princípios que o plano respeita:
- **Profundidade sobre cobertura.** Três requisitos bem preparados batem oito superficiais; o entrevistador aprofunda no que você citar.
- **Prática sobre leitura.** Para gap técnico, o alvo é escrever código/consulta pequena que funcione, não ler documentação.
- **Ensaio em voz alta.** Resposta pensada e resposta falada são coisas diferentes; a segunda precisa de repetição.
- **Véspera é revisão e sono.** Conteúdo novo na véspera aumenta ansiedade e não fixa.

## Passo 3 — banco de perguntas e respostas ancoradas

Gere 8 a 12 perguntas prováveis: técnicas derivadas dos requisitos de maior peso, comportamentais derivadas das responsabilidades do anúncio, e uma ou duas sobre cada gap (o entrevistador vai perguntar justamente onde o currículo é fino).

Para cada pergunta, monte a resposta a partir de **experiências reais que estão no perfil** — nunca uma resposta genérica de blog. Estrutura:

> **Contexto** (1 frase: onde, quando, qual era o problema)
> **O que eu fiz** (2–3 frases: a decisão técnica e por que ela, não a lista de tudo)
> **Como medi** (a métrica, o baseline comparado)
> **Resultado e o que mudou depois** (o número e a decisão que ele destravou)

Isso é o STAR sem o vício do STAR — que é virar lista longa e perder o entrevistador no meio. Duas regras de ritmo: **60 a 90 segundos por resposta**, e nunca enumerar mais de três itens seguidos em voz alta. Se a resposta pede uma lista de sete coisas, diga as duas mais importantes e ofereça o resto ("posso detalhar os outros se for útil").

Prepare também as três perguntas difíceis que quase sempre aparecem e quase nunca são ensaiadas: por que saiu do último emprego, o buraco no histórico, e a pretensão salarial.

## Passo 4 — o que perguntar ao entrevistador

Cinco perguntas, específicas daquela empresa e daquela função. Perguntas boas revelam preparo e coletam informação de decisão:
- como o sucesso nesta função é medido nos primeiros 6 meses;
- quem consome o que a pessoa produz e como a decisão é tomada quando há discordância;
- como está a dívida técnica / maturidade da área hoje;
- por que a vaga está aberta (crescimento ou reposição);
- próximos passos e prazo.

Evite perguntas cuja resposta está no site da empresa.

## Passo 5 — logística e riscos

Checklist antes da entrevista:
- fuso horário confirmado e convertido (erro clássico em processo internacional);
- link, câmera, microfone e plano B testados;
- faixa salarial pesquisada para **aquele país e aquele nível**, com número de partida e piso definidos antes da conversa;
- status de visto/relocação e prazo de disponibilidade prontos em uma frase;
- para take-home: prazo, escopo combinado e limite de tempo que você vai respeitar.

## Simulação de entrevista

Quando o usuário pedir para treinar, conduza uma pergunta por vez. Depois de cada resposta: um feedback curto (um ponto forte concreto, um ajuste específico), a versão melhorada de uma frase da resposta dele, e a próxima pergunta. Sem despejar tudo no fim.

Calibre a dificuldade pela senioridade da vaga e faça a simulação **no idioma do processo** — treinar em português para uma entrevista em inglês não prepara para a parte mais difícil, que é achar a palavra sob pressão.

No fechamento, entregue: as duas respostas mais fortes, as duas mais fracas com o que mudar, e o que praticar antes da próxima rodada.

## Depois da entrevista

Registre enquanto está fresco: perguntas que apareceram, o que travou, o que o entrevistador enfatizou. Isso alimenta a próxima preparação e revela padrões de reprovação que ninguém enxerga candidatura a candidatura.

## Arquivos deste skill

- `scripts/gerar_plano.py` — cronograma priorizado a partir do `score.json` e da data da entrevista
