import os
import subprocess
from rdflib import Graph, Namespace, RDF, RDFS, OWL
from collections import defaultdict
import re
import importlib.resources

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RDF_DIR = os.path.abspath(os.path.join(BASE_DIR, "./rdf"))
PROTO_DIR = os.path.abspath(os.path.join(
    BASE_DIR, "proto/handshake/v1"))
PROTO_FILENAME = "handshake_domain.proto"
GOOGLE_PROTO_DIR = importlib.resources.files("grpc_tools").joinpath("_proto")

print(BASE_DIR)
print(RDF_DIR)
print(PROTO_DIR)
print(PROTO_FILENAME)
print(GOOGLE_PROTO_DIR)


# Load RDF
g = Graph()
g.parse(os.path.join(RDF_DIR, "upper.ttl"), format="turtle")
g.parse(os.path.join(RDF_DIR, "handshake_domain.ttl"), format="turtle")

# Namespaces
UPPER = Namespace("https://rdf.joinhandshake.com/upper#")

# Utils


def local_name(uri):
    return uri.split("#")[-1]


def to_upper_snake_case(value):
    if not value:
        return ""
    s = re.sub(r"[-.\s]", "_", value)
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", s)
    s = s.upper()
    s = re.sub(r"__+", "_", s)
    return s.strip("_")


def to_pascal_case(value):
    parts = re.split(r'[_\s-]', value)
    return ''.join(word.capitalize() for word in parts if word)


def to_snake_case(value):
    return re.sub(r'(?<!^)(?=[A-Z])', '_', value).lower()


proto_lines = [
    'syntax = "proto3";',
    'package handshake.v1;',
    'option java_multiple_files = true;',
    ''
]

# Enums
enums = {}
for enum_class in g.subjects(RDF.type, UPPER.Enumeration):
    name = to_pascal_case(local_name(enum_class))
    values = [(f"{name.upper()}_UNSPECIFIED", "Default unspecified value")]
    for member in g.subjects(RDF.type, enum_class):
        label = g.value(member, RDFS.label)
        values.append(
            (f"{name.upper()}_{to_upper_snake_case(local_name(member))}", label))
    enums[name] = values

for enum_class in g.subjects(OWL.oneOf, None):
    name = to_pascal_case(local_name(enum_class))
    collection = g.value(enum_class, OWL.oneOf)
    values = [(f"{name.upper()}_UNSPECIFIED", "Default unspecified value")]
    for member in g.items(collection):
        label = g.value(member, RDFS.label)
        values.append(
            (f"{name.upper()}_{to_upper_snake_case(local_name(member))}", label))
    enums[name] = values

for name, values in enums.items():
    proto_lines.append(f"enum {name} {{")
    for idx, (val, label) in enumerate(values):
        if label:
            proto_lines.append(f"  // {label}")
        proto_lines.append(f"  {val} = {idx};")
    proto_lines.append("}\n")

# Entities
entities = {}
dependencies = defaultdict(set)

for s in g.subjects(RDF.type, UPPER.DirectClass):
    name = local_name(s)
    entities[name] = s
    for p in g.objects(s, UPPER.property):
        if (p, RDF.type, UPPER.Relationship) in g:
            target = g.value(p, UPPER["class"])
            if target:
                dependencies[name].add(local_name(target))

# Topological sort
visited = set()
sorted_entities = []


def visit(n):
    if n in visited:
        return
    visited.add(n)
    for dep in dependencies.get(n, []):
        visit(dep)
    sorted_entities.append(n)


for name in entities:
    visit(name)

requires_timestamp = False
requires_validation_import = False


def map_xsd_to_proto(xsd_type):
    global requires_timestamp
    suffix = xsd_type.split("#")[-1]
    mapping = {
        "string": "string",
        "int": "int32",
        "integer": "int64",
        "float": "float",
        "double": "double",
        "boolean": "bool",
        "gYear": "int32",
        "date": "string",
        "dateTime": "google.protobuf.Timestamp"
    }
    if suffix == "dateTime":
        requires_timestamp = True
    return mapping.get(suffix, "string")


# Emit messages
for entity_name in reversed(sorted_entities):
    proto_lines.append(f"message {entity_name} {{")
    fields = list(g.objects(entities[entity_name], UPPER.property))
    grouped = defaultdict(list)
    for f in fields:
        grouped[str(g.value(f, UPPER.group) or "General")].append(f)
    idx = 1
    for group in sorted(grouped):
        proto_lines.append(f"\n  // === {group} ===")
        for f in grouped[group]:
            label = g.value(f, RDFS.label)
            comment = g.value(f, RDFS.comment)
            if label:
                proto_lines.append(f"  // {label}")
            if comment:
                proto_lines.append(f"  // {comment}")
            min_count = g.value(f, UPPER.minCount)
            max_count = g.value(f, UPPER.maxCount)
            modifier = "repeated" if str(max_count) == "-1" else "optional"
            dtype = g.value(f, UPPER.datatype)
            if dtype and local_name(dtype) in enums:
                f_type = local_name(dtype)
            elif (f, RDF.type, UPPER.Attribute) in g:
                f_type = map_xsd_to_proto(str(dtype)) if dtype else "string"
            elif (f, RDF.type, UPPER.Relationship) in g:
                f_type = local_name(g.value(f, UPPER["class"])) or "string"
            else:
                f_type = "string"
            options = []
            if (f, RDF.type, UPPER.Deprecated) in g:
                options.append("deprecated = true")
            if f_type == "string":
                if g.value(f, UPPER.minLength):
                    requires_validation_import = True
                    options.append(
                        f"(buf.validate.field).string.min_len = {g.value(f, UPPER.minLength)}")
                if g.value(f, UPPER.maxLength):
                    requires_validation_import = True
                    options.append(
                        f"(buf.validate.field).string.max_len = {g.value(f, UPPER.maxLength)}")
                if g.value(f, UPPER.pattern):
                    requires_validation_import = True
                    options.append(
                        f"(buf.validate.field).string.pattern = \"{g.value(f, UPPER.pattern)}\"")
            elif f_type in {"int32", "int64"}:
                if g.value(f, UPPER.minInclusive):
                    requires_validation_import = True
                    options.append(
                        f"(buf.validate.field).{f_type}.gte = {g.value(f, UPPER.minInclusive)}")
                if g.value(f, UPPER.maxInclusive):
                    requires_validation_import = True
                    options.append(
                        f"(buf.validate.field).{f_type}.lte = {g.value(f, UPPER.maxInclusive)}")
            option_str = f" [{', '.join(options)}]" if options else ""
            proto_lines.append(
                f"  {modifier} {f_type} {to_snake_case(local_name(f))} = {idx}{option_str};")
            idx += 1
    proto_lines.append("}\n")

# Add imports
insertion_index = 3
if requires_timestamp:
    proto_lines.insert(
        insertion_index, 'import "google/protobuf/timestamp.proto";')
    insertion_index += 1
if requires_validation_import:
    proto_lines.insert(
        insertion_index, 'import "buf/validate/validate.proto";')

# Write proto file
os.makedirs(PROTO_DIR, exist_ok=True)
proto_path = os.path.join(PROTO_DIR, PROTO_FILENAME)
with open(proto_path, "w") as f:
    f.write("\n".join(proto_lines))

# Generate code via buf
subprocess.run([
    "buf", "generate", "--path", f"proto/handshake/v1/{PROTO_FILENAME}"
], check=True)

print("✅ .proto generation and code output via buf complete.")
