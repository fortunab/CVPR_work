"""Check one Python 3.11 reviewer environment without downloading data or weights.

These are dependency/API smoke checks, not a study or feature reproduction run.
The script uses only the standard library until it imports the selected profile.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stdout
import importlib
import importlib.metadata
import io
import json
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PROVIDER_COMMIT = '141cc09c7d4ff33d8eda562bd75169b457f71a62'


def expected_packages(profile):
    packages = {}
    requirements = ROOT / 'requirements' / f'reviewer-{profile}.txt'
    for line in requirements.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '==' not in line:
            continue
        requirement, _, marker = line.partition(';')
        if marker.strip() == 'sys_platform == "win32"' and sys.platform != 'win32':
            continue
        name, version = requirement.strip().split('==', 1)
        packages[name] = version
    return packages


def check_versions(profile):
    versions = {}
    for name, expected in expected_packages(profile).items():
        actual = importlib.metadata.version(name)
        # CPU wheels use PEP 440 local versions such as 2.5.1+cpu.
        if actual.split('+', 1)[0] != expected:
            raise RuntimeError(f'{name}: expected {expected}, found {actual}')
        versions[name] = actual
    if profile == 'pathology':
        distribution = importlib.metadata.distribution('conch')
        direct_url = json.loads(distribution.read_text('direct_url.json') or '{}')
        actual_commit = direct_url.get('vcs_info', {}).get('commit_id')
        if actual_commit != PROVIDER_COMMIT:
            raise RuntimeError('CONCH provider commit is not the recorded original release')
        versions['conch'] = distribution.version
        versions['conch_provider_commit'] = actual_commit
    return versions


def dependency_smoke(profile):
    modules = ['numpy', 'scipy.optimize', 'sklearn.linear_model', 'PIL.Image']
    if profile == 'vision':
        modules += ['torch', 'torchvision', 'transformers', 'safetensors', 'pyarrow']
    if profile == 'pathology':
        modules += ['torch', 'torchvision', 'timm', 'transformers', 'conch.open_clip_custom']
    for name in modules:
        importlib.import_module(name)
    import numpy as np
    from scipy.optimize import minimize_scalar
    from sklearn.linear_model import LogisticRegression
    result = minimize_scalar(lambda value: (value - 1.0) ** 2)
    if not result.success or abs(result.x - 1.0) > 1e-5:
        raise RuntimeError('SciPy numerical smoke check failed')
    model = LogisticRegression().fit(np.array([[-2.0], [-1.0], [1.0], [2.0]]), [0, 0, 1, 1])
    if model.predict([[-1.5], [1.5]]).tolist() != [0, 1]:
        raise RuntimeError('Classifier dependency smoke check failed')
    probes = ['scipy_optimization', 'sklearn_linear_fit']
    if profile == 'vision':
        import torch
        from torchvision.models import resnet18
        from transformers import AutoImageProcessor, AutoModel, Dinov2Config
        # Small randomly initialized models exercise native CPU kernels and the
        # DINOv2 API. No medical data or pretrained study weights are involved.
        torch.set_num_threads(1)
        with torch.inference_mode():
            resnet = resnet18(weights=None).eval()
            if tuple(resnet(torch.zeros(1, 3, 32, 32)).shape) != (1, 1000):
                raise RuntimeError('Torchvision forward smoke check failed')
            config = Dinov2Config(hidden_size=32, num_hidden_layers=1,
                                  num_attention_heads=4, image_size=32, patch_size=16)
            dino = AutoModel.from_config(config, attn_implementation='sdpa').eval()
            output = dino(pixel_values=torch.zeros(1, 3, 32, 32))
            if not torch.equal(output.pooler_output, output.last_hidden_state[:, 0]):
                raise RuntimeError('DINOv2 final-CLS API differs from the extractor contract')
        if AutoImageProcessor is None:
            raise RuntimeError('Transformers image preprocessing API is unavailable')
        probes += ['untrained_resnet18_forward', 'small_untrained_dinov2_final_cls']
    elif profile == 'pathology':
        import torch
        from conch.open_clip_custom import create_model_from_pretrained
        if not callable(create_model_from_pretrained):
            raise RuntimeError('Original CONCH model construction API is unavailable')
        if not torch.isfinite(torch.nn.Linear(2, 2)(torch.zeros(1, 2))).all():
            raise RuntimeError('Pathology PyTorch CPU kernel smoke check failed')
        probes += ['original_conch_api_import', 'torch_cpu_linear_forward']
    return modules, probes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=('heads', 'vision', 'pathology'), default='heads')
    parser.add_argument('--output', type=Path, help='Optional JSON environment-check record')
    args = parser.parse_args()
    record = {'profile': args.profile, 'scope': 'data-free dependency and API smoke check',
              'python': platform.python_version(), 'platform': sys.platform,
              'architecture': platform.machine(), 'data_or_weights_downloaded': False,
              'full_study_reproduced': False, 'status': 'failed'}
    exit_code = 1
    try:
        if sys.version_info[:2] != (3, 11):
            raise RuntimeError(f'Use Python 3.11 for every reviewer environment; found {platform.python_version()}')
        installed = subprocess.run([sys.executable, '-m', 'pip', 'check'],
                                   check=False, capture_output=True, text=True)
        if installed.returncode:
            raise RuntimeError('pip check failed: ' + (installed.stdout + installed.stderr).strip())
        record['pip_check_passed'] = True
        record['versions'] = check_versions(args.profile)
        from PIL import features as image_features
        record['image_codecs'] = {'jpeg': image_features.version('jpg'),
                                  'libjpeg_turbo': image_features.version('libjpeg_turbo')}
        if args.profile == 'vision' and record['image_codecs']['jpeg'] != '9.0':
            record['warnings'] = [
                'The original PolypGen JPEG pixels were decoded with libjpeg 9. '
                'Other JPEG builds can change fresh features even with Pillow 10.4.0. '
                'Exact original-cache refitting avoids this decoding difference; '
                'do not infer raw-image numerical agreement from this installation check.'
            ]
        with redirect_stdout(io.StringIO()):
            modules, probes = dependency_smoke(args.profile)
        record.update(checked_imports=modules, dependency_probes=probes, status='passed')
        exit_code = 0
    except Exception as error:
        record['error'] = {'type': type(error).__name__, 'message': str(error)}
    text = json.dumps(record, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding='utf-8')
    print(text, end='')
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
