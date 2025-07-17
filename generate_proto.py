#!/usr/bin/env python3
import os
import subprocess
import argparse
import pathlib
import sys
import logging
from rdflib import Graph, Namespace, RDF, RDFS, OWL
from collections import defaultdict
import re
from rich.logging import RichHandler

# === Logging ===
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(markup=True)]
)

# === Constants and Paths ===
UPPER = Namespace("https://rdf.joinhandshake.com/upper#")

# === Helper Functions ===


def local_name(uri): return uri.split("#")[-1]


def to_upper_snake_case(value):
    s = re.sub(r"[-.\s]", "_", value or "")
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", s)
    return re.sub(r"__+", "_", s.upper()).strip("_")


def to_pascal_case(value):
    return ''.join(word.capitalize() for word in re.split(r'[_\s-]', value or "") if word)


def to_snake_case(value):
    return re.sub(r'(?<!^)(?=[A-Z])', '_', value or "").lower()


def is_safe_proto_path(proto_path: str = './gen/proto/uda/v1', root_dir: str = ".") -> bool:
    abs_root = pathlib.Path(root_dir).resolve()
    abs_path = pathlib.Path(proto_path).resolve()
    return abs_root in abs_path.parents and abs_path.suffix == ".proto"


def run_buf_generate(proto_path: str):
    try:
        subprocess.run(
            ["buf", "generate", "--path", proto_path],
            check=True
        )
        logging.info(f"✅ Buf codegen complete for: {proto_path}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Buf generation failed: {e}")
        sys.exit(1)


# === Main Codegen Logic ===
def generate_proto(rdf_dir: str, output_proto: str, run_buf: bool):
    rdf_dir = pathlib.Path(rdf_dir).resolve()
    proto_path = pathlib.Path(output_proto).resolve()
    proto_dir = proto_path.parent

    if not is_safe_proto_path(str(proto_path)):
        raise ValueError("Untrusted or invalid output path")

    # Load RDF
    g = Graph()
    g.parse(rdf_dir / "upper.ttl", format="turtle")
    g.parse(rdf_dir / "handshake_domain.ttl", format="turtle")

    proto_lines = ['syntax = "proto3";', 'package uda.v1;', '']
    enums = {}
    requires_timestamp = False
    requires_validation = False

    # Enums
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
    deps = defaultdict(set)
    for s in g.subjects(RDF.type, UPPER.DirectClass):
        name = local_name(s)
        entities[name] = s
        for p in g.objects(s, UPPER.property):
            if (p, RDF.type, UPPER.Relationship) in g:
                target = g.value(p, UPPER["class"])
                if target:
                    deps[name].add(local_name(target))

    # Topo sort
    visited = set()
    ordered = []

    def visit(n):
        if n in visited:
            return
        visited.add(n)
        for d in deps.get(n, []):
            visit(d)
        ordered.append(n)

    for name in entities:
        visit(name)

    def map_xsd_to_proto(xsd_type: str):
        nonlocal requires_timestamp
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

    # Messages
    for name in reversed(ordered):
        proto_lines.append(f"message {name} {{")
        fields = list(g.objects(entities[name], UPPER.property))
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
                    f_type = map_xsd_to_proto(
                        str(dtype)) if dtype else "string"
                elif (f, RDF.type, UPPER.Relationship) in g:
                    f_type = local_name(g.value(f, UPPER["class"])) or "string"
                else:
                    f_type = "string"

                options = []
                if (f, RDF.type, UPPER.Deprecated) in g:
                    options.append("deprecated = true")

                if f_type == "string":
                    if g.value(f, UPPER.minLength):
                        requires_validation = True
                        options.append(
                            f"(buf.validate.field).string.min_len = {int(str(g.value(f, UPPER.minLength)))}")
                    if g.value(f, UPPER.maxLength):
                        requires_validation = True
                        options.append(
                            f"(buf.validate.field).string.max_len = {int(str(g.value(f, UPPER.maxLength)))}")
                    if g.value(f, UPPER.pattern):
                        requires_validation = True
                        options.append(
                            f"(buf.validate.field).string.pattern = \"{g.value(f, UPPER.pattern)}\"")
                elif f_type in {"int32", "int64"}:
                    if g.value(f, UPPER.minInclusive):
                        requires_validation = True
                        options.append(
                            f"(buf.validate.field).{f_type}.gte = {int(str(g.value(f, UPPER.minInclusive)))}")
                    if g.value(f, UPPER.maxInclusive):
                        requires_validation = True
                        options.append(
                            f"(buf.validate.field).{f_type}.lte = {int(str(g.value(f, UPPER.maxInclusive)))}")

                if str(min_count) and int(str(min_count)) >= 1:
                    requires_validation = True
                    if modifier == "repeated":
                        options.append(
                            "(buf.validate.field).repeated.min_items = 1")
                    else:
                        options.append("(buf.validate.field).required = true")

                opt_str = f" [{', '.join(options)}]" if options else ""
                proto_lines.append(
                    f"  {modifier} {f_type} {to_snake_case(local_name(f))} = {idx}{opt_str};")
                idx += 1
        proto_lines.append("}\n")

    # Imports
    insertion = 3
    if requires_timestamp:
        proto_lines.insert(
            insertion, 'import "google/protobuf/timestamp.proto";')
        insertion += 1
    if requires_validation:
        proto_lines.insert(
            insertion, 'import "buf/validate/validate.proto";')

    # Output proto file
    os.makedirs(proto_dir, exist_ok=True)
    with open(proto_path, "w") as f:
        f.write("\n".join(proto_lines))

    logging.info(f"✅ Wrote .proto file to: {proto_path}")

    if run_buf:
        run_buf_generate(str(proto_path))


# === CLI Entrypoint ===
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate protobuf schema from RDF + run buf codegen.")
    parser.add_argument("--rdf-dir", type=str, default="./rdf",
                        help="Directory containing .ttl RDF files")
    parser.add_argument("--output", type=str, default="./gen/proto/uda/v1/handshake_domain.proto",
                        help="Path to generated .proto file")
    parser.add_argument("--generate", default=True,
                        help="Run buf generate after writing .proto")
    args = parser.parse_args()

    try:
        generate_proto(args.rdf_dir, args.output, args.generate)
    except Exception as e:
        logging.exception(f"Codegen failed: {e}")
        sys.exit(1)
