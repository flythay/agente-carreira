#!/usr/bin/env python3
"""
Extrai uma vaga a partir de um link.

Estrategia em camadas:
  1. JSON-LD schema.org/JobPosting embutido na pagina — a maioria dos ATS
     (Greenhouse, Lever, Workday, Ashby, SmartRecruiters, Gupy) publica isso
     porque e requisito do Google for Jobs. Da titulo, empresa, local, data,
     salario e descricao ja estruturados.
  2. Endpoint JSON do proprio ATS, quando a URL e reconhecida.
  3. Fallback: texto limpo da pagina, para o LLM interpretar.

Os campos de requisitos ficam vazios de proposito: quem classifica
obrigatorio x desejavel e atribui peso e o modelo, com julgamento.

Uso:
    python vaga_de_url.py "https://boards.greenhouse.io/empresa/jobs/123" --saida vaga.json
    python vaga_de_url.py "https://..." --texto     # so o texto limpo

Sem dependencias externas (urllib + html.parser).
"""

import argparse
import hashlib
import json
import re
import sys
import urllib.request
import urllib.error
from datetime import date
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urlparse

UA = ("Mozilla/5.0 (compatible; AgenteCarreira/1.0; "
      "+uso pessoal de candidatura)")
TIMEOUT = 25


def baixar(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
        "Accept-Language": "en,pt-BR;q=0.8",
    })
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        bruto = r.read()
        charset = r.headers.get_content_charset() or "utf-8"
        return bruto.decode(charset, errors="replace"), r.headers.get("Content-Type", "")


# --------------------------------------------------------------------------
# 1) JSON-LD
# --------------------------------------------------------------------------

class ColetorScripts(HTMLParser):
    def __init__(self):
        super().__init__()
        self.capturando = False
        self.blocos = []
        self._buf = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "script":
            d = dict(attrs)
            if (d.get("type") or "").lower().strip() == "application/ld+json":
                self.capturando = True
                self._buf = []

    def handle_endtag(self, tag):
        if tag.lower() == "script" and self.capturando:
            self.blocos.append("".join(self._buf))
            self.capturando = False

    def handle_data(self, data):
        if self.capturando:
            self._buf.append(data)


def achar_jobposting(html):
    p = ColetorScripts()
    try:
        p.feed(html)
    except Exception:
        pass

    def varrer(no):
        if isinstance(no, dict):
            t = no.get("@type")
            tipos = t if isinstance(t, list) else [t]
            if any(str(x).lower() == "jobposting" for x in tipos if x):
                return no
            for v in no.values():
                r = varrer(v)
                if r:
                    return r
        elif isinstance(no, list):
            for v in no:
                r = varrer(v)
                if r:
                    return r
        return None

    for bloco in p.blocos:
        txt = bloco.strip()
        if not txt:
            continue
        for tentativa in (txt, re.sub(r",\s*([}\]])", r"\1", txt)):
            try:
                dados = json.loads(tentativa)
            except Exception:
                continue
            achado = varrer(dados)
            if achado:
                return achado
    return None


# --------------------------------------------------------------------------
# HTML -> texto
# --------------------------------------------------------------------------

class ParaTexto(HTMLParser):
    IGNORAR = {"script", "style", "noscript", "svg", "head"}
    QUEBRA = {"p", "br", "div", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6",
              "section", "ul", "ol"}

    def __init__(self):
        super().__init__()
        self.pilha_ignora = 0
        self.partes = []

    def handle_starttag(self, tag, attrs):
        t = tag.lower()
        if t in self.IGNORAR:
            self.pilha_ignora += 1
        elif t in self.QUEBRA:
            self.partes.append("\n")
        if t == "li":
            self.partes.append("- ")

    def handle_endtag(self, tag):
        t = tag.lower()
        if t in self.IGNORAR and self.pilha_ignora:
            self.pilha_ignora -= 1
        elif t in self.QUEBRA:
            self.partes.append("\n")

    def handle_data(self, data):
        if not self.pilha_ignora:
            self.partes.append(data)


