"""Побудова RDF-графу освітньо-наукової програми (ЛР №1)."""

from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, OWL, XSD, FOAF, DCTERMS, SKOS

import onp_data as d

BASE = "https://pryanikalenaknu.github.io/semantic-web-lab1/onp/"
ONP = Namespace(BASE)
SDO = Namespace("https://schema.org/")     # Schema.org — саме https, не http
ORG = Namespace("http://www.w3.org/ns/org#")
WD = Namespace("http://www.wikidata.org/entity/")


def build() -> Graph:
    g = Graph()
    for p, ns in [("onp", ONP), ("sdo", SDO), ("org", ORG), ("wd", WD),
                  ("foaf", FOAF), ("dcterms", DCTERMS), ("skos", SKOS), ("owl", OWL)]:
        g.bind(p, ns)

    dzherelo = Literal(d.DZHERELO, lang="uk")

    knu, fit, pst = ONP["KNU"], ONP["FIT"], ONP["kafedra-PST"]

    g.add((knu, RDF.type, SDO.CollegeOrUniversity))
    g.add((knu, RDF.type, ONP.Universytet))
    g.add((knu, SDO.name, Literal("Київський національний університет імені Тараса Шевченка", lang="uk")))
    g.add((knu, SDO.name, Literal("Taras Shevchenko National University of Kyiv", lang="en")))
    g.add((knu, SDO.url, Literal("https://knu.ua", datatype=XSD.anyURI)))

    g.add((fit, RDF.type, ONP.Fakultet))
    g.add((fit, RDF.type, ORG.OrganizationalUnit))
    g.add((fit, SDO.name, Literal("Факультет інформаційних технологій", lang="uk")))
    g.add((fit, ORG.subOrganizationOf, knu))

    g.add((pst, RDF.type, ONP.Kafedra))
    g.add((pst, RDF.type, ORG.OrganizationalUnit))
    g.add((pst, SDO.name, Literal("Кафедра програмних систем і технологій", lang="uk")))
    g.add((pst, SDO.url, Literal(d.PROGRAMA["sajt"], datatype=XSD.anyURI)))
    g.add((pst, ORG.subOrganizationOf, fit))

    prog = ONP["programa-F2-mahistr"]
    g.add((prog, RDF.type, SDO.EducationalOccupationalProgram))
    g.add((prog, RDF.type, ONP.OsvitnyaPrograma))
    g.add((prog, DCTERMS.title, Literal(d.PROGRAMA["nazva_spec"], lang="uk")))
    g.add((prog, SDO.name, Literal(d.PROGRAMA["nazva_spec"], lang="uk")))
    g.add((prog, ONP.kodSpecialnosti, Literal(d.PROGRAMA["kod_spec"])))
    g.add((prog, ONP.galuzZnan, Literal(d.PROGRAMA["galuz"], lang="uk")))
    g.add((prog, ONP.osvitniyRiven, Literal(d.PROGRAMA["riven"], lang="uk")))
    g.add((prog, ONP.typProgramy, Literal(d.PROGRAMA["typ"], lang="uk")))
    g.add((prog, SDO.numberOfCredits, Literal(d.PROGRAMA["kredyty"], datatype=XSD.integer)))
    g.add((prog, SDO.timeToComplete, Literal("P2Y", datatype=XSD.duration)))
    g.add((prog, ONP.akredytacia, Literal(d.PROGRAMA["akredytacia"], lang="uk")))
    g.add((prog, ONP.realizuietsyaKafedroyu, pst))
    g.add((prog, DCTERMS.source, dzherelo))

    for key, nazva in d.FORMY.items():
        f = ONP[f"forma-{key}"]
        g.add((f, RDF.type, ONP.FormaKontrolyu))
        g.add((f, RDF.type, SKOS.Concept))
        g.add((f, SKOS.prefLabel, Literal(nazva, lang="uk")))

    for kod, (typ, tekst) in d.KOMPETENTNOSTI.items():
        k = ONP[f"kompetentnist-{kod}"]
        g.add((k, RDF.type, ONP.Kompetentnist))
        g.add((k, RDF.type, SKOS.Concept))
        g.add((k, SKOS.notation, Literal(kod)))
        g.add((k, SKOS.prefLabel, Literal(tekst, lang="uk")))
        g.add((k, ONP.typKompetentnosti, Literal(typ, lang="uk")))
        g.add((k, DCTERMS.source, dzherelo))

    for kod, tekst in d.PRN.items():
        r = ONP[f"rezultat-{kod}"]
        g.add((r, RDF.type, ONP.RezultatNavchannya))
        g.add((r, RDF.type, SKOS.Concept))
        g.add((r, SKOS.notation, Literal(kod.replace("_", "."))))
        g.add((r, SKOS.prefLabel, Literal(tekst, lang="uk")))
        g.add((r, DCTERMS.source, dzherelo))
        for kk in d.PRN_KOMPETENTNIST.get(kod, []):
            g.add((r, ONP.spyraietsyaNaKompetentnist, ONP[f"kompetentnist-{kk}"]))

    for kod, (nazva, kredyty, forma, vyd) in d.KOMPONENTY.items():
        c = ONP[f"komponent-{kod}"]
        g.add((c, RDF.type, SDO.Course))
        g.add((c, RDF.type, ONP.OsvitniyKomponent))
        g.add((c, SDO.courseCode, Literal(kod)))
        g.add((c, SDO.name, Literal(nazva, lang="uk")))
        g.add((c, DCTERMS.title, Literal(nazva, lang="uk")))
        if kod in d.NAZVY_EN:
            g.add((c, SDO.name, Literal(d.NAZVY_EN[kod], lang="en")))
        g.add((c, SDO.numberOfCredits, Literal(kredyty, datatype=XSD.integer)))
        g.add((c, ONP.vydKomponenta, Literal(vyd, lang="uk")))
        g.add((c, DCTERMS.source, dzherelo))
        if forma:
            g.add((c, ONP.maieFormuKontrolyu, ONP[f"forma-{forma}"]))
        g.add((prog, SDO.hasCourse, c))
        for kk in d.KOMPONENT_KOMPETENTNIST.get(kod, []):
            g.add((c, ONP.formuieKompetentnist, ONP[f"kompetentnist-{kk}"]))
        for rr in d.KOMPONENT_PRN.get(kod, []):
            g.add((c, ONP.zabezpechuieRezultat, ONP[f"rezultat-{rr}"]))

    grupa = ONP[f"grupa-{d.GRUPA['kod']}"]
    g.add((grupa, RDF.type, FOAF.Group))
    g.add((grupa, RDF.type, ONP.Grupa))
    g.add((grupa, SDO.name, Literal(d.GRUPA["kod"], lang="uk")))
    g.add((grupa, ONP.navchaietsyaZaProgramoyu, prog))
    g.add((grupa, ONP.kilkistStudentiv, Literal(d.GRUPA["kilkist_studentiv"], datatype=XSD.integer)))

    for n in d.GRUPA["pidgrupy"]:
        sg = ONP[f"pidgrupa-{n}"]
        g.add((sg, RDF.type, FOAF.Group))
        g.add((sg, RDF.type, ONP.Pidgrupa))
        g.add((sg, SDO.name, Literal(f"{d.GRUPA['kod']}, підгрупа {n}", lang="uk")))
        g.add((sg, ONP.nomerPidgrupy, Literal(n, datatype=XSD.integer)))
        g.add((sg, ORG.subOrganizationOf, grupa))

    for sid, imia, sub in d.STUDENTY:
        s = ONP[f"student-{sid}"]
        g.add((s, RDF.type, FOAF.Person))
        g.add((s, RDF.type, ONP.Student))
        g.add((s, FOAF.name, Literal(imia, lang="uk")))
        g.add((s, ONP.nalezhytPidgrupi, ONP[f"pidgrupa-{sub}"]))

    g.add((knu, OWL.sameAs, URIRef(d.WIKIDATA["universytet"])))

    return g


if __name__ == "__main__":
    g = build()
    g.serialize("onp.ttl", format="turtle")
    g.serialize("onp.jsonld", format="json-ld", auto_compact=True, indent=2)

    typy = set(g.objects(None, RDF.type))
    vlasni = {t for t in typy if str(t).startswith(BASE)}
    ekz = {s for s in g.subjects(RDF.type, None)}
    predykaty = set(g.predicates(None, None))
    vlasni_pred = {p for p in predykaty if str(p).startswith(BASE)}

    print(f"трійок:              {len(g)}")
    print(f"типів сутностей:     {len(vlasni)}  (власних)")
    print(f"екземплярів:         {len(ekz)}")
    print(f"типів зв'язків:      {len(vlasni_pred)} власних + повторно вжиті словники")
    print(f"усіх предикатів:     {len(predykaty)}")
    print("\nвласні типи:", ", ".join(sorted(str(t).replace(BASE, "") for t in vlasni)))
