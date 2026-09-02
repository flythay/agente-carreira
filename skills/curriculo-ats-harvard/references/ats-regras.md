# Regras de ATS

Um ATS (Applicant Tracking System — Workday, Greenhouse, Lever, Taleo, SmartRecruiters, Gupy) faz três coisas com o currículo: **extrai texto**, **mapeia campos** (nome, empresas, datas, formação) e **pontua contra a vaga** (correspondência de termos, filtros obrigatórios). Cada uma falha por um motivo diferente.

## 1. Extração de texto — o que quebra

| Elemento | Efeito |
|---|---|
| Tabelas | Parser lê célula por célula e embaralha a ordem; datas descolam dos cargos |
| Duas colunas / barra lateral | Texto sai intercalado e ilegível |
| Caixas de texto (text box) | Frequentemente ignoradas — a seção some |
| Cabeçalho/rodapé (header/footer) | Vários parsers descartam; contato no rodapé = candidato sem e-mail |
| Ícones e imagens (inclusive ícone de e-mail) | Não viram texto |
| Colunas de tecnologia com barras de progresso | Vira ruído ou nada |
| Fonte não padrão incorporada | Pode gerar caracteres corrompidos |
| PDF gerado por imagem/scan | Extração falha inteira (sem OCR, o CV é vazio) |

O que é seguro: coluna única, parágrafos, listas com marcador real, negrito e itálico, fontes padrão (Calibri, Arial, Helvetica, Georgia, Times), tamanho 10–12, margens 1,5–2,5 cm.

## 2. Mapeamento de campos

- Use **títulos de seção convencionais**: "Experiência profissional" / "Professional Experience", "Formação acadêmica" / "Education", "Competências" / "Skills". Títulos criativos ("Minha jornada", "O que me move") não são reconhecidos e a seção inteira pode não ser mapeada.
- Um cargo por bloco, com empresa e datas na mesma vizinhança do título.
- Datas completas com mês: `03/2021 – 08/2024`. Só o ano faz alguns sistemas calcularem tempo de experiência errado.
- Nunca escreva o nome da empresa e o cargo na mesma linha separados por caractere exótico (`❯`, `▸`).

## 3. Pontuação por palavra-chave

O ATS compara o texto do currículo com o texto da vaga. Ele faz correspondência quase literal — sinônimo humano não é sinônimo para ele.

Regras:
- Se a vaga diz "PySpark", escreva "PySpark", não "processamento distribuído em Spark".
- Se a vaga usa sigla e por extenso ("NLP (Natural Language Processing)"), use as duas formas ao menos uma vez.
- Coloque os termos **dentro dos bullets de experiência**, não só numa lista de skills. Vários sistemas ponderam mais o que aparece na experiência, e o recrutador humano definitivamente pondera.
- Frequência não é ranking: repetir "Python" oito vezes não melhora a nota e piora a leitura humana.
- **Nunca** use texto branco, palavras-chave escondidas atrás de imagem ou keyword stuffing invisível. Isso é detectado, e quando é detectado o candidato é bloqueado — não só rejeitado.

Cobertura alvo: **75%+ dos requisitos obrigatórios** aparecendo literalmente no documento, desde que verdadeiros. Meça isso com o skill `match-score-vaga`.

## 4. Formato de arquivo

- **DOCX** é o mais seguro para ATS antigos (Taleo, alguns Workday).
- **PDF gerado a partir de texto** é seguro na maioria dos sistemas modernos e preserva o layout para o leitor humano.
- Regra prática: se o formulário aceita os dois, envie PDF; se o sistema é desconhecido ou o campo pede "upload resume" com parsing automático que preenche o formulário, envie DOCX.
- Nunca envie: PDF escaneado, imagem, Pages, ODT, link para Google Docs, ou arquivo protegido por senha.
- Nome do arquivo: `Nome_Sobrenome_Cargo_CV.pdf`.

## 5. Filtros eliminatórios (knockout)

Antes da pontuação, muitos sistemas aplicam filtros binários. Se a resposta não estiver clara no currículo ou no formulário, o candidato cai fora sem ninguém ler:

- autorização de trabalho / visto no país da vaga
- anos mínimos de experiência
- formação obrigatória
- idioma mínimo
- localização ou disponibilidade para trabalho presencial/híbrido

Trate isso explicitamente no documento quando for a favor do candidato (ex.: `Inglês C2`, `Disponível para relocação`) e sinalize ao usuário quando for contra — ele precisa decidir se aplica mesmo assim.

## 6. Teste rápido antes de enviar

1. Abra o PDF/DOCX, selecione tudo, copie e cole num editor de texto puro. Se a ordem sair embaralhada ou faltar seção, o parser vai errar igual.
2. Confira se nome, e-mail e telefone aparecem na primeira linha do texto colado.
3. Verifique se as datas ficaram junto dos cargos correspondentes.