def html_para_texto(html):
    p = ParaTexto()
    try:
        p.feed(html)
    except Exception:
        pass
    txt = unescape("".join(p.partes))
    txt = re.sub(r"[ \t\r\f\v]+", " ", txt)
    txt = re.sub(r"\n\s*\n\s*\n+", "\n\n", txt)
    linhas = [l.strip() for l in txt.split("\n")]
    return "\n".join(l for l in linhas if l).strip()


# --------------------------------------------------------------------------
# 2) Endpoints de ATS conhecidos
# --------------------------------------------------------------------------

def url_api_ats(url):
    """Devolve (url_json, fonte) quando reconhece o ATS, senao (None, None)."""
    u = urlparse(url)
    host, caminho = u.netloc.lower(), u.path

    m = re.search(r"/(?:embed/job_app\?for=|)([\w-]+)/jobs/(\d+)", caminho)
    if "greenhouse.io" in host and m:
        return (f"https://boards-api.greenhouse.io/v1/boards/{m.group(1)}"
                f"/jobs/{m.group(2)}", "greenhouse")

    m = re.search(r"/([\w.-]+)/([0-9a-f-]{36})", caminho)
    if "lever.co" in host and m:
        return (f"https://api.lever.co/v0/postings/{m.group(1)}/{m.group(2)}",
                "lever")

    if "ashbyhq.com" in host:
        m = re.search(r"/([\w.-]+)/", caminho)
        if m:
            return (f"https://api.ashbyhq.com/posting-api/job-board/{m.group(1)}",
                    "ashby")
    return (None, None)


def de_jsonld(j, url):
    def txt(x):
        if isinstance(x, dict):
            return x.get("name") or x.get("value") or ""
        return x or ""

    org = j.get("hiringOrganization") or {}
    local_obj = j.get("jobLocation") or {}
    if isinstance(local_obj, list):
        local_obj = local_obj[0] if local_obj else {}
    end = (local_obj or {}).get("address") or {}
    partes = [end.get("addressLocality"), end.get("addressRegion"),
              end.get("addressCountry")]
    if isinstance(partes[-1], dict):
        partes[-1] = partes[-1].get("name")
    local = ", ".join([str(p) for p in partes if p])

    desc = html_para_texto(j.get("description") or "")

    salario = ""
    bs = j.get("baseSalary") or {}
    v = (bs.get("value") or {}) if isinstance(bs, dict) else {}
    if v:
        faixa = [v.get("minValue"), v.get("maxValue"), v.get("value")]
        faixa = [str(x) for x in faixa if x]
        if faixa:
            salario = (f"{bs.get('currency','')} {' – '.join(faixa)} "
                       f"{v.get('unitText','')}").strip()

    remoto = j.get("jobLocationType") == "TELECOMMUTE"

    return {
        "titulo": txt(j.get("title")),
        "empresa": txt(org),
        "local": "Remoto" if (remoto and not local) else local,
        "modalidade": "remoto" if remoto else "",
        "faixa_salarial": salario,
        "data_publicacao": (j.get("datePosted") or "")[:10],
        "prazo": (j.get("validThrough") or "")[:10],
        "tipo_contrato": j.get("employmentType") or "",
        "texto_completo": desc,
        "url": url,
        "fonte": "json-ld",
    }


