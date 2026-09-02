#!/usr/bin/env python3
"""
Gera um cronograma de preparacao a partir do score.json (saida do skill
match-score-vaga) e da data da entrevista.

Aloca as horas disponiveis por peso do requisito, reserva tempo fixo para
ensaio de respostas e deixa a vespera para revisao.

Uso:
    python gerar_plano.py score.json --data-entrevista 2026-09-15 --horas-dia 2
    python gerar_plano.py score.json --dias 7 --horas-dia 1.5 --saida plano.md
"""

import argparse
import json
from datetime import date, datetime, timedelta
from pathlib import Path

# Fracao das horas totais reservada para cada tipo de trabalho
FRACAO_ESTUDO = 0.55      # fechar gaps tecnicos
FRACAO_ENSAIO = 0.30      # respostas, historias, simulacao
FRACAO_PESQUISA = 0.15    # empresa, produto, entrevistadores, salario

PESO_STATUS = {"ausente": 1.0, "declarado": 0.5}


def dias_uteis_ate(alvo, hoje=None):
    hoje = hoje or date.today()
    return max(1, (alvo - hoje).days)


def alocar(gaps, horas_estudo):
    """Distribui horas proporcionalmente a peso x severidade do status."""
    itens = []
    for g in gaps:
        peso = float(g.get("peso", 1) or 1)
        sev = PESO_STATUS.get(g.get("status", "ausente"), 1.0)
        itens.append((g.get("termo", "?"), g.get("status", "ausente"), peso * sev))
    total = sum(i[2] for i in itens) or 1
    saida = []
    for termo, status, p in sorted(itens, key=lambda x: -x[2]):
        h = round(horas_estudo * p / total, 1)
        if h >= 0.3:  # abaixo disso nao vale bloco proprio
            saida.append({"termo": termo, "status": status, "horas": h})
    return saida


def objetivo_para(termo, status):
    if status == "declarado":
        return (f"transformar '{termo}' de declarado em demonstrável: preparar 1 história "
                f"real de uso com contexto, decisão e resultado")
    return (f"atingir 'sei explicar e sei fazer um exemplo pequeno' em '{termo}': "
            f"conceito → exemplo mínimo funcionando → 1 pergunta provável respondida em voz alta")


