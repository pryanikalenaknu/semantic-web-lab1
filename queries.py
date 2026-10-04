"""SPARQL-запити до графу ОНП (п.4 та п.6.6 лабораторної роботи)."""

from rdflib import Graph

PREFIXES = """
PREFIX onp:     <https://example.org/onp/>
PREFIX sdo:     <https://schema.org/>
PREFIX skos:    <http://www.w3.org/2004/02/skos/core#>
PREFIX org:     <http://www.w3.org/ns/org#>
PREFIX foaf:    <http://xmlns.com/foaf/0.1/>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX rdf:     <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
"""

Z1 = PREFIXES + """
# Q1. Які обов'язкові компоненти завершуються іспитом і скільки в них кредитів?
SELECT ?kod ?nazva ?kredyty WHERE {
  ?k a onp:OsvitniyKomponent ;
     sdo:courseCode ?kod ;
     sdo:name ?nazva ;
     sdo:numberOfCredits ?kredyty ;
     onp:vydKomponenta "обов'язковий"@uk ;
     onp:maieFormuKontrolyu ?f .
  ?f skos:prefLabel "іспит"@uk .
  FILTER (lang(?nazva) = "uk")
}
ORDER BY ?kod
"""

Z2 = PREFIXES + """
# Q2. Компоненти вагою понад 5 кредитів (демонстрація FILTER).
SELECT ?kod ?nazva ?kredyty WHERE {
  ?k sdo:courseCode ?kod ;
     sdo:name ?nazva ;
     sdo:numberOfCredits ?kredyty .
  FILTER (?kredyty > 5)
  FILTER (lang(?nazva) = "uk")
}
ORDER BY ?kod
"""

Z3 = PREFIXES + """
# Q3. Компоненти за спаданням кредитів (демонстрація сортування).
SELECT ?kod ?kredyty ?vyd WHERE {
  ?k sdo:courseCode ?kod ;
     sdo:numberOfCredits ?kredyty ;
     onp:vydKomponenta ?vyd .
}
ORDER BY DESC(?kredyty) ?kod
"""

Z4 = PREFIXES + """
# Q4. Скільки компонентів і кредитів припадає на кожну форму контролю
#     (агрегатні функції COUNT і SUM).
SELECT ?forma (COUNT(?k) AS ?kilkist) (SUM(?kredyty) AS ?vsogo_kredytiv) WHERE {
  ?k a onp:OsvitniyKomponent ;
     sdo:numberOfCredits ?kredyty ;
     onp:maieFormuKontrolyu ?f .
  ?f skos:prefLabel ?forma .
}
GROUP BY ?forma
ORDER BY DESC(?vsogo_kredytiv)
"""

Z5 = PREFIXES + """
# Q5. Через які компоненти студент підгрупи 2 виходить на компетентність СК11.
#     П'ять переходів: студент -> підгрупа -> група -> програма -> компонент -> компетентність.
SELECT DISTINCT ?student ?kod ?nazva WHERE {
  ?s a onp:Student ;
     foaf:name ?student ;
     onp:nalezhytPidgrupi ?pg .
  ?pg onp:nomerPidgrupy 2 ;
      org:subOrganizationOf ?grupa .
  ?grupa onp:navchaietsyaZaProgramoyu ?prog .
  ?prog sdo:hasCourse ?k .
  ?k sdo:courseCode ?kod ;
     sdo:name ?nazva ;
     onp:formuieKompetentnist ?komp .
  ?komp skos:notation "SK11" .
  FILTER (lang(?nazva) = "uk")
}
ORDER BY ?student ?kod
"""

Z6 = PREFIXES + """
# Q6 (додатковий). Які компоненти забезпечують ПРН20 і які компетентності
#     при цьому формуються — перехід через дві матриці ОНП.
SELECT ?kod ?kompetentnist WHERE {
  ?k sdo:courseCode ?kod ;
     onp:zabezpechuieRezultat ?r ;
     onp:formuieKompetentnist ?komp .
  ?r skos:notation "PRN20" .
  ?komp skos:notation ?kompetentnist .
}
ORDER BY ?kod ?kompetentnist
"""

ZAPYTY = [
    ("Q1. Обов'язкові компоненти з формою контролю «іспит»", Z1),
    ("Q2. Компоненти понад 5 кредитів (FILTER)", Z2),
    ("Q3. Компоненти за спаданням кредитів (сортування)", Z3),
    ("Q4. Кредити за формами контролю (COUNT, SUM, GROUP BY)", Z4),
    ("Q5. Шлях студент → підгрупа → група → програма → компонент → СК11", Z5),
    ("Q6. Компоненти, що забезпечують ПРН20, та їхні компетентності", Z6),
]

# П.6.6 — помилковий і виправлений приклад

POMYLKOVYI = PREFIXES + """
# ПОМИЛКА. Наміром було «усі обов'язкові компоненти та їхні викладачі».
# Викладач у графі є неоднорідним атрибутом: робочі програми доступні лише
# для частини компонент. Запит без OPTIONAL мовчки відкидає всі компоненти
# без викладача — замість 15 рядків повертається значно менше або жодного,
# і жодної помилки не виникає.
SELECT ?kod ?vykladach WHERE {
  ?k a onp:OsvitniyKomponent ;
     sdo:courseCode ?kod ;
     onp:vydKomponenta "обов'язковий"@uk ;
     onp:vykladach ?vykladach .
}
ORDER BY ?kod
"""

VYPRAVLENYI = PREFIXES + """
# ВИПРАВЛЕННЯ. Неоднорідний атрибут до графу не вноситься взагалі —
# джерелом істини для складу програми є ОНП, однакова для всіх компонент.
# Запит повертає всі 15 обов'язкових компонент.
SELECT ?kod ?nazva ?kredyty WHERE {
  ?k a onp:OsvitniyKomponent ;
     sdo:courseCode ?kod ;
     sdo:name ?nazva ;
     sdo:numberOfCredits ?kredyty ;
     onp:vydKomponenta "обов'язковий"@uk .
  FILTER (lang(?nazva) = "uk")
}
ORDER BY ?kod
"""


def vykonaty(g: Graph, nazva: str, zapyt: str, limit: int = 40) -> None:
    print("=" * 78)
    print(nazva)
    print("-" * 78)
    res = list(g.query(zapyt))
    for i, row in enumerate(res):
        if i >= limit:
            print(f"  … ще {len(res) - limit} рядків")
            break
        print("  " + " | ".join(str(v) for v in row))
    print(f"  [рядків: {len(res)}]\n")


if __name__ == "__main__":
    g = Graph()
    g.parse("onp.ttl", format="turtle")
    for nazva, z in ZAPYTY:
        vykonaty(g, nazva, z)
    vykonaty(g, "П.6.6 — ПОМИЛКОВИЙ запит", POMYLKOVYI)
    vykonaty(g, "П.6.6 — ВИПРАВЛЕНИЙ запит", VYPRAVLENYI)
