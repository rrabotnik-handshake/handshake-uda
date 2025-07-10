from rdflib import Graph, Namespace, RDF, RDFS, URIRef

# Load the RDF data
g = Graph()
g.parse("../rdf/upper.ttl", format="turtle")
g.parse("../rdf/handshake_domain.ttl", format="turtle")

UPPER = Namespace("https://rdf.joinhandshake.com/upper#")
DOM = Namespace("https://rdf.joinhandshake.com/domain#")

# List all DirectClasses (entities)
print("Entities:")
for s in g.subjects(RDF.type, UPPER.DirectClass):
    label = g.value(s, RDFS.label)
    print(f"  • {s.split('#')[-1]} – {label}")

# List fields (upper:property) for each entity
print("\nEntity Fields:")
for entity in g.subjects(RDF.type, UPPER.DirectClass):
    label = g.value(entity, RDFS.label)
    print(f"{label}:")
    for _, _, field in g.triples((entity, UPPER.property, None)):
        flabel = g.value(field, RDFS.label) or "<no label>"
        ftype = g.value(field, RDF.type)
        ftype_str = ftype.split("#")[-1] if ftype else "UnknownType"

        print(f"  - {flabel} ({ftype_str})")

        if flabel == "<no label>" or ftype is None:
            print(f"    ⚠️  Incomplete definition for {field}")
