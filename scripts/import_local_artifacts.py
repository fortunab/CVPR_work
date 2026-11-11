"""Copy only the five registered feature files from an existing project; no old runs."""
import argparse
from pathlib import Path
import shutil

from data_catalog import catalog,feature_directory
from review_protocol import sha256,write_json


PATHS={
 'polypgen_resnet18':'isolated_datasets/polypgen_v3_copy_2026-10-17/features/resnet18_imagenet1k_v1.npz',
 'polypgen_dinov2':'isolated_datasets/polypgen_extensions_2026-10-20/exp4_dinov2/features/dinov2_base_cls.npz',
 'camelyon_resnet18':'isolated_datasets/polypgen_extensions_2026-10-20/exp5_camelyon/features/resnet18_imagenet1k_v1.npz',
 'camelyon_custom_uni':'reproduction_runs/pathology_uni_conch_2026-11-10/features_uni/features.npz',
 'camelyon_custom_conch':'reproduction_runs/pathology_uni_conch_2026-11-10/features_conch/features.npz'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True,help='Original local research project or directory of TASK.npz files')
    parser.add_argument('--tasks',nargs='+',choices=list(PATHS),default=list(PATHS))
    args=parser.parse_args()
    definitions=catalog()['tasks']; destination=feature_directory();destination.mkdir(parents=True,exist_ok=True)
    verified={}
    for task in args.tasks:
        source=args.source/PATHS[task]
        if not source.is_file():source=args.source/definitions[task]['features']
        if not source.is_file() or sha256(source)!=definitions[task]['paper_feature_sha256']:
            raise ValueError('Missing or different original feature bytes for '+task)
        target=destination/definitions[task]['features']
        if target.exists():
            if sha256(target)!=sha256(source):raise FileExistsError('Refusing to replace a different cache: '+target.name)
        else:
            partial=target.with_suffix('.partial')
            with partial.open('xb') as out,source.open('rb') as inp:shutil.copyfileobj(inp,out)
            if sha256(partial)!=definitions[task]['paper_feature_sha256']:raise ValueError('Copy checksum failed')
            partial.replace(target)
        verified[task]=sha256(target)
        print('Verified original feature cache:',task,flush=True)
    write_json(destination/'import_receipt.json',{'features_sha256':verified,'scope':'only registered feature caches; no raw images or experiment folders'})


if __name__=='__main__':main()