def de_api_ats(dados, fonte, url):
    if fonte == "greenhouse":
        loc = (dados.get("location") or {}).get("name", "")
        return {"titulo": dados.get("title", ""), "empresa": "",
                "local": loc, "modalidade": "",
                "data_publicacao": (dados.get("updated_at") or "")[:10],
                "texto_completo": html_para_texto(unescape(dados.get("content") or "")),
                "url": dados.get("absolute_url") or url, "fonte": "greenhouse"}
    if fonte == "lever":
        cat = dados.get("categories") or {}
        return {"titulo": dados.get("text", ""), "empresa": "",
                "local": cat.get("location", ""),
                "modalidade": cat.get("commitment", ""),
                "data_publicacao": "",
                "texto_completo": html_para_texto(dados.get("description", "") +
                                                  " " + str(dados.get("lists", ""))),
                "url": dados.get("hostedUrl") or url, "fonte": "lever"}
    return None


# --------------------------------------------------------------------------

MOLDE = {
    "id": "", "titulo": "", "empresa": "", "local": "", "modalidade": "",
    "idioma_anuncio": "", "senioridade": "", "anos_minimos": None,
    "faixa_salarial": "", "url": "", "fonte": "", "data_publicacao": "",
    "prazo": "", "requisitos_obrigatorios": [], "requisitos_desejaveis": [],
    "eliminatorios": [], "responsabilidades": [], "sobre_empresa": "",
    "beneficios": [], "texto_completo": "", "capturado_em": "",
}


def id_vaga(v):
    base = f"{v.get('empresa','')}|{v.get('titulo','')}|{v.get('local','')}"
    return hashlib.sha1(base.lower().encode("utf-8")).hexdigest()[:16]


def extrair(url):
    api, fonte = url_api_ats(url)
    if api:
        try:
            corpo, _ = baixar(api)
            dados = json.loads(corpo)
            r = de_api_ats(dados, fonte, url)
            if r and r.get("texto_completo"):
                return r
        except Exception as e:
            print(f"[aviso] endpoint {fonte} falhou ({e}); tentando HTML",
                  file=sys.stderr)

    html, ctype = baixar(url)
    if "application/json" in ctype:
        try:
            return {"titulo": "", "empresa": "", "local": "",
                    "texto_completo": json.dumps(json.loads(html), ensure_ascii=False),
                    "url": url, "fonte": "json"}
        except Exception:
            pass

    j = achar_jobposting(html)
    if j:
        return de_jsonld(j, url)

    print("[aviso] sem JSON-LD JobPosting nesta página — usando texto puro. "
          "Confira se a página não exige login ou JavaScript.", file=sys.stderr)
    return {"titulo": "", "empresa": "", "local": "",
            "texto_completo": html_para_texto(html), "url": url,
            "fonte": urlparse(url).netloc}


def main():
    ap = argparse.ArgumentParser(description="Extrai vaga a partir de um link.")
    ap.add_argument("url")
    ap.add_argument("--saida", default=None, help="grava vaga.json neste caminho")
    ap.add_argument("--texto", action="store_true", help="imprime só o texto da vaga")
    args = ap.parse_args()

    try:
        dados = extrair(args.url)
    except urllib.error.HTTPError as e:
        print(f"[erro] HTTP {e.code} ao acessar a página. Muitos sites bloqueiam "
              f"acesso automatizado — nesse caso copie e cole o texto do anúncio.",
              file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"[erro] {e}", file=sys.stderr)
        sys.exit(2)

    if args.texto:
        print(dados.get("texto_completo", ""))
        return

    vaga = dict(MOLDE)
    vaga.update({k: v for k, v in dados.items() if v not in (None, "")})
    vaga["capturado_em"] = date.today().isoformat()
    vaga["id"] = id_vaga(vaga)

    saida = json.dumps(vaga, ensure_ascii=False, indent=2)
    if args.saida:
        open(args.saida, "w", encoding="utf-8").write(saida)
        print(f"[ok] {args.saida} — título: {vaga['titulo'] or '(preencher)'} · "
              f"{len(vaga['texto_completo'])} caracteres de descrição")
        print("[próximo passo] classificar requisitos obrigatórios/desejáveis "
              "e pesos antes de rodar o score.")
    else:
        print(saida)


if __name__ == "__main__":
    main()
