"""П.5 — поєднання власного графу з відкритими даними Wikidata.

Обґрунтування предиката: onp:KNU і wd:Q84151 позначають ту саму реальну
організацію, тому твердження про тотожність денотата (owl:sameAs) коректне.
rdfs:seeAlso було б слабшим, ніж дозволяють дані, а skos:exactMatch описує
відповідність понять, а не окремих об'єктів.

Механіка: rdflib підтримує ключове слово SERVICE, але в evalServiceQuery
жорстко зашитий заголовок user-agent «rdflibForAnUser» без можливості
перевизначення, а політика Wikimedia блокує неописові user-agent (HTTP 403).
Тому дані тягнемо через SPARQLWrapper із власним user-agent, вливаємо
у локальний граф і виконуємо один запит до об'єднаного графу.
"""

from rdflib import Graph, Namespace, Literal, URIRef, XSD
from rdflib.namespace import RDFS
from SPARQLWrapper import SPARQLWrapper, JSON

import onp_data as d

ENDPOINT = "https://query.wikidata.org/sparql"
# Описовий user-agent згідно з політикою Wikimedia — підставити свої дані:
USER_AGENT = "KNU-SemanticWebLab/1.0 (https://github.com/pryanikalenaknu/semantic-web-lab1)"

WD = Namespace("http://www.wikidata.org/entity/")
WDT = Namespace("http://www.wikidata.org/prop/direct/")
ONP = Namespace("https://example.org/onp/")

ZAPYT_WIKIDATA = """
SELECT ?zasnovano ?misto ~?mistoLabel ?sajt ?koordynaty WHERE {
  wd:Q84151 wdt:P571 ?zasnovano .
  OPTIONAL { wd:Q84151 wdt:P131 ?misto . }
  OPTIONAL { wd:Q84151 wdt:P856 ?sajt . }
  OPTIONAL { wd:Q84151 wdt:P625 ?koordynaty . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "uk,en". }
}
LIMIT 1
""".replace("~", "")


def zavantazhyty_z_wikidata(g: Graph) -> int:
    """Тягне властивості університету з Wikidata і вливає їх у граф."""
    sparql = SPARQLWrapper(ENDPOINT, agent=USER_AGENT)
    sparql.setQuery(ZAPYT_WIKIDATA)
    sparql.setReturnFormat(JSON)
    dani = sparql.query().convert()

    knu_wd = URIRef(d.WIKIDATA["universytet"])
    dodano = 0
    for row in dani["results"]["bindings"]:
        if "zasnovano" in row:
            g.add((knu_wd, WDT.P571, Literal(row["zasnovano"]["value"][:10],
                                             datatype=XSD.date))); dodano += 1
        if "misto" in row:
            misto = URIRef(row["misto"]["value"])
            g.add((knu_wd, WDT.P131, misto)); dodano += 1
            if "mistoLabel" in row:
                g.add((misto, RDFS.label, Literal(row["mistoLabel"]["value"], lang="uk")))
                dodano += 1
        if "sajt" in row:
            g.add((knu_wd, WDT.P856, Literal(row["sajt"]["value"], datatype=XSD.anyURI)))
            dodano += 1
        if "koordynaty" in row:
            g.add((knu_wd, WDT.P625, Literal(row["koordynaty"]["value"]))); dodano += 1
    return dodano


OBIEDNANYI_ZAPYT = """
PREFIX onp:  <https://example.org/onp/>
PREFIX sdo:  <https://schema.org/>
PREFIX owl:  <http://www.w3.org/2002/07/owl#>
PREFIX wdt:  <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

# Дані власного графу (програма, компоненти, кредити) поєднані з даними
# Wikidata (рік заснування, місто, офіційний сайт університету).
SELECT ?universytet ?zasnovano ?misto (COUNT(?k) AS ?komponentiv)
       (SUM(?kredyty) AS ?kredytiv)
WHERE {
  ?u a onp:Universytet ;
     sdo:name ?universytet ;
     owl:sameAs ?wd .
  ?wd wdt:P571 ?zasnovano .
  OPTIONAL { ?wd wdt:P131 ?m . ?m rdfs:label ?misto . }

  ?prog a onp:OsvitnyaPrograma ; sdo:hasCourse ?k .
  ?k onp:vydKomponenta "обов'язковий"@uk ;
     sdo:numberOfCredits ?kredyty .
  FILTER (lang(?universytet) = "uk")
}
GROUP BY ?universytet ?zasnovano ?misto
"""

# Демонстрація SERVICE (виконується всередині rdflib; на Wikidata часто дає 403
# через зашитий user-agent — показуємо як ілюстрацію обмеження реалізації).
SERVICE_DEMO = """
PREFIX onp: <https://example.org/onp/>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>

SELECT ?wd ?zasnovano WHERE {
  ?u a onp:Universytet ; owl:sameAs ?wd .
  SERVICE <https://query.wikidata.org/sparql> {
    ?wd wdt:P571 ?zasnovano .
  }
}
"""


if __name__ == "__main__":
    g = Graph(); g.parse("onp.ttl", format="turtle")
    print(f"локальний граф: {len(g)} трійок")
    try:
        n = zavantazhyty_z_wikidata(g)
        print(f"додано з Wikidata: {n} трійок -> разом {len(g)}")
        print("\nОб'єднаний запит:")
        for row in g.query(OBIEDNANYI_ZAPYT):
            print("  " + " | ".join(str(v) for v in row))
        g.serialize("onp_z_wikidata.ttl", format="turtle")
    except Exception as e:
        print(f"Wikidata недоступна ({type(e).__name__}): {e}")
