"""Orchestration checks; these small fixtures do not establish scientific reproduction."""
import csv
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('reviewer_entry', Path(__file__).resolve().parents[1] / 'reproduce.py')
entry = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(entry)


class ReviewerEntryTests(unittest.TestCase):
    def test_conda_dispatch_preserves_prefix_spaces_and_uses_conda_run(self):
        state = {'manager': 'conda', 'conda': ['base python', '-m', 'conda'], 'profiles': {'heads': 'prefix with spaces'}}
        command = entry.interpreter_command(state, 'heads', 'scripts/run_experiments.py', '--help')
        self.assertEqual(command, ['base python', '-m', 'conda', 'run', '--no-capture-output', '--prefix',
                                   'prefix with spaces', 'python', 'scripts/run_experiments.py', '--help'])

    def test_full_export_gate_requires_complete_five_task_ten_seed_grid(self):
        complete = {'tasks': entry.TASKS, 'seeds': entry.SEEDS, 'protocols': entry.PROTOCOLS, 'completed_jobs': 50}
        self.assertTrue(entry.is_full_study(entry.TASKS, entry.SEEDS, complete))
        self.assertFalse(entry.is_full_study(entry.TASKS[:1], entry.SEEDS, complete))
        self.assertFalse(entry.is_full_study(entry.TASKS, [17], complete))
        self.assertFalse(entry.is_full_study(entry.TASKS, entry.SEEDS, dict(complete, completed_jobs=49)))

    def test_existing_outputs_are_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary) / 'existing'
            out.mkdir()
            marker = out / 'keep.txt'
            marker.write_text('keep')
            with self.assertRaises(FileExistsError):
                entry.reserve_output(out, False)
            self.assertEqual(marker.read_text(), 'keep')
            self.assertEqual(entry.reserve_output(out, True), out.resolve())

    def test_partial_run_recomputes_report_and_does_not_call_full_exporters(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(entry, 'ROOT', Path(temporary)):
            root = Path(temporary)
            (root / 'configs').mkdir()
            (root / 'configs/tasks.json').write_text(json.dumps({'tasks': {'polypgen_resnet18': {'features': 'features.npz'}}}))
            features = root / 'features'
            features.mkdir()
            (features / 'features.npz').write_bytes(b'orchestration fixture only')
            (root / 'results/paper').mkdir(parents=True)
            row = {'task': 'polypgen_resnet18', 'protocol': 'historical', 'center': 'C5', 'method': 'cbmp',
                   **{m: 0.8 for m in entry.METRICS}}
            for name in ['original_image_metrics.csv', 'histology_image_metrics.csv']:
                with (root / 'results/paper' / name).open('w', newline='') as stream:
                    writer = csv.DictWriter(stream, fieldnames=list(row))
                    writer.writeheader()
                    writer.writerow(row)
            args = entry.parser().parse_args(['run', '--features', str(features), '--output', str(root / 'out'),
                                               '--tasks', 'polypgen_resnet18', '--seeds', '17'])
            calls = []
            def runtime(state, profile, script, *arguments, env=None):
                calls.append(script)
                self.assertEqual(script, 'scripts/run_experiments.py')
                run = root / 'out/runs'
                run.mkdir()
                (run / 'run_manifest.json').write_text('{}')
                (run / 'COMPLETE.json').write_text(json.dumps({'tasks': args.tasks, 'seeds': args.seeds,
                                                               'protocols': entry.PROTOCOLS, 'completed_jobs': 1}))
                self.assertEqual(Path(env['CBMP_FEATURE_DIR']), features.resolve())
            stages = []
            def report_stage(state, script, destination, options, proof, env):
                stages.append(script)
                self.assertEqual(script, 'report_review_revision.py')
                destination.mkdir()
                with (destination / 'image_metrics_seed_means.csv').open('w', newline='') as stream:
                    writer = csv.DictWriter(stream, fieldnames=list(row))
                    writer.writeheader()
                    writer.writerow(dict(row, balanced_accuracy=0.7))
            state = {'manager': 'venv', 'profiles': {'heads': str(root / 'heads')}}
            with patch.object(entry, 'runtime', runtime), patch.object(entry, 'stage_output', report_stage):
                entry.run_study(args, state)
            self.assertEqual(calls, ['scripts/run_experiments.py'])
            self.assertEqual(stages, ['report_review_revision.py'])
            comparison = json.loads((root / 'out/comparison.json').read_text())
            self.assertFalse(comparison['complete_five_task_ten_seed_study'])
            self.assertIn('not the full ten-seed estimate', comparison['partial_run_note'])
            self.assertAlmostEqual(comparison['maximum_absolute_difference']['balanced_accuracy'], 0.1)

    def test_missing_features_fail_before_reserving_outputs(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(entry, 'ROOT', Path(temporary)):
            root = Path(temporary)
            (root / 'configs').mkdir()
            (root / 'configs/tasks.json').write_text(json.dumps({'tasks': {'polypgen_resnet18': {'features': 'missing.npz'}}}))
            out = root / 'out'
            args = entry.parser().parse_args(['run', '--features', str(root), '--output', str(out),
                                               '--tasks', 'polypgen_resnet18', '--seeds', '17'])
            with self.assertRaisesRegex(FileNotFoundError, 'missing.npz'):
                entry.run_study(args, {'manager': 'venv', 'profiles': {'heads': 'prefix'}})
            self.assertFalse(out.exists())

    def test_resume_rejects_tampered_report_and_preserves_its_bytes(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(entry, 'ROOT', Path(temporary)):
            root = Path(temporary)
            (root / 'scripts').mkdir()
            (root / 'scripts/report_review_revision.py').write_text('fixture reporter')
            upstream = root / 'run_manifest.json'
            upstream.write_text('{"completed": true}')
            report = root / 'report'
            calls = []
            def make_report(state, profile, script, *options, env=None):
                calls.append(script)
                report.mkdir()
                (report / 'provenance.json').write_text(json.dumps({'run_manifest_sha256': entry.digest(upstream)}))
                (report / 'image_metrics_seed_means.csv').write_text('balanced_accuracy\n0.8\n')
            arguments = ({}, 'report_review_revision.py', report, ['--run-dir', root / 'runs'],
                         {'run_manifest_sha256': upstream}, {})
            with patch.object(entry, 'runtime', make_report):
                entry.stage_output(*arguments)
                entry.stage_output(*arguments)
                self.assertEqual(len(calls), 1)
                changed = 'balanced_accuracy\n0.99\n'
                (report / 'image_metrics_seed_means.csv').write_text(changed)
                with self.assertRaisesRegex(ValueError, 'output content changed'):
                    entry.stage_output(*arguments)
                self.assertEqual((report / 'image_metrics_seed_means.csv').read_text(), changed)
                self.assertEqual(len(calls), 1)

    def test_full_comparison_checks_sd_and_rejects_missing_valid_seed(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(entry, 'ROOT', Path(temporary)):
            root = Path(temporary)
            (root / 'results/paper').mkdir(parents=True)
            report = root / 'output/report'
            report.mkdir(parents=True)
            expected = {'task': 'camelyon_custom_uni', 'protocol': 'matched4', 'center': '2',
                        'method': 'cbmp', 'fitting_seeds': 10}
            for metric in entry.METRICS:
                expected.update({metric: 0.8, metric + '_seed_sd': 0.01, metric + '_valid_seeds': 10})
            def save(path, row):
                with path.open('w', newline='') as stream:
                    writer = csv.DictWriter(stream, fieldnames=list(row))
                    writer.writeheader()
                    writer.writerow(row)
            for name in ['original_image_metrics.csv', 'histology_image_metrics.csv']:
                save(root / 'results/paper' / name, expected)
            changed = dict(expected, balanced_accuracy_seed_sd=0.03)
            save(report / 'image_metrics_seed_means.csv', changed)
            result = entry.compare_report(report, True)
            self.assertEqual(result['maximum_absolute_difference']['balanced_accuracy'], 0)
            self.assertAlmostEqual(result['maximum_absolute_seed_sd_difference']['balanced_accuracy'], 0.02)
            self.assertFalse(result['within_numerical_tolerance'])
            save(report / 'image_metrics_seed_means.csv', dict(expected, auroc_valid_seeds=9))
            with self.assertRaisesRegex(ValueError, 'valid-seed count differs'):
                entry.compare_report(report, True)


if __name__ == '__main__':
    unittest.main()