def gerar(score, dias, horas_dia, data_entrevista):
    total = dias * horas_dia
    h_estudo = total * FRACAO_ESTUDO
    h_ensaio = total * FRACAO_ENSAIO
    h_pesq = total * FRACAO_PESQUISA

    v = score.get("vaga", {})
    gaps = score.get("gaps_priorizados", [])
    blocos = alocar(gaps, h_estudo)

    L = []
    L.append(f"# Plano de preparação — {v.get('titulo') or 'vaga'} "
             f"({v.get('empresa') or '?'})")
    L.append("")
    L.append(f"- Score de aderência atual: **{score.get('score')}/100** — {score.get('faixa','')}")
    if data_entrevista:
        L.append(f"- Entrevista em **{data_entrevista.strftime('%d/%m/%Y')}** "
                 f"({dias} dia(s) de preparação)")
    else:
        L.append(f"- Janela de preparação: **{dias} dia(s)**")
    L.append(f"- Tempo total: **{total:.1f}h** "
             f"({h_estudo:.1f}h fechar gaps · {h_ensaio:.1f}h ensaio · {h_pesq:.1f}h pesquisa)")
    L.append("")

    elim = [e for e in score.get("eliminatorios", []) if e.get("acao") != "ok"]
    if elim:
        L.append("## ⚠ Resolver antes de tudo")
        for e in elim:
            L.append(f"- **{e['criterio']}** — {e['acao']}. "
                     f"Ter uma frase pronta sobre isso; provavelmente é a primeira pergunta do RH.")
        L.append("")

    L.append("## 1. Fechar gaps (por prioridade)")
    L.append("")
    if not blocos:
        L.append("Nenhum gap relevante — use o tempo em ensaio e pesquisa.")
    for b in blocos:
        L.append(f"### {b['termo']} — {b['horas']}h  _(status: {b['status']})_")
        L.append(f"Objetivo: {objetivo_para(b['termo'], b['status'])}.")
        L.append("")
    L.append("")

    L.append("## 2. Ensaio de respostas")
    L.append("")
    L.append(f"Reservar **{h_ensaio:.1f}h**, sempre em voz alta e cronometrado (60–90s por resposta):")
    L.append("")
    L.append("- 6 a 8 respostas técnicas ancoradas em experiências reais do currículo")
    L.append("- 4 comportamentais (conflito, erro, prioridade, influência sem autoridade)")
    L.append("- as 3 difíceis: motivo da saída, lacuna no histórico, pretensão salarial")
    L.append("- 1 simulação completa no idioma do processo, sem pausar para pensar")
    L.append("")

    L.append("## 3. Pesquisa")
    L.append("")
    L.append(f"Reservar **{h_pesq:.1f}h**:")
    L.append("")
    L.append(f"- o que a {v.get('empresa') or 'empresa'} faz, como ganha dinheiro, notícias dos últimos 6 meses")
    L.append("- produto/área específica da vaga e quem consome o trabalho")
    L.append("- perfil dos entrevistadores, se conhecidos")
    L.append("- faixa salarial para o nível e o país da vaga; definir número de partida e piso")
    L.append("- 5 perguntas para fazer ao entrevistador")
    L.append("")

    if data_entrevista:
        L.append("## 4. Distribuição por dia")
        L.append("")
        hoje = date.today()
        seq = [b for b in blocos]
        idx = 0
        for d in range(dias):
            dia = hoje + timedelta(days=d)
            falta = (data_entrevista - dia).days
            if falta == 0:
                L.append(f"- **{dia.strftime('%d/%m')}** — entrevista. "
                         f"Revisar só as 3 histórias principais e as perguntas a fazer.")
            elif falta == 1:
                L.append(f"- **{dia.strftime('%d/%m')}** — véspera: revisão e simulação completa. "
                         f"Nada de conteúdo novo. Testar link, câmera e fuso horário.")
            else:
                foco = seq[idx % len(seq)]["termo"] if seq else "ensaio de respostas"
                idx += 1
                L.append(f"- **{dia.strftime('%d/%m')}** — {horas_dia:.1f}h: {foco} "
                         f"+ 2 respostas ensaiadas em voz alta")
        L.append("")

    L.append("## 5. Checklist final")
    L.append("")
    for item in ["Fuso horário confirmado e convertido",
                 "Link, câmera, microfone e plano B testados",
                 "Faixa salarial pesquisada; número de partida e piso definidos",
                 "Status de visto/disponibilidade em uma frase pronta",
                 "Currículo adaptado enviado e revisado — sei defender cada linha",
                 "5 perguntas para o entrevistador anotadas",
                 "Registro pós-entrevista preparado (perguntas que apareceram, o que travou)"]:
        L.append(f"- [ ] {item}")
    L.append("")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description="Cronograma de preparação a partir do score.")
    ap.add_argument("score", help="score.json gerado por match_score.py")
    ap.add_argument("--data-entrevista", default=None, help="AAAA-MM-DD")
    ap.add_argument("--dias", type=int, default=None,
                    help="dias de preparação (se não houver data)")
    ap.add_argument("--horas-dia", type=float, default=2.0)
    ap.add_argument("--saida", default=None, help="arquivo .md de saída")
    args = ap.parse_args()

    score = json.loads(Path(args.score).read_text(encoding="utf-8"))

    data_ent = None
    if args.data_entrevista:
        data_ent = datetime.strptime(args.data_entrevista, "%Y-%m-%d").date()
        dias = dias_uteis_ate(data_ent)
    else:
        dias = args.dias or 7

    texto = gerar(score, dias, args.horas_dia, data_ent)
    if args.saida:
        Path(args.saida).write_text(texto, encoding="utf-8")
        print(f"[ok] plano gravado em {args.saida}")
    else:
        print(texto)


if __name__ == "__main__":
    main()
