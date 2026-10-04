"""Візуалізація RDF-графу: статична схема зрізу та інтерактивний повний граф."""

import html
import shutil
import subprocess

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, FOAF, RDF, SKOS

BASE = "https://example.org/onp/"
ONP = Namespace(BASE)
SDO = Namespace("https://schema.org/")
ORG = Namespace("http://www.w3.org/ns/org#")

KOLORY = {
    "OsvitnyaPrograma": "#8B0000",
    "OsvitniyKomponent": "#1F4E79",
    "FormaKontrolyu": "#2E7D32",
    "Kompetentnist": "#B8860B",
    "RezultatNavchannya": "#6A1B9A",
    "Universytet": "#000000",
    "Fakultet": "#37474F",
    "Kafedra": "#37474F",
    "Grupa": "#00695C",
    "Pidgrupa": "#00838F",
    "Student": "#90A4AE",
}

ROZMIRY = {"OsvitnyaPrograma": 34, "Universytet": 28, "OsvitniyKomponent": 22, "Student": 8}

# на схемі показуємо тільки каркас програми, інакше 500+ ребер нечитабельні
ZVYAZKY_ZRIZU = [
    SDO.hasCourse,
    ONP.maieFormuKontrolyu,
    ONP.realizuietsyaKafedroyu,
    ONP.navchaietsyaZaProgramoyu,
    ORG.subOrganizationOf,
]


def skorotyty(uri):
    return str(uri).split("/")[-1].split("#")[-1]


def typ(g, vuzol):
    for t in g.objects(vuzol, RDF.type):
        nazva = str(t).replace(BASE, "")
        if nazva in KOLORY:
            return nazva
    return None


def pidpys(g, vuzol):
    for p in (SDO.courseCode, SKOS.notation):
        znachennya = g.value(vuzol, p)
        if znachennya:
            return str(znachennya)
    for p in (SDO.name, FOAF.name, SKOS.prefLabel, DCTERMS.title):
        for znachennya in g.objects(vuzol, p):
            if isinstance(znachennya, Literal) and znachennya.language in (None, "uk"):
                tekst = str(znachennya)
                return tekst if len(tekst) <= 34 else tekst[:31] + "…"
    return skorotyty(vuzol)


def zibraty_zriz(g):
    vuzly = {}
    rebra = []
    for predykat in ZVYAZKY_ZRIZU:
        for subyekt, obyekt in g.subject_objects(predykat):
            if not isinstance(obyekt, URIRef):
                continue
            ts, to = typ(g, subyekt), typ(g, obyekt)
            if not ts or not to or "Student" in (ts, to) or ts == "Pidgrupa":
                continue
            vuzly[subyekt] = ts
            vuzly[obyekt] = to
            rebra.append((subyekt, skorotyty(predykat), obyekt))
    return vuzly, rebra


def zriz_png(g, out="graf_zriz.png"):
    if not shutil.which("dot"):
        print("Graphviz не знайдено — статичну схему пропущено")
        return None

    vuzly, rebra = zibraty_zriz(g)
    ids = {vuzol: f"n{i}" for i, vuzol in enumerate(vuzly)}

    rows = [
        "digraph G {",
        '  rankdir=LR; bgcolor="white";',
        '  node [shape=box style="rounded,filled" fontname="DejaVu Sans" '
        'fontsize=10 fillcolor="#FFFFFF"];',
        '  edge [fontname="DejaVu Sans" fontsize=8 color="#666666"];',
    ]
    for vuzol, t in vuzly.items():
        rows.append(
            f'  {ids[vuzol]} [label="{html.escape(pidpys(g, vuzol))}" '
            f'color="{KOLORY[t]}" fontcolor="{KOLORY[t]}"];'
        )
    for subyekt, predykat, obyekt in rebra:
        rows.append(f'  {ids[subyekt]} -> {ids[obyekt]} [label="{html.escape(predykat)}"];')
    rows.append("}")

    with open("graf_zriz.dot", "w", encoding="utf-8") as f:
        f.write("\n".join(rows))
    subprocess.run(["dot", "-Tpng", "-Gdpi=150", "graf_zriz.dot", "-o", out], check=True)
    print(f"створено {out} ({len(vuzly)} вузлів, {len(rebra)} ребер)")
    return out


def povnyi_html(g, out="graf_povnyi.html"):
    from pyvis.network import Network

    net = Network(height="820px", width="100%", directed=True,
                  bgcolor="#ffffff", font_color="#222222")
    net.barnes_hut(gravity=-9000, spring_length=130)
    dodani = set()

    def dodaty(vuzol, t):
        if vuzol in dodani:
            return
        net.add_node(str(vuzol), label=pidpys(g, vuzol), color=KOLORY[t],
                     size=ROZMIRY.get(t, 15), title=f"{t}: {pidpys(g, vuzol)}")
        dodani.add(vuzol)

    for subyekt, predykat, obyekt in g:
        if predykat == RDF.type or not isinstance(obyekt, URIRef):
            continue
        ts, to = typ(g, subyekt), typ(g, obyekt)
        if not ts or not to:
            continue
        dodaty(subyekt, ts)
        dodaty(obyekt, to)
        net.add_edge(str(subyekt), str(obyekt), label=skorotyty(predykat),
                     color="#bbbbbb", width=0.5)

    net.save_graph(out)
    print(f"створено {out} ({len(dodani)} вузлів)")
    return out


if __name__ == "__main__":
    graf = Graph()
    graf.parse("onp.ttl", format="turtle")
    zriz_png(graf)
    povnyi_html(graf)
