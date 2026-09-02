#!/usr/bin/env python3
"""
Score de aderencia entre um perfil (curriculo) e uma vaga.

Deterministico e explicavel: o LLM extrai os requisitos da vaga para JSON,
este script calcula o numero e mostra a evidencia de cada requisito. Sem
dependencias externas (so stdlib), para rodar em qualquer servidor.

Uso:
    python match_score.py perfil.json vaga.json
    python match_score.py perfil.json vaga.json --json          # saida so JSON
    python match_score.py perfil.json vaga.json --sinonimos meu_dic.json

Formato de vaga.json: ver referencia em references/formato-vaga.md
"""

import argparse
import json
import math
import re
import sys
import unicodedata
from collections import Counter
from datetime import date
from pathlib import Path

# --------------------------------------------------------------------------
# Normalizacao
# --------------------------------------------------------------------------

STOPWORDS = set("""
a o os as um uma uns umas de do da dos das em no na nos nas por para com sem
sob sobre entre e ou que se ao aos à às como mais menos muito muita ser estar
ter haver foi era sao são será seu sua seus suas este esta isso aquele nosso
the a an and or of in on for to with without at by from as is are was were be
been being this that these those we you they it our your their will would can
could should has have had do does did not no nor but if then than there here
experiencia experience conhecimento knowledge trabalhar work working
""".split())

# Termos que nunca devem ser normalizados a ponto de colidir
ALIAS_BASE = {
    "js": "javascript",
    "py": "python",
    "postgres": "postgresql",
    "k8s": "kubernetes",
    "ml": "machine learning",
    "dl": "deep learning",
    "nlp": "natural language processing",
    "pln": "natural language processing",
    "gcp": "google cloud",
    "aws": "amazon web services",
    "ci/cd": "cicd",
    "ci cd": "cicd",
    "power bi": "powerbi",
    "sql server": "sqlserver",
    "scikit learn": "scikitlearn",
    "sklearn": "scikitlearn",
    "tensor flow": "tensorflow",
    "a/b": "ab",
}


