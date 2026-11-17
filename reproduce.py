"""Short reviewer entry point; the scientific scripts remain unchanged."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
TASKS = ['polypgen_resnet18', 'polypgen_dinov2', 'camelyon_resnet18', 'camelyon_custom_uni', 'camelyon_custom_conch']
SEEDS = [17, 29, 43, 61, 89, 101, 131, 173, 211, 257]
PROTOCOLS = ['historical', 'matched4', 'factorial']
METRICS = ['balanced_accuracy', 'auroc', 'macro_f1', 'negative_log_likelihood', 'brier_score']
PROFILES = ['heads', 'vision', 'pathology']


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def process_env(extra=None):
    env = os.environ.copy()
    env.pop('PYTHONPATH', None)
    env['PYTHONNOUSERSITE'] = '1'
    env.update(extra or {})
    return env


def execute(command, env=None):
    subprocess.run([str(x) for x in command], cwd=ROOT, env=process_env(env), check=True)


def load_state():
    path = ROOT / '.reproduce/state.json'
    if not path.is_file():
        raise RuntimeError('First run: python reproduce.py setup --manager venv (or conda).')
    return json.loads(path.read_text(encoding='utf-8'))


def interpreter_command(state, profile, *arguments):
    if profile not in state['profiles']:
        raise RuntimeError(f'{profile} environment is missing. Run setup --manager {state["manager"]} --features.')
    prefix = Path(state['profiles'][profile])
    if state['manager'] == 'conda':
        return [*state['conda'], 'run', '--no-capture-output', '--prefix', str(prefix), 'python', *map(str, arguments)]
    executable = prefix / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    return [str(executable), *map(str, arguments)]


def runtime(state, profile, *arguments, env=None):
    execute(interpreter_command(state, profile, *arguments), env=env)


def find_conda():
    # Prefer the base module over Windows conda.bat, which can depend on shell activation.
    if importlib.util.find_spec('conda') is not None:
        return [sys.executable, '-m', 'conda']
    executable = os.environ.get('CONDA_EXE') or shutil.which('conda.exe') or shutil.which('conda')
    if not executable:
        raise RuntimeError('Conda was not found. Open an Anaconda/Miniconda prompt or choose --manager venv.')
    return [executable]


def find_python(requested=None):
    choices = [[requested]] if requested else ([[sys.executable]] if sys.version_info[:2] == (3, 11) else [])
    if not requested:
        if shutil.which('python3.11'):
            choices.append([shutil.which('python3.11')])
        if os.name == 'nt' and shutil.which('py'):
            choices.append([shutil.which('py'), '-3.11'])
    for command in choices:
        try:
            check = subprocess.run([*command, '-c', 'import sys; raise SystemExit(sys.version_info[:2] != (3,11))'],
                                   capture_output=True, check=False, env=process_env())
            if check.returncode == 0:
                return command
        except OSError:
            pass
    raise RuntimeError('Python 3.11 is required. Install it or pass setup --python /path/to/python3.11.')


def setup(args):
    profiles = PROFILES if args.features else ['heads']
    state_path = ROOT / '.reproduce/state.json'
    previous = json.loads(state_path.read_text(encoding='utf-8')) if state_path.exists() else {}
    state = {'manager': args.manager, 'python': '3.11', 'profiles': {}}
    if previous.get('manager') == args.manager:
        state['profiles'].update(previous.get('profiles', {}))
    conda_env = {'CONDA_PKGS_DIRS': str(ROOT / '.reproduce/conda-cache')}
    creator = find_conda() if args.manager == 'conda' else find_python(args.python)
    if args.manager == 'conda':
        state['conda'] = creator
    for profile in profiles:
        prefix = ROOT / '.reproduce' / args.manager / profile
        if not prefix.exists():
            if args.manager == 'conda':
                execute([*creator, 'create', '--prefix', prefix, 'python=3.11', 'pip', '-y'], conda_env)
            else:
                prefix.parent.mkdir(parents=True, exist_ok=True)
                execute([*creator, '-m', 'venv', prefix])
        state['profiles'][profile] = str(prefix)
        runtime(state, profile, '-c', 'import sys; assert sys.version_info[:2] == (3,11), sys.version')
        if profile != 'heads':
            pair = ('2.13.0', '0.28.0') if profile == 'vision' else ('2.5.1', '0.20.1')
            index = ['--index-url', 'https://download.pytorch.org/whl/cpu'] if sys.platform in ('win32', 'linux') else []
            runtime(state, profile, '-m', 'pip', 'install', *index, 'torch==' + pair[0], 'torchvision==' + pair[1])
        runtime(state, profile, '-m', 'pip', 'install', '-r', ROOT / f'requirements/reviewer-{profile}.txt')
        runtime(state, profile, '-m', 'pip', 'check')
        # Save after each successful profile, so an optional-provider failure does not hide a working head environment.
        write_json(state_path, state)
    print('Setup complete. Next: python reproduce.py check' + (' --features' if args.features else ''))


def check(args):
    state = load_state()
    for profile in (PROFILES if args.features else ['heads']):
        runtime(state, profile, 'scripts/check_reviewer_environment.py', '--profile', profile,
                '--output', ROOT / f'.reproduce/checks/{state["manager"]}-{profile}.json')
    runtime(state, 'heads', '-m', 'pytest', 'tests', '-q', '--basetemp', ROOT / '.reproduce/test-output')
    if args.features:
        runtime(state, 'pathology', '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_pathology_checkpoint.py')
    print('Checking published summary files next; this check does not refit experiments.', flush=True)
    runtime(state, 'heads', 'scripts/verify_paper_results.py')


def reserve_output(output, resume):
    output = output.resolve()
    if output.exists() and not resume:
        raise FileExistsError(f'Preserving existing output: {output}. Use a new --output or --resume.')
    output.mkdir(parents=True, exist_ok=True)
    return output


def stage_output(state, script, destination, options, proof, env):
    if destination.exists():
        marker = destination / 'provenance.json'
        if not marker.is_file():
            raise FileExistsError(f'Incomplete output is preserved at {destination}; choose a new --output.')
        record = json.loads(marker.read_text(encoding='utf-8'))
        if any(record.get(key) != digest(path) for key, path in proof.items()):
            raise ValueError(f'Existing output provenance differs: {destination}')
        print('Preserved verified stage:', destination.name, flush=True)
        return
    runtime(state, 'heads', 'scripts/' + script, *options, '--output-dir', destination, env=env)


def is_full_study(tasks, seeds, completed):
    return (set(tasks) == set(TASKS) and set(seeds) == set(SEEDS)
            and completed.get('tasks') == tasks and completed.get('seeds') == seeds
            and completed.get('protocols') == PROTOCOLS and completed.get('completed_jobs') == 50)


def compare_report(report, full):
    def records(path):
        with path.open(encoding='utf-8', newline='') as stream:
            return list(csv.DictReader(stream))
    def key(row):
        return tuple(row[name] for name in ('task', 'protocol', 'center', 'method'))
    reference = {}
    for name in ('original_image_metrics.csv', 'histology_image_metrics.csv'):
        for row in records(ROOT / 'results/paper' / name):
            previous = reference.get(key(row))
            if previous and any(float(previous[m]) != float(row[m]) for m in METRICS):
                raise ValueError('Conflicting recorded result summaries')
            reference[key(row)] = row
    actual = records(report / 'image_metrics_seed_means.csv')
    if not actual:
        raise ValueError('No recomputed result rows were produced')
    if len({key(r) for r in actual}) != len(actual):
        raise ValueError('Repeated task/protocol/target/head result in recomputed report')
    if full and {key(r) for r in actual} != set(reference):
        raise ValueError('Complete-study report does not contain all 308 recorded result cells')
    maxima = {m: 0.0 for m in METRICS}
    for row in actual:
        if key(row) not in reference:
            raise ValueError('Unexpected recomputed result cell: ' + str(key(row)))
        for metric in METRICS:
            difference = abs(float(row[metric]) - float(reference[key(row)][metric]))
            if not math.isfinite(difference):
                raise ValueError('Non-finite recomputed metric: ' + metric)
            maxima[metric] = max(maxima[metric], difference)
    result = {'scope': 'recomputed predictions versus released ten-seed means',
              'complete_five_task_ten_seed_study': full, 'result_rows_compared': len(actual),
              'report_sha256': digest(report / 'image_metrics_seed_means.csv'),
              'maximum_absolute_difference': maxima,
              'partial_run_note': None if full else 'Selected task/seed means are not the full ten-seed estimate; differences from the published ten-seed means are expected.'}
    write_json(report.parent / 'comparison.json', result)
    print('Maximum absolute differences from recorded ten-seed means:', json.dumps(maxima), flush=True)
    if not full:
        print(result['partial_run_note'], flush=True)
    return result


def run_study(args, state=None, prepared=False):
    state = state or load_state()
    features = args.features.resolve()
    catalog = json.loads((ROOT / 'configs/tasks.json').read_text(encoding='utf-8'))['tasks']
    missing = [catalog[t]['features'] for t in args.tasks if not (features / catalog[t]['features']).is_file()]
    if missing:
        raise FileNotFoundError('Missing registered features: ' + ', '.join(missing) + '. Use images to reconstruct them, or supply the verified feature directory.')
    interpreter_command(state, 'heads')
    out = args.output.resolve() if prepared else reserve_output(args.output, args.resume)
    env = {'CBMP_FEATURE_DIR': str(features)}
    options = ['--run-dir', out / 'runs', '--tasks', *args.tasks, '--seeds', *map(str, args.seeds),
               '--protocols', *PROTOCOLS, '--threads', str(args.threads), '--workers', str(args.workers)]
    if args.resume:
        options.append('--resume')
    runtime(state, 'heads', 'scripts/run_experiments.py', *options, env=env)
    done = json.loads((out / 'runs/COMPLETE.json').read_text(encoding='utf-8'))
    if (done.get('tasks') != args.tasks or done.get('seeds') != args.seeds
            or done.get('protocols') != PROTOCOLS
            or done.get('completed_jobs') != len(args.tasks) * len(args.seeds)):
        raise ValueError('Fitting did not complete the requested task/seed grid')
    report = out / 'report'
    manifest = out / 'runs/run_manifest.json'
    stage_output(state, 'report_review_revision.py', report,
                 ['--run-dir', out / 'runs', '--attempts', '2000', '--seed', '2027'],
                 {'run_manifest_sha256': manifest}, env)
    full = is_full_study(args.tasks, args.seeds, done)
    compare_report(report, full)
    if full:
        aggregate, stability = out / 'aggregate', out / 'stability'
        report_proof = report / 'provenance.json'
        stage_output(state, 'audit_aggregate_uncertainty.py', aggregate, ['--report-dir', report],
                     {'report_provenance_sha256': report_proof}, env)
        stage_output(state, 'audit_review_stability.py', stability, ['--run-dir', out / 'runs'],
                     {'run_manifest_sha256': manifest}, env)
        stage_output(state, 'export_paper_results.py', out / 'paper', ['--report-dir', report],
                     {'report_sha256': report_proof}, env)
        stage_output(state, 'export_review_supplement.py', out / 'supplement',
                     ['--report-dir', report, '--aggregate-dir', aggregate, '--stability-dir', stability],
                     {'report_sha256': report_proof, 'aggregate_sha256': aggregate / 'provenance.json',
                      'stability_sha256': stability / 'provenance.json'}, env)
    else:
        print('Partial experiment completed; full-paper exports were intentionally not produced.', flush=True)
    print('Experiment output:', out, flush=True)


def images(args):
    state = load_state()
    catalog = json.loads((ROOT / 'configs/tasks.json').read_text(encoding='utf-8'))['tasks']
    needed = {'pathology' if catalog[t]['encoder'] in ('uni', 'conch') else 'vision' for t in args.tasks}
    for profile in needed:
        interpreter_command(state, profile)  # Fail before downloads if setup is incomplete.
    for dataset, root in [('polypgen', args.polypgen_root), ('camelyon', args.camelyon_root)]:
        if any(catalog[t]['dataset'] == dataset for t in args.tasks) and not root.is_dir():
            raise FileNotFoundError(f'Missing {dataset} image directory: {root}. Stage real images first or override its root.')
    out = reserve_output(args.output, args.resume)
    args.features = out / 'features'
    env = {'CBMP_FEATURE_DIR': str(args.features)}
    checkpoints = args.checkpoints.resolve()
    if 'vision' in needed:
        runtime(state, 'vision', 'scripts/fetch_vision_checkpoints.py', '--destination', checkpoints / 'vision')
    if 'pathology' in needed:
        runtime(state, 'pathology', 'scripts/fetch_pathology_checkpoints.py', '--registry', ROOT / 'configs/pathology_models.json',
                '--dest', checkpoints / 'pathology')
    for task in args.tasks:
        definition = catalog[task]
        profile = 'pathology' if definition['encoder'] in ('uni', 'conch') else 'vision'
        cache = args.features / definition['features']
        if cache.exists() and args.resume:
            print('Existing feature cache will be provenance-checked by the fitter:', task, flush=True)
            continue
        image_root = args.polypgen_root if definition['dataset'] == 'polypgen' else args.camelyon_root
        runtime(state, profile, 'scripts/extract_features.py', '--task', task, '--image-root', image_root.resolve(),
                '--checkpoint-dir', checkpoints / profile, '--device', args.device,
                '--batch-size', str(args.batch_size), '--threads', str(args.threads), env=env)
    run_study(args, state, prepared=True)


def stage_images(args):
    state = load_state()
    interpreter_command(state, 'vision')
    interpreter_command(state, 'heads')
    if not args.polypgen_archive.is_file() or not args.camelyon_shards.is_dir():
        raise FileNotFoundError('Supply the permitted PolypGen ZIP and the downloaded CAMELYON parquet directory.')
    runtime(state, 'heads', 'scripts/stage_images.py', '--dataset', 'polypgen', '--archive', args.polypgen_archive.resolve())
    runtime(state, 'vision', 'scripts/extract_camelyon_parquet.py', '--shard-dir', args.camelyon_shards.resolve())


def parser():
    cli = argparse.ArgumentParser(description=__doc__)
    commands = cli.add_subparsers(dest='command', required=True)
    p = commands.add_parser('setup', help='Create separate Python 3.11 environments and install portable requirements')
    p.add_argument('--manager', choices=['venv', 'conda'], default='venv')
    p.add_argument('--features', action='store_true', help='Also install the vision and original UNI/CONCH environments')
    p.add_argument('--python', help='Python 3.11 executable for venv creation')
    p.set_defaults(handler=setup)
    p = commands.add_parser('check', help='Test the environment and code; separately check the recorded summaries')
    p.add_argument('--features', action='store_true')
    p.set_defaults(handler=check)
    for name, handler in [('run', run_study), ('images', images)]:
        p = commands.add_parser(name, help='Refit from registered features' if name == 'run' else 'Extract from real images, then refit and report')
        p.add_argument('--output', type=Path, default=ROOT / 'artifacts/reviewer-run')
        p.add_argument('--tasks', nargs='+', choices=TASKS, default=list(TASKS))
        p.add_argument('--seeds', nargs='+', type=int, default=list(SEEDS))
        p.add_argument('--threads', type=int, default=2)
        p.add_argument('--workers', type=int, default=1)
        p.add_argument('--resume', action='store_true')
        if name == 'run':
            p.add_argument('--features', type=Path, required=True)
        else:
            p.add_argument('--polypgen-root', type=Path, default=ROOT / 'data/raw/polypgen')
            p.add_argument('--camelyon-root', type=Path, default=ROOT / 'data/raw/camelyon')
            p.add_argument('--checkpoints', type=Path, default=ROOT / 'artifacts/checkpoints')
            p.add_argument('--device', choices=['cpu', 'cuda'], default='cpu')
            p.add_argument('--batch-size', type=int, default=16)
        p.set_defaults(handler=handler)
    p = commands.add_parser('login', help='Interactive local Hugging Face login for approved UNI/CONCH access')
    p.set_defaults(handler=lambda args: runtime(load_state(), 'pathology', '-c',
                   'from huggingface_hub import login; login(add_to_git_credential=False)'))
    p = commands.add_parser('stage', help='Stage the permitted PolypGen ZIP and downloaded CAMELYON parquet shards')
    p.add_argument('--polypgen-archive', type=Path, required=True)
    p.add_argument('--camelyon-shards', type=Path, required=True)
    p.set_defaults(handler=stage_images)
    return cli


def main(argv=None):
    cli = parser()
    args = cli.parse_args(argv)
    if hasattr(args, 'tasks'):
        if (len(args.tasks) != len(set(args.tasks)) or len(args.seeds) != len(set(args.seeds))
                or min(args.seeds) < 0 or args.threads < 1 or args.workers < 1
                or getattr(args, 'batch_size', 1) < 1):
            cli.error('Use unique tasks/seeds, non-negative seeds and positive resource limits.')
    try:
        args.handler(args)
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f'Reproduction stopped: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
