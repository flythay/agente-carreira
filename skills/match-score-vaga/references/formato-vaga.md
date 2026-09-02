# Formato de `vaga.json`

Contrato compartilhado entre `coletar-vagas`, `match-score-vaga`, `adaptar-curriculo-vaga` e `plano-preparacao-vaga`. Só o LLM preenche este arquivo; os scripts apenas consomem.

```json
{
  "id": "hash estável: sha1(empresa|titulo|local)",
  "titulo": "Senior Data Scientist — Fraud & Risk",
  "empresa": "Adyen",
  "local": "Amsterdam, Netherlands",
  "modalidade": "hibrido",
  "idioma_anuncio": "en",
  "senioridade": "senior",
  "anos_minimos": 5,
  "faixa_salarial": "€75.000 – €95.000/ano",
  "url": "https://...",
  "fonte": "greenhouse",
  "data_publicacao": "2026-08-28",
  "prazo": "",
  "requisitos_obrigatorios": [
    { "termo": "Python", "peso": 3, "tipo": "tecnico" },
    { "termo": "fraud detection", "peso": 3, "tipo": "dominio" },
    { "termo": "stakeholder management", "peso": 1, "tipo": "comportamental" }
  ],
  "requisitos_desejaveis": [
    { "termo": "PySpark", "peso": 1, "tipo": "tecnico" }
  ],
  "eliminatorios": [
    {
      "criterio": "Autorização de trabalho na União Europeia",
      "tipo": "visto",
      "termos_evidencia": ["EU work authorization", "autorização de trabalho", "EU Blue Card"]
    }
  ],
  "responsabilidades": ["texto de cada bullet de responsabilidade"],
  "sobre_empresa": "2–4 frases, se o anúncio trouxer",
  "beneficios": ["relocation package", "30 dias de férias"],
  "texto_completo": "descrição integral em texto puro",
  "capturado_em": "2026-09-02"
}
```

## Campos que mais importam

- **`texto_completo`** — alimenta a similaridade lexical e a preparação de entrevista. Sem ele, o score perde um componente. Guarde o texto puro, sem HTML.
- **`peso`** — 1 a 3, calibrado por quanto o requisito decide a contratação (não por dificuldade). Se está no título da vaga, é 3.
- **`tipo`** — `tecnico`, `dominio`, `comportamental`, `formacao`, `idioma`, `certificacao`. Usado para agrupar o plano de preparação.
- **`termos_evidencia`** nos eliminatórios — lista de strings que, se aparecerem no perfil, marcam o critério como atendido. Sem essa lista o script devolve "confirmar com o candidato", que é o comportamento correto quando não há como verificar automaticamente.

## Classificação de requisitos — regras práticas

| Sinal no anúncio | Classificação |
|---|---|
| "required", "must have", "obrigatório", "you have X years of" | obrigatório |
| aparece no título da vaga | obrigatório, peso 3 |
| "nice to have", "plus", "bonus", "differential", "familiarity with" | desejável |
| "we'd love if", "ideally" | desejável, peso 1 |
| citado duas vezes em seções diferentes | obrigatório, sobe um peso |
| requisito legal/administrativo (visto, registro profissional, disponibilidade presencial) | eliminatório, não requisito |

Quebre requisitos compostos em termos atômicos. `"Python, Spark e Airflow em cloud"` → `Python`, `Spark`, `Airflow`, `cloud`. Requisito composto casa parcialmente e distorce o resultado.

Ignore texto institucional ("somos uma empresa que valoriza diversidade") — não vira requisito. Mas guarde em `sobre_empresa` o que ajuda na entrevista.

## Sobre soft skills

Requisitos comportamentais ("comunicação com stakeholders", "trabalho em ambiente ambíguo") entram com peso 1 e tipo `comportamental`. Eles quase nunca casam por palavra-chave — e é correto que apareçam como gap, porque o lugar de resolvê-los não é o currículo, é a preparação de entrevista com uma história STAR pronta.
