"""Portable input checks use explicit tiny fixtures, never synthetic paper results."""
import json
from pathlib import Path

import numpy as np
import pytest

import data_catalog as data
from review_protocol import sha256,write_csv,write_json


def fixture(tmp_path,monkeypatch):
    rows=[]
    for center in ('0','3','4','1','2'):
        for j in range(4):
            rows.append({'sample_id':f'{center}:{j}','label':j%2,'center':center,
                'group_id':f'{center}:patient{j//2}','sha256':f'unique:{center}:{j}',
                'pixel_sha256':f'pixel:{center}:{j}','image_path':f'{center}/image{j}.png',
                'partition':'source_train' if center in ('0','3','4') else 'primary_test' if center=='2' else 'secondary_test'})
    manifest=tmp_path/'manifests/camelyon.csv';write_csv(manifest,rows)
    features=np.random.default_rng(71).normal(size=(20,6));features/=np.linalg.norm(features,axis=1,keepdims=True)
    path=tmp_path/'features/camelyon_resnet18.npz';path.parent.mkdir()
    np.savez_compressed(path,features=features,sample_ids=[r['sample_id'] for r in rows],metadata=json.dumps({'checkpoint_sha256':'fixture-weights'}))
    config={'datasets':{'camelyon':{'manifest':'manifests/camelyon.csv','manifest_sha256':sha256(manifest),
        'ordered_identity_sha256':data.ordered_identity(rows),'rows':20,'original_manifest_sha256':'fixture-original'}},
        'tasks':{'camelyon_resnet18':{'dataset':'camelyon','dimension':6,'features':path.name,
        'paper_feature_sha256':sha256(path),'checkpoint_sha256':'fixture-weights'}}}
    write_json(tmp_path/'configs/tasks.json',config)
    monkeypatch.setattr(data,'ROOT',tmp_path);monkeypatch.setattr(data,'verify_core',lambda:None)
    monkeypatch.setenv('CBMP_FEATURE_DIR',str(path.parent))
    return rows,config,path


def test_registered_input_is_portable_and_keeps_both_targets_out_of_selection(tmp_path,monkeypatch):
    rows,config,path=fixture(tmp_path,monkeypatch)
    values,loaded,splits,proof=data.load_task('camelyon_resnet18')
    assert values.shape==(20,6) and proof['cache_mode']=='exact_paper_cache'
    for split in splits:
        assert {loaded[i]['center'] for i in split['outer_train']}=={'0','3','4'}
        assert {loaded[i]['center'] for i in split['outer_test']}=={split['heldout_center']}
        for fold in split['inner_folds']:
            assert {loaded[i]['center'] for i in fold['validation']}<={'0','3','4'}


def test_unknown_cache_bytes_require_a_fresh_extraction_receipt(tmp_path,monkeypatch):
    _,config,path=fixture(tmp_path,monkeypatch)
    config['tasks']['camelyon_resnet18']['paper_feature_sha256']='another-cache'
    write_json(tmp_path/'configs/tasks.json',config)
    with pytest.raises(ValueError,match='no verified fresh-extraction receipt'):data.load_task('camelyon_resnet18')


def test_altered_manifest_and_reordered_samples_are_rejected(tmp_path,monkeypatch):
    rows,config,path=fixture(tmp_path,monkeypatch)
    rows[0]['label']=1
    write_csv(tmp_path/'manifests/camelyon.csv',rows)
    with pytest.raises(ValueError,match='manifest bytes'):data.load_task('camelyon_resnet18')


@pytest.mark.parametrize('value',['../outside.png','C:/private/image.png','/absolute/image.png','a/../../image.png'])
def test_recorded_paths_cannot_escape_the_data_root(value):
    with pytest.raises(ValueError,match='safe relative'):data.safe_relative(value)


def test_missing_artifacts_have_actionable_instructions(tmp_path,monkeypatch):
    _,_,path=fixture(tmp_path,monkeypatch);path.unlink()
    with pytest.raises(FileNotFoundError,match='import_local_artifacts.py'):data.load_task('camelyon_resnet18')


def test_frozen_scientific_sources_are_still_byte_identical():
    data.verify_core()


def test_resume_provenance_records_configuration_and_split_identity(tmp_path,monkeypatch):
    _,config,_=fixture(tmp_path,monkeypatch)
    before=data.load_task('camelyon_resnet18')[3]
    config['tasks']['camelyon_resnet18']['annotation']='explicitly revised input plan'
    write_json(tmp_path/'configs/tasks.json',config)
    after=data.load_task('camelyon_resnet18')[3]
    assert before['catalog_sha256']!=after['catalog_sha256']
    assert before['splits_sha256']==after['splits_sha256']
