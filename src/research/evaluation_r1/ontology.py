"""Machine-readable project ontology, independent of any dataset loader."""
import json
from pathlib import Path
from . import DOMAINS, SCHEMA_VERSION


def load_ontology():
    value = json.loads(Path(__file__).with_name("ontology.json").read_text(encoding="utf-8"))
    if value["schema_version"] != SCHEMA_VERSION or set(value["domains"]) != set(DOMAINS):
        raise ValueError("ontology schema/domain drift")
    return value


def domain_schema(domain):
    ontology = load_ontology()
    if domain not in ontology["domains"]:
        raise ValueError("unknown domain")
    return {"schema_version": SCHEMA_VERSION, "domain": domain,
            "task_id": ontology["domains"][domain]["task_id"], "segmentation": "binary",
            "classes": {0: "background", 1: ontology["domains"][domain]["foreground"]},
            "annotated_subclasses": "NOT_AVAILABLE"}
