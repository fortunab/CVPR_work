"""Portable registered cohorts and explicit feature provenance for the paper."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath

import numpy as np

from review_protocol import ROOT, CORE, read_csv, sha256, validate_splits


def catalog():
    return json.loads((ROOT/'configs/tasks.json').read_text(encoding='utf-8'))


def ordered_identity(rows):
    fields=('sample_id','label','center','group_id','sha256','pixel_sha256')
    values=[[str(r.get(k,'')) for k in fields] for r in rows]
    return hashlib.sha256(json.dumps(values,separators=(',',':')).encode()).hexdigest()


def safe_relative(value):
    path=PurePosixPath(value.replace('\\','/'))
    if not value or path.is_absolute() or '..' in path.parts or ':' in value:
        raise ValueError('A safe relative artifact/image path is required')
    return Path(*path.parts)


def verify_core():
    proof=json.loads((ROOT/'provenance/core_sources.json').read_text(encoding='utf-8'))
    for record in proof['files']:
        if sha256(ROOT/record['path'])!=record['sha256']:
            raise ValueError('The frozen classifier implementation changed: '+record['path'])


def load_cohort(dataset):
    definition=catalog()['datasets'][dataset]
    manifest=ROOT/safe_relative(definition['manifest'])
    if sha256(manifest)!=definition['manifest_sha256']:
        raise ValueError('Registered manifest bytes changed')
    rows=read_csv(manifest)
    if len(rows)!=definition['rows'] or ordered_identity(rows)!=definition['ordered_identity_sha256']:
        raise ValueError('Cohort identities, order or labels changed')
    for row in rows:
        row['label']=int(row['label'])
        if row['label'] not in (0,1) or not row['group_id'] or not row['sha256']:
            raise ValueError('Audited binary labels, recorded groups and hashes are mandatory')
        safe_relative(row['image_path'])
    return rows,definition


def splits_for(dataset,rows):
    if dataset=='polypgen':
        expected=catalog()['datasets'][dataset]['splits_sha256']
        if sha256(ROOT/'configs/polypgen_splits.json')!=expected:
            raise ValueError('Frozen PolypGen split definitions changed')
        splits=json.loads((ROOT/'configs/polypgen_splits.json').read_text(encoding='utf-8'))
    else:
        sources=[i for i,r in enumerate(rows) if r['center'] in ('0','3','4')]
        if any(rows[i]['partition']!='source_train' for i in sources):
            raise ValueError('Unexpected histology source partition')
        inner=[{'train':[i for i in sources if rows[i]['center']!=center],
                'validation':[i for i in sources if rows[i]['center']==center],
                'validation_center':center} for center in ('0','3','4')]
        splits=[{'heldout_center':center,'outer_train':sources,
                 'outer_test':[i for i,r in enumerate(rows) if r['center']==center],
                 'inner_folds':inner,'selection_protocol':'leave_one_source_center_out'} for center in ('2','1')]
    validate_splits(rows,splits)
    return splits


def feature_directory():
    return Path(os.environ.get('CBMP_FEATURE_DIR',str(ROOT/'artifacts/features'))).resolve()


def load_task(task):
    verify_core()
    definition=catalog()['tasks'].get(task)
    if definition is None:
        raise ValueError('Unknown registered paper task: '+task)
    rows,cohort=load_cohort(definition['dataset'])
    path=feature_directory()/safe_relative(definition['features'])
    if not path.is_file():
        raise FileNotFoundError('Missing '+path.name+'. Import the verified local caches with '
            'scripts/import_local_artifacts.py, or run scripts/extract_features.py; see docs/REPRODUCTION.md.')
    fingerprint=sha256(path)
    exact=fingerprint==definition['paper_feature_sha256']
    with np.load(path,allow_pickle=False) as cache:
        features=cache['features'].copy()
        metadata=json.loads(str(cache['metadata'].item()))
        if 'sample_ids' in cache:
            if cache['sample_ids'].tolist()!=[r['sample_id'] for r in rows]:
                raise ValueError('Feature sample order differs from the registered manifest')
        elif not exact or task!='polypgen_resnet18':
            raise ValueError('Explicit feature sample identities are required')
    if not exact:
        receipt=path.with_suffix('.receipt.json')
        if not receipt.is_file():
            raise ValueError('Unknown cache bytes: no verified fresh-extraction receipt')
        audit=json.loads(receipt.read_text(encoding='utf-8'))
        if (audit['features_sha256']!=fingerprint or audit['manifest_sha256']!=cohort['manifest_sha256']
                or audit['ordered_identity_sha256']!=cohort['ordered_identity_sha256']
                or audit['extractor_sha256']!=sha256(ROOT/'scripts/extract_features.py')
                or metadata.get('checkpoint_sha256')!=definition['checkpoint_sha256']
                or metadata.get('manifest_sha256')!=cohort['manifest_sha256']):
            raise ValueError('Fresh cache provenance does not match this cohort, checkpoint or extractor')
    if (features.shape!=(len(rows),definition['dimension']) or not np.isfinite(features).all()
            or not np.allclose(np.linalg.norm(features,axis=1),1,atol=1e-5)):
        raise ValueError('Features must have the registered dimensions and finite unit-norm rows')
    splits=splits_for(definition['dataset'],rows)
    split_digest=hashlib.sha256(json.dumps(splits,sort_keys=True).encode()).hexdigest()
    return features,rows,splits,{
        'task':task,'feature_sha256':fingerprint,'manifest_sha256':cohort['manifest_sha256'],
        'ordered_identity_sha256':cohort['ordered_identity_sha256'],
        'original_manifest_sha256':cohort['original_manifest_sha256'],
        'catalog_sha256':sha256(ROOT/'configs/tasks.json'),'splits_sha256':split_digest,
        'feature_metadata':metadata,'cache_mode':'exact_paper_cache' if exact else 'fresh_extraction',
        'classifier_sources':{p.name:sha256(p) for p in CORE.glob('*.py')},
        'raw_image_verification':'Original recorded audit for imported caches; fresh extraction reopens and hashes all images'}
