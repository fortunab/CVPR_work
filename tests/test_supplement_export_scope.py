"""Integration fixtures for exporting the original supplement from unified reports.

These small invented values test encoder selection, not the paper's results.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from export_review_supplement import export
from export_review_tables import HEADS
from review_protocol import write_csv, write_json


ORIGINAL_TASKS = ("polypgen_resnet18", "polypgen_dinov2", "camelyon_resnet18")
FOUNDATION_TASKS = ("camelyon_custom_conch", "camelyon_custom_uni")


def report_fixture(root, include_foundation_contrasts):
    report, aggregates, stability = (root / name for name in ("report", "aggregate", "stability"))
    tasks = ORIGINAL_TASKS + FOUNDATION_TASKS if include_foundation_contrasts else ORIGINAL_TASKS
    uncertainty = {"ci_low": -.1, "ci_high": .1, "valid_draws": 50}
    write_csv(report / "factorial_ranking_contrasts.csv", [
        {"task": "polypgen_resnet18", "center": "C5", "K": 4, "metric": "across_auc",
         "beta1_minus_beta0": -.02, **uncertainty}])
    write_csv(report / "factorial_ba_interactions.csv", [
        {"task": task, "center": "equal_center_mean", "interaction": .01, **uncertainty}
        for task in tasks])
    write_csv(report / "protocol_sensitivity_intervals.csv", [
        {"task": task, "center": "equal_center_mean", "method": "cbmp",
         "matched4_minus_historical": .01, **uncertainty} for task in tasks])
    sequence, patients = [], []
    for protocol in ("historical", "matched4"):
        for method in HEADS:
            for task in ORIGINAL_TASKS[:2]:
                for center in ("C4", "C5", "C6"):
                    sequence.append({"task": task, "protocol": protocol, "method": method,
                                     "center": center, "balanced_accuracy": .7, "auroc": .75})
            # Foundation rows deliberately precede ResNet18. Row order must not
            # silently change the encoder used by the original supplement.
            for task in FOUNDATION_TASKS + ("camelyon_resnet18",):
                value = .81 if task == "camelyon_resnet18" else .96
                for center in ("2", "1"):
                    patients.append({"task": task, "protocol": protocol, "method": method,
                                     "center": center, "balanced_accuracy": value, "auroc": value})
    write_csv(report / "sequence_metrics_seed_means.csv", sequence)
    write_csv(report / "patient_macro_seed_means.csv", patients)
    write_csv(aggregates / "paired_aggregate_intervals.csv", [
        {"task": task, "protocol": "historical", "center": "equal_center_mean",
         "comparison": "cbmp_minus_trainable_cosine" if task == "polypgen_dinov2"
         else "cbmp_minus_linear_logistic", "metric": "balanced_accuracy",
         "difference": -.01, **uncertainty} for task in tasks])
    write_csv(stability / "prototype_stability_summary.csv", [
        {"task": "polypgen_resnet18", "center": "C5", "protocol": "historical", "method": "cbmp",
         "class": 0, "comparable_pairs": 45, "mean_matched_cosine": .99,
         "min_pair_mean_cosine": .98}])
    for folder in (report, aggregates, stability):
        write_json(folder / "provenance.json", {"scope": "synthetic exporter regression fixture"})
    return report, aggregates, stability


def test_original_patient_table_uses_resnet18_even_when_foundation_rows_come_first(tmp_path):
    paths = report_fixture(tmp_path, include_foundation_contrasts=False)
    output = tmp_path / "tables"
    export(*paths, output)
    text = (output / "review_group_endpoints.tex").read_text(encoding="utf-8")
    expected = "CBMP & 81.00 & 81.00 & 81.00 & 81.00"
    assert text.count(expected) == 2
    assert "96.00" not in text


def test_original_supplement_accepts_a_unified_five_task_report(tmp_path):
    paths = report_fixture(tmp_path, include_foundation_contrasts=True)
    output = tmp_path / "tables"
    export(*paths, output)
    assert len(list(output.glob("*.tex"))) == 6
    interactions = (output / "review_ba_interactions.tex").read_text(encoding="utf-8")
    assert "Histology & Mean" in interactions
    assert "camelyon_custom" not in interactions
    patient_text = (output / "review_group_endpoints.tex").read_text(encoding="utf-8")
    assert "96.00" not in patient_text