def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def normalizar(texto):
    t = sem_acento((texto or "").lower())
    t = t.replace("+", "plus").replace("#", "sharp")
    t = re.sub(r"[^\w\s/.-]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    for k, v in ALIAS_BASE.items():
        t = re.sub(rf"(?<![\w]){re.escape(k)}(?![\w])", v, t)
    return t


def tokens(texto, remover_stop=True):
    t = normalizar(texto)
    brutos = re.findall(r"[a-z0-9][a-z0-9.+#-]*", t)
    if remover_stop:
        brutos = [b for b in brutos if b not in STOPWORDS and len(b) > 1]
    return brutos


def bigramas(toks):
    return [f"{a}_{b}" for a, b in zip(toks, toks[1:])]


def similaridade_fuzzy(a, b):
    """Razao de similaridade 0..1 (SequenceMatcher da stdlib)."""
    from difflib import SequenceMatcher
    return SequenceMatcher(None, a, b).ratio()


# --------------------------------------------------------------------------
# Extracao de evidencias do perfil
# --------------------------------------------------------------------------

def coletar_evidencias(perfil):
    """Retorna lista de (texto, origem, peso_evidencia).

    Peso: 1.0 = experiencia (o que o candidato de fato fez);
          0.6 = lista de competencias/certificacao (declarado, nao demonstrado).
    """
    ev = []
    dp = perfil.get("dados_pessoais", {}) or {}
    cab = " ".join(str(dp.get(k, "")) for k in
                   ("titulo_profissional", "cidade", "pais",
                    "autorizacao_trabalho", "disponibilidade"))
    if cab.strip():
        ev.append((cab, "dados pessoais", 0.8))
    if perfil.get("resumo"):
        ev.append((perfil["resumo"], "resumo", 0.8))
    for exp in perfil.get("experiencias", []):
        cabec = f"{exp.get('cargo','')} {exp.get('empresa','')} {exp.get('setor','')}"
        ev.append((cabec, f"cargo: {exp.get('cargo','')}", 0.9))
        if exp.get("contexto"):
            ev.append((exp["contexto"], f"contexto: {exp.get('empresa','')}", 0.7))
        for b in exp.get("bullets", []):
            txt = b.get("texto", "")
            tec = " ".join(b.get("tecnologias", []) or [])
            ev.append((f"{txt} {tec}".strip(),
                       f"{exp.get('empresa','')} — bullet", 1.0))
    for cat, itens in (perfil.get("competencias") or {}).items():
        ev.append((f"{cat}: {', '.join(itens)}", f"competências ({cat})", 0.6))
    for c in perfil.get("certificacoes", []) or []:
        ev.append((f"{c.get('nome','')} {c.get('emissor','')}", "certificação", 0.7))
    for f in perfil.get("formacao", []) or []:
        ev.append((f"{f.get('grau','')} {f.get('curso','')} {f.get('instituicao','')} "
                   f"{f.get('detalhe','')}", "formação", 0.7))
    for p in perfil.get("projetos", []) or []:
        ev.append((f"{p.get('nome','')} {p.get('descricao','')} "
                   f"{' '.join(p.get('tecnologias', []) or [])}", "projeto", 0.85))
    for i in perfil.get("idiomas", []) or []:
        ev.append((f"{i.get('idioma','')} {i.get('nivel','')} {i.get('certificacao','')}",
                   "idiomas", 0.8))
    return [(t, o, p) for t, o, p in ev if (t or "").strip()]


def texto_perfil(perfil):
    return " \n ".join(t for t, _, _ in coletar_evidencias(perfil))


# --------------------------------------------------------------------------
# Casamento de requisito x evidencia
# --------------------------------------------------------------------------

def expandir(termo, sinonimos):
    chave = normalizar(termo)
    variantes = {chave}
    for grupo in sinonimos:
        grupo_norm = [normalizar(g) for g in grupo]
        if chave in grupo_norm:
            variantes.update(grupo_norm)
    return variantes


def casar_requisito(termo, evidencias, sinonimos, limiar_fuzzy=0.90):
    """Devolve (status, peso_evidencia, trecho, forma_do_match).

    status: 'demonstrado' (aparece em experiencia/projeto),
            'declarado'   (so em lista de competencias/certificacao),
            'ausente'
    """
    variantes = expandir(termo, sinonimos)
    melhor = None
    for texto, origem, peso in evidencias:
        norm = normalizar(texto)
        toks = set(tokens(texto)) | set(bigramas(tokens(texto)))
        for v in variantes:
            forma = None
            if v and re.search(rf"(?<![\w]){re.escape(v)}(?![\w])", norm):
                forma = "literal"
            elif v.replace(" ", "_") in toks:
                forma = "literal"
            else:
                v_toks = v.split()
                if len(v_toks) == 1 and len(v) >= 5:
                    for t in toks:
                        if "_" not in t and similaridade_fuzzy(v, t) >= limiar_fuzzy:
                            forma = f"aproximado (~{t})"
                            break
            if forma:
                cand = (peso, texto.strip()[:180], forma, origem)
                if melhor is None or cand[0] > melhor[0]:
                    melhor = cand
    if not melhor:
        return ("ausente", 0.0, "", "", "")
    peso, trecho, forma, origem = melhor
    status = "demonstrado" if peso >= 0.7 else "declarado"
    return (status, peso, trecho, forma, origem)


# --------------------------------------------------------------------------
# Similaridade lexical global (cosseno sobre tf logaritmico)
# --------------------------------------------------------------------------

def cosseno_tf(texto_a, texto_b):
    ta, tb = tokens(texto_a), tokens(texto_b)
    va = Counter(ta) + Counter(bigramas(ta))
    vb = Counter(tb) + Counter(bigramas(tb))
    if not va or not vb:
        return 0.0
    wa = {k: 1 + math.log(v) for k, v in va.items()}
    wb = {k: 1 + math.log(v) for k, v in vb.items()}
    comum = set(wa) & set(wb)
    num = sum(wa[k] * wb[k] for k in comum)
    den = math.sqrt(sum(v * v for v in wa.values())) * \
        math.sqrt(sum(v * v for v in wb.values()))
    return num / den if den else 0.0


# --------------------------------------------------------------------------
# Senioridade / anos de experiencia
# --------------------------------------------------------------------------

def meses(inicio, fim):
    def parse(v):
        if not v:
            return None
        v = str(v).strip().lower()
        if v in ("atual", "present", "current", "hoje"):
            hoje = date.today()
            return hoje.year * 12 + hoje.month
        m = re.match(r"^(\d{4})[-/](\d{1,2})", v)
        if m:
            return int(m.group(1)) * 12 + int(m.group(2))
        m = re.match(r"^(\d{4})$", v)
        if m:
            return int(m.group(1)) * 12 + 6
        return None
    a, b = parse(inicio), parse(fim)
    if a is None or b is None:
        return 0
    return max(0, b - a)


def anos_experiencia(perfil):
    """Soma de intervalos, unindo sobreposicoes para nao inflar."""
    intervalos = []
    for e in perfil.get("experiencias", []):
        def parse(v):
            if not v:
                return None
            v = str(v).strip().lower()
            if v in ("atual", "present", "current", "hoje"):
                h = date.today()
                return h.year * 12 + h.month
            m = re.match(r"^(\d{4})[-/](\d{1,2})", v)
            if m:
                return int(m.group(1)) * 12 + int(m.group(2))
            m = re.match(r"^(\d{4})$", v)
            if m:
                return int(m.group(1)) * 12 + 6
            return None
        a, b = parse(e.get("inicio")), parse(e.get("fim"))
        if a is not None and b is not None and b >= a:
            intervalos.append((a, b))
    if not intervalos:
        return 0.0
    intervalos.sort()
    unidos = [list(intervalos[0])]
    for a, b in intervalos[1:]:
        if a <= unidos[-1][1]:
            unidos[-1][1] = max(unidos[-1][1], b)
        else:
            unidos.append([a, b])
    return round(sum(b - a for a, b in unidos) / 12, 1)


# --------------------------------------------------------------------------
# Score
# --------------------------------------------------------------------------

PESOS_COMPONENTES = {
    "obrigatorios": 0.55,
    "desejaveis": 0.15,
    "similaridade": 0.15,
    "senioridade": 0.15,
}

VALOR_STATUS = {"demonstrado": 1.0, "declarado": 0.6, "ausente": 0.0}


def avaliar(perfil, vaga, sinonimos):
    evidencias = coletar_evidencias(perfil)

    def bloco(lista):
        itens = []
        for req in lista or []:
            if isinstance(req, str):
                req = {"termo": req, "peso": 1}
            termo = req.get("termo", "")
            peso = float(req.get("peso", 1) or 1)
            status, pe, trecho, forma, origem = casar_requisito(termo, evidencias, sinonimos)
            itens.append({
                "termo": termo,
                "peso": peso,
                "tipo": req.get("tipo", ""),
                "status": status,
                "match": forma,
                "origem": origem,
                "evidencia": trecho,
                "pontos": VALOR_STATUS[status] * peso,
                "maximo": peso,
            })
        return itens

    obrig = bloco(vaga.get("requisitos_obrigatorios"))
    desej = bloco(vaga.get("requisitos_desejaveis"))

    def taxa(itens):
        tot = sum(i["maximo"] for i in itens)
        return (sum(i["pontos"] for i in itens) / tot) if tot else None

    t_obrig = taxa(obrig)
    t_desej = taxa(desej)

    sim_bruta = cosseno_tf(texto_perfil(perfil),
                           vaga.get("texto_completo") or " ".join(
                               [r["termo"] if isinstance(r, dict) else r
                                for r in (vaga.get("requisitos_obrigatorios") or [])]))
    # Calibracao: cosseno tf entre CV e anuncio raramente passa de ~0.35 mesmo
    # em aderencia alta (vocabulario e tamanho muito diferentes). 0.35 = teto.
    sim = min(1.0, sim_bruta / 0.35)

    anos = anos_experiencia(perfil)
    min_anos = vaga.get("anos_minimos")
    if min_anos:
        t_sen = min(1.0, anos / float(min_anos))
    else:
        t_sen = None

    # Renormaliza os pesos ignorando componentes sem dado
    componentes = {"obrigatorios": t_obrig, "desejaveis": t_desej,
                   "similaridade": sim, "senioridade": t_sen}
    disponiveis = {k: v for k, v in componentes.items() if v is not None}
    soma_pesos = sum(PESOS_COMPONENTES[k] for k in disponiveis)
    score = sum(PESOS_COMPONENTES[k] * v for k, v in disponiveis.items()) / soma_pesos
    score100 = round(score * 100, 1)

    if score100 >= 80:
        faixa = "Forte — aplicar e priorizar"
    elif score100 >= 65:
        faixa = "Boa — aplicar com currículo adaptado"
    elif score100 >= 50:
        faixa = "Média — aplicar só se a vaga interessa muito; endereçar gaps na carta"
    else:
        faixa = "Baixa — provavelmente não passa da triagem"

    # Eliminatorios: nunca zeram o score em silencio, sao reportados a parte
    elim = []
    texto_p = normalizar(texto_perfil(perfil))
    for k in vaga.get("eliminatorios") or []:
        crit = k.get("criterio") if isinstance(k, dict) else str(k)
        chaves = (k.get("termos_evidencia") if isinstance(k, dict) else None) or []
        atendido = any(normalizar(c) in texto_p for c in chaves) if chaves else None
        elim.append({"criterio": crit,
                     "atendido": atendido,
                     "acao": "confirmar com o candidato" if atendido is None
                             else ("ok" if atendido else "risco de eliminação")})

    gaps = sorted([i for i in obrig if i["status"] == "ausente"],
                  key=lambda x: -x["peso"]) + \
        sorted([i for i in obrig if i["status"] == "declarado"],
               key=lambda x: -x["peso"])

    return {
        "vaga": {"titulo": vaga.get("titulo"), "empresa": vaga.get("empresa"),
                 "local": vaga.get("local"), "url": vaga.get("url")},
        "score": score100,
        "faixa": faixa,
        "componentes": {
            "cobertura_obrigatorios": None if t_obrig is None else round(t_obrig * 100, 1),
            "cobertura_desejaveis": None if t_desej is None else round(t_desej * 100, 1),
            "similaridade_lexical": round(sim * 100, 1),
            "similaridade_lexical_bruta": round(sim_bruta * 100, 1),
            "senioridade": None if t_sen is None else round(t_sen * 100, 1),
            "anos_experiencia_calculados": anos,
            "anos_minimos_vaga": min_anos,
        },
        "requisitos_obrigatorios": obrig,
        "requisitos_desejaveis": desej,
        "eliminatorios": elim,
        "gaps_priorizados": [{"termo": g["termo"], "peso": g["peso"],
                              "status": g["status"]} for g in gaps],
    }


# --------------------------------------------------------------------------
# Relatorio
# --------------------------------------------------------------------------

ICONE = {"demonstrado": "[++]", "declarado": "[+-]", "ausente": "[--]"}


def relatorio(r):
    L = []
    v = r["vaga"]
    L.append(f"VAGA: {v.get('titulo') or '?'} — {v.get('empresa') or '?'}"
             + (f" ({v['local']})" if v.get("local") else ""))
    L.append(f"SCORE DE ADERÊNCIA: {r['score']}/100 — {r['faixa']}")
    c = r["componentes"]
    L.append("")
    L.append("Componentes:")
    L.append(f"  obrigatórios cobertos ....... {c['cobertura_obrigatorios']}%")
    L.append(f"  desejáveis cobertos ......... {c['cobertura_desejaveis']}%")
    L.append(f"  similaridade lexical ........ {c['similaridade_lexical']}%")
    if c["senioridade"] is not None:
        L.append(f"  senioridade ................. {c['senioridade']}% "
                 f"({c['anos_experiencia_calculados']} anos vs {c['anos_minimos_vaga']} exigidos)")
    L.append("")
    L.append("Requisitos obrigatórios:")
    for i in r["requisitos_obrigatorios"]:
        L.append(f"  {ICONE[i['status']]} {i['termo']} (peso {i['peso']:g}) — {i['status']}")
        if i["evidencia"]:
            L.append(f"        evidência [{i['origem']}]: {i['evidencia']}")
    if r["requisitos_desejaveis"]:
        L.append("")
        L.append("Desejáveis:")
        for i in r["requisitos_desejaveis"]:
            L.append(f"  {ICONE[i['status']]} {i['termo']} — {i['status']}")
    if r["eliminatorios"]:
        L.append("")
        L.append("Critérios eliminatórios:")
        for e in r["eliminatorios"]:
            L.append(f"  - {e['criterio']}: {e['acao']}")
    if r["gaps_priorizados"]:
        L.append("")
        L.append("Gaps por prioridade (entrada para o plano de preparação):")
        for g in r["gaps_priorizados"]:
            L.append(f"  {g['peso']:g}x {g['termo']} ({g['status']})")
    L.append("")
    L.append("Legenda: [++] demonstrado na experiência · [+-] apenas declarado em "
             "competências · [--] ausente")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description="Score de aderência currículo x vaga.")
    ap.add_argument("perfil")
    ap.add_argument("vaga")
    ap.add_argument("--sinonimos", default=None,
                    help="JSON com lista de grupos de sinônimos (default: assets/sinonimos.json)")
    ap.add_argument("--json", action="store_true", help="imprime só o JSON do resultado")
    ap.add_argument("--saida", default=None, help="grava o JSON do resultado neste caminho")
    args = ap.parse_args()

    perfil = json.loads(Path(args.perfil).read_text(encoding="utf-8"))
    vaga = json.loads(Path(args.vaga).read_text(encoding="utf-8"))

    caminho_sin = args.sinonimos or (Path(__file__).parent.parent / "assets" / "sinonimos.json")
    sinonimos = []
    try:
        sinonimos = json.loads(Path(caminho_sin).read_text(encoding="utf-8"))
    except Exception:
        pass

    r = avaliar(perfil, vaga, sinonimos)
    if args.saida:
        Path(args.saida).write_text(json.dumps(r, ensure_ascii=False, indent=2),
                                    encoding="utf-8")
    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print(relatorio(r))


if __name__ == "__main__":
    main()
