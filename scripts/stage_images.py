"""Stage the audited paper cohort from a ZIP or image tree, verifying content hashes."""
import argparse
import hashlib
from pathlib import Path
import shutil
import zipfile

from data_catalog import load_cohort,safe_relative
from review_protocol import ROOT,sha256,write_json


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset',choices=('polypgen','camelyon'),required=True)
    source=parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--archive',type=Path,help='ZIP, e.g. the official PolypGen release')
    source.add_argument('--image-root',type=Path,help='Extracted images; exact hash matching is required')
    parser.add_argument('--destination',type=Path)
    args=parser.parse_args();rows,definition=load_cohort(args.dataset)
    destination=(args.destination or ROOT/'data/raw'/args.dataset).resolve()
    destination.mkdir(parents=True,exist_ok=True)
    archive=zipfile.ZipFile(args.archive) if args.archive else None
    names=[p.filename for p in archive.infolist() if not p.is_dir()] if archive else []
    index=None
    try:
        for count,row in enumerate(rows,1):
            relative=safe_relative(row['image_path']);target=(destination/relative).resolve()
            if not target.is_relative_to(destination):raise ValueError('Unsafe staging target')
            if target.exists():
                if sha256(target)!=row['sha256']:raise ValueError('Existing staged image differs: '+row['sample_id'])
                continue
            if archive:
                suffix=relative.as_posix()
                candidates=[n for n in names if n==suffix or n.endswith('/'+suffix)]
                if len(candidates)!=1:raise ValueError('Missing/ambiguous ZIP member: '+suffix)
                data=archive.read(candidates[0])
            else:
                image=args.image_root/relative
                if not image.is_file():
                    if index is None:
                        index={}
                        for file in args.image_root.rglob('*'):
                            if file.is_file():index.setdefault(file.name,[]).append(file)
                    candidates=index.get(relative.name,[])
                    candidates=[p for p in candidates if sha256(p)==row['sha256']]
                    if len(candidates)!=1:raise ValueError('Missing/ambiguous image content: '+row['sample_id'])
                    image=candidates[0]
                data=image.read_bytes()
            if hashlib.sha256(data).hexdigest()!=row['sha256']:raise ValueError('Image hash mismatch: '+row['sample_id'])
            target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('xb') as stream:stream.write(data)
            if count%1000==0:print('Verified/staged',count,'/',len(rows),flush=True)
    finally:
        if archive:archive.close()
    write_json(destination/'STAGED.json',{'dataset':args.dataset,'images':len(rows),
        'manifest_sha256':definition['manifest_sha256'],'all_image_bytes_verified':True})
    print('Staged the audited cohort:',len(rows),'images')


if __name__=='__main__':main()
