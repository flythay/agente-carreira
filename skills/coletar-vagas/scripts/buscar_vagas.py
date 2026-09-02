#!/usr/bin/env python3
"""
Busca vagas em fontes que oferecem API publica ou feed oficial, normaliza para
um formato unico e deduplica.

Fontes suportadas (ver references/fontes-e-apis.md para limites e termos):
  remotive      sem chave   remoto, tech, global
  remoteok      sem chave   remoto, tech, global
  arbeitnow     sem chave   Europa (forte na Alemanha), inclui presencial
  arbeitsagentur sem chave  Alemanha, base publica federal
  adzuna        chave       ~20 paises (br, nl, de, uk, us...), agregador
  greenhouse    sem chave   quadro de uma empresa (--empresas)
  lever         sem chave   quadro de uma empresa (--empresas)
  ashby         sem chave   quadro de uma empresa (--empresas)

Uso:
    python buscar_vagas.py --termo "fraud data scientist" --fontes remotive,remoteok
    python buscar_vagas.py --termo "data scientist" --fontes adzuna --pais nl --paginas 2
    python buscar_vagas.py --fontes greenhouse,lever --empresas adyen,mollie,booking
    python buscar_vagas.py --termo "risk" --fontes todas --saida vagas/ --min-dias 14

Credenciais por variavel de ambiente: ADZUNA_APP_ID, ADZUNA_APP_KEY.
Sem dependencias externas.
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from html import unescape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
try:
    from vaga_de_url import html_para_texto
except Exception:                                     # fallback minimo
    def html_para_texto(h):
        return re.sub(r"<[^>]+>", " ", unescape(h or ""))

UA = "Mozilla/5.0 (compatible; AgenteCarreira/1.0; uso pessoal de candidatura)"
TIMEOUT = 25
PAUSA = 0.7          # cortesia entre chamadas; nao remova


def http_json(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept": "application/json",
                                               **(headers or {})})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode(r.headers.get_content_charset() or "utf-8",
                                          errors="replace"))


def registro(**kw):
    base = {"titulo": "", "empresa": "", "local": "", "modalidade": "",
            "faixa_salarial": "", "url": "", "fonte": "", "data_publicacao": "",
            "texto_completo": ""}
    base.update({k: v for k, v in kw.items() if v is not None})
    base["id"] = hashlib.sha1(
        f"{base['empresa']}|{base['titulo']}|{base['local']}".lower().encode()
    ).hexdigest()[:16]
    return base


# --------------------------------------------------------------------------
# Fontes
# --------------------------------------------------------------------------

def f_remotive(termo, **kw):
    url = "https://remotive.com/api/remote-jobs?limit=100"
    if termo:
        url += "&search=" + urllib.parse.quote(termo)
    dados = http_json(url)
    out = []
    for j in dados.get("jobs", []):
        out.append(registro(titulo=j.get("title"), empresa=j.get("company_name"),
                            local=j.get("candidate_required_location") or "Remoto",
                            modalidade="remoto", faixa_salarial=j.get("salary"),
                            url=j.get("url"), fonte="remotive",
                            data_publicacao=(j.get("publication_date") or "")[:10],
                            texto_completo=html_para_texto(j.get("description"))))
    return out


def f_remoteok(termo, **kw):
    dados = http_json("https://remoteok.com/api")
    out = []
    for j in dados:
        if not isinstance(j, dict) or not j.get("position"):
            continue                                  # 1o item e aviso legal
        texto = f"{j.get('position','')} {j.get('description','')}"
        if termo and termo.lower() not in texto.lower():
            continue
        out.append(registro(titulo=j.get("position"), empresa=j.get("company"),
                            local=j.get("location") or "Remoto", modalidade="remoto",
                            faixa_salarial=" – ".join(
                                str(x) for x in [j.get("salary_min"), j.get("salary_max")] if x),
                            url=j.get("url") or j.get("apply_url"), fonte="remoteok",
                            data_publicacao=(j.get("date") or "")[:10],
                            texto_completo=html_para_texto(j.get("description"))))
    return out


def f_arbeitnow(termo, **kw):
    dados = http_json("https://www.arbeitnow.com/api/job-board-api")
    out = []
    for j in dados.get("data", []):
        texto = f"{j.get('title','')} {j.get('description','')}"
        if termo and termo.lower() not in texto.lower():
            continue
        criado = j.get("created_at")
        dt = datetime.utcfromtimestamp(criado).date().isoformat() if criado else ""
        out.append(registro(titulo=j.get("title"), empresa=j.get("company_name"),
                            local=j.get("location"),
                            modalidade="remoto" if j.get("remote") else "presencial",
                            url=j.get("url"), fonte="arbeitnow", data_publicacao=dt,
                            texto_completo=html_para_texto(j.get("description"))))
    return out


def f_arbeitsagentur(termo, pais=None, paginas=1, local=None, **kw):
    """Base publica da Bundesagentur für Arbeit (Alemanha)."""
    out = []
    for p in range(1, paginas + 1):
        q = {"was": termo or "", "page": p, "size": 50, "pav": "false"}
        if local:
            q["wo"] = local
        url = ("https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs?"
               + urllib.parse.urlencode(q))
        dados = http_json(url, headers={"X-API-Key": "jobboerse-jobsuche"})
        for j in dados.get("stellenangebote", []) or []:
            ort = (j.get("arbeitsort") or {})
            loc = ", ".join([x for x in [ort.get("ort"), ort.get("region")] if x])
            ref = j.get("refnr", "")
            out.append(registro(
                titulo=j.get("titel") or j.get("beruf"),
                empresa=j.get("arbeitgeber"), local=loc or "Alemanha",
                url=j.get("externeUrl") or
                    f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{ref}",
                fonte="arbeitsagentur",
                data_publicacao=(j.get("aktuelleVeroeffentlichungsdatum") or "")[:10],
                texto_completo=j.get("titel") or ""))
        time.sleep(PAUSA)
    return out


def f_adzuna(termo, pais="gb", paginas=1, local=None, **kw):
    app_id = os.environ.get("ADZUNA_APP_ID")
    app_key = os.environ.get("ADZUNA_APP_KEY")
    if not (app_id and app_key):
        print("[aviso] ADZUNA_APP_ID/ADZUNA_APP_KEY não definidas — fonte ignorada.",
              file=sys.stderr)
        return []
    out = []
    for p in range(1, paginas + 1):
        q = {"app_id": app_id, "app_key": app_key, "results_per_page": 50,
             "what": termo or "", "content-type": "application/json"}
        if local:
            q["where"] = local
        url = (f"https://api.adzuna.com/v1/api/jobs/{pais}/search/{p}?"
               + urllib.parse.urlencode(q))
        dados = http_json(url)
        for j in dados.get("results", []):
            sal = " – ".join(str(int(x)) for x in
                             [j.get("salary_min"), j.get("salary_max")] if x)
            if sal and j.get("salary_is_predicted") == "1":
                sal += " (estimado)"
            out.append(registro(
                titulo=j.get("title"), empresa=(j.get("company") or {}).get("display_name"),
                local=(j.get("location") or {}).get("display_name"),
                faixa_salarial=sal, url=j.get("redirect_url"), fonte="adzuna",
                data_publicacao=(j.get("created") or "")[:10],
                texto_completo=html_para_texto(j.get("description"))))
        time.sleep(PAUSA)
    return out


def f_greenhouse(termo, empresas=(), **kw):
    out = []
    for e in empresas:
        try:
            dados = http_json(
                f"https://boards-api.greenhouse.io/v1/boards/{e}/jobs?content=true")
        except Exception as ex:
            print(f"[aviso] greenhouse/{e}: {ex}", file=sys.stderr)
            continue
        for j in dados.get("jobs", []):
            texto = html_para_texto(unescape(j.get("content") or ""))
            if termo and termo.lower() not in (j.get("title", "") + texto).lower():
                continue
            out.append(registro(titulo=j.get("title"), empresa=e,
                                local=(j.get("location") or {}).get("name"),
                                url=j.get("absolute_url"), fonte="greenhouse",
                                data_publicacao=(j.get("updated_at") or "")[:10],
                                texto_completo=texto))
        time.sleep(PAUSA)
    return out


def f_lever(termo, empresas=(), **kw):
    out = []
    for e in empresas:
        try:
            dados = http_json(f"https://api.lever.co/v0/postings/{e}?mode=json")
        except Exception as ex:
            print(f"[aviso] lever/{e}: {ex}", file=sys.stderr)
            continue
        for j in dados:
            texto = html_para_texto(j.get("descriptionPlain") or j.get("description") or "")
            if termo and termo.lower() not in (j.get("text", "") + texto).lower():
                continue
            cat = j.get("categories") or {}
            criado = j.get("createdAt")
            out.append(registro(
                titulo=j.get("text"), empresa=e, local=cat.get("location"),
                modalidade=cat.get("commitment"), url=j.get("hostedUrl"),
                fonte="lever", texto_completo=texto,
                data_publicacao=(datetime.utcfromtimestamp(criado / 1000).date().isoformat()
                                 if criado else "")))
        time.sleep(PAUSA)
    return out


def f_ashby(termo, empresas=(), **kw):
    out = []
    for e in empresas:
        try:
            dados = http_json(
                f"https://api.ashbyhq.com/posting-api/job-board/{e}?includeCompensation=true")
        except Exception as ex:
            print(f"[aviso] ashby/{e}: {ex}", file=sys.stderr)
            continue
        for j in dados.get("jobs", []):
            texto = html_para_texto(j.get("descriptionHtml") or j.get("descriptionPlain") or "")
            if termo and termo.lower() not in (j.get("title", "") + texto).lower():
                continue
            out.append(registro(titulo=j.get("title"), empresa=e,
                                local=j.get("location"),
                                modalidade="remoto" if j.get("isRemote") else "",
                                url=j.get("jobUrl"), fonte="ashby",
                                data_publicacao=(j.get("publishedAt") or "")[:10],
                                texto_completo=texto))
        time.sleep(PAUSA)
    return out


FONTES = {"remotive": f_remotive, "remoteok": f_remoteok, "arbeitnow": f_arbeitnow,
          "arbeitsagentur": f_arbeitsagentur, "adzuna": f_adzuna,
          "greenhouse": f_greenhouse, "lever": f_lever, "ashby": f_ashby}


# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Busca vagas em fontes oficiais.")
    ap.add_argument("--termo", default="", help='ex.: "fraud data scientist"')
    ap.add_argument("--fontes", default="remotive,remoteok",
                    help="lista separada por vírgula, ou 'todas'")
    ap.add_argument("--pais", default="gb", help="código Adzuna: br, nl, de, gb, us...")
    ap.add_argument("--local", default=None, help="cidade/região (adzuna, arbeitsagentur)")
    ap.add_argument("--empresas", default="", help="slugs para greenhouse/lever/ashby")
    ap.add_argument("--paginas", type=int, default=1)
    ap.add_argument("--min-dias", type=int, default=None,
                    help="descarta anúncios mais antigos que N dias")
    ap.add_argument("--saida", default=None,
                    help="diretório: grava um vaga_<id>.json por vaga; "
                         "arquivo .jsonl: grava tudo em um arquivo")
    args = ap.parse_args()

    nomes = list(FONTES) if args.fontes.strip() == "todas" else \
        [f.strip() for f in args.fontes.split(",") if f.strip()]
    empresas = [e.strip() for e in args.empresas.split(",") if e.strip()]

    todas = []
    for n in nomes:
        fn = FONTES.get(n)
        if not fn:
            print(f"[aviso] fonte desconhecida: {n}", file=sys.stderr)
            continue
        try:
            r = fn(args.termo, pais=args.pais, paginas=args.paginas,
                   local=args.local, empresas=empresas)
            print(f"[{n}] {len(r)} vagas", file=sys.stderr)
            todas.extend(r)
        except Exception as e:
            print(f"[erro] {n}: {e}", file=sys.stderr)
        time.sleep(PAUSA)

    # Dedup por id (empresa+titulo+local)
    vistos, unicas = set(), []
    for v in todas:
        if v["id"] in vistos:
            continue
        vistos.add(v["id"])
        unicas.append(v)

    if args.min_dias:
        limite = (date.today() - timedelta(days=args.min_dias)).isoformat()
        unicas = [v for v in unicas
                  if not v["data_publicacao"] or v["data_publicacao"] >= limite]

    unicas.sort(key=lambda v: v["data_publicacao"], reverse=True)
    print(f"[total] {len(unicas)} vagas únicas", file=sys.stderr)

    if not args.saida:
        print(json.dumps(unicas, ensure_ascii=False, indent=2))
        return

    p = Path(args.saida)
    if str(p).endswith(".jsonl"):
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8") as fh:
            for v in unicas:
                fh.write(json.dumps(v, ensure_ascii=False) + "\n")
    else:
        p.mkdir(parents=True, exist_ok=True)
        for v in unicas:
            (p / f"vaga_{v['id']}.json").write_text(
                json.dumps(v, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[ok] gravado em {p}", file=sys.stderr)


if __name__ == "__main__":
    main()
