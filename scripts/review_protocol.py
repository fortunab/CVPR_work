"""Shared protocol and validation for the approved cached-feature revision."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "src"
sys.path.insert(0, str(CORE))
from cbmp_data import load_manifest
from cbmp_evaluation import candidate_methods


SEEDS = (17, 29, 43, 61, 89, 101, 131, 173, 211, 257)
TASKS = ("polypgen_resnet18", "polypgen_dinov2", "camelyon_resnet18", "camelyon_custom_uni", "camelyon_custom_conch")


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def write_csv(path, records):
    if not records:
        raise ValueError("Cannot write an empty result table")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    temporary.replace(path)


def grids(protocol):
    if protocol == "factorial":
        return {f"K{k}_beta{int(b)}": [{"kind": "prototype", "k": k, "beta": b}]
                for k in (1, 4) for b in (0.0, 1.0)}
    methods = candidate_methods()
    if protocol == "historical":
        return methods
    if protocol != "matched4":
        raise ValueError(f"Unknown candidate protocol: {protocol}")
    methods.update({
        "cbmp": [{"kind": "prototype", "k": k, "beta": b} for k in (1, 4) for b in (0.0, 1.0)],
        "linear_logistic": [{"kind": "linear", "C": c} for c in (0.1, 1.0, 10.0, 100.0)],
        "trainable_cosine": [{"kind": "cosine", "learning_rate": lr} for lr in (0.003, 0.01, 0.03, 0.1)],
        "linear_group_center_weighted": [
            {"kind": "linear", "C": c, "beta": b} for b in (0.0, 1.0) for c in (0.1, 10.0)
        ],
        "cosine_group_center_weighted": [
            {"kind": "cosine", "learning_rate": lr, "beta": b}
            for b in (0.0, 1.0) for lr in (0.01, 0.1)
        ],
    })
    return methods


def validate_splits(rows, splits):
    labels = np.array([r["label"] for r in rows], dtype=int)
    centers = np.array([r["center"] for r in rows])
    groups = np.array([r["group_id"] for r in rows])
    content = np.array([r.get("pixel_sha256") or r["sha256"] for r in rows])
    if len({r["sample_id"] for r in rows}) != len(rows):
        raise ValueError("Sample IDs must be unique")
    for split in splits:
        train = np.asarray(split["outer_train"], dtype=int)
        test = np.asarray(split["outer_test"], dtype=int)
        if (not len(train) or not len(test) or min(train.min(), test.min()) < 0
                or max(train.max(), test.max()) >= len(rows)
                or len(set(train)) != len(train) or len(set(test)) != len(test)):
            raise ValueError("Invalid outer row indices")
        if (set(train) & set(test) or set(groups[train]) & set(groups[test])
                or set(content[train]) & set(content[test])
                or np.any(centers[train] == split["heldout_center"])
                or not np.all(centers[test] == split["heldout_center"])):
            raise ValueError("Source/target group, center, or content leakage")
        if set(labels[train]) != {0, 1} or set(labels[test]) != {0, 1}:
            raise ValueError("Outer training and target must each contain both classes")
        for inner in split["inner_folds"]:
            fit, validation = map(lambda key: np.asarray(inner[key], dtype=int), ("train", "validation"))
            if (not len(fit) or not len(validation) or set(fit) & set(validation)
                    or not (set(fit) | set(validation)) <= set(train)
                    or set(groups[fit]) & set(groups[validation])
                    or set(content[fit]) & set(content[validation])):
                raise ValueError("Invalid source-validation boundary")
            if set(labels[fit]) != {0, 1} or set(labels[validation]) != {0, 1}:
                raise ValueError("Source fold must retain both classes")


def load_cached_task(task):
    """Load a registered portable task, never an implicit experiment folder."""
    from data_catalog import load_task
    return load_task(task)
