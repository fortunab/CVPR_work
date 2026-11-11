"""Recover only registered patient-capped patches from the pinned redistribution."""
import argparse
from collections import defaultdict
import hashlib
import io
from pathlib import Path

from PIL import Image
from data_catalog import load_cohort,safe_relative
from review_protocol import ROOT,sha256,write_json


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--shard-dir',type=Path,required=True)
    parser.add_argument('--destination',type=Path,default=ROOT/'data/raw/camelyon')
    args=parser.parse_args()
    import pyarrow.parquet as pq
    rows,definition=load_cohort('camelyon');by_shard=defaultdict(list)
    for row in rows:by_shard[row['shard']].append(row)
    destination=args.destination.resolve();destination.mkdir(parents=True,exist_ok=True)
    for shard,records in sorted(by_shard.items()):
        files=list(args.shard_dir.rglob(shard))
        if len(files)!=1:raise ValueError('Supply exactly one pinned parquet shard named '+shard)
        parquet=pq.ParquetFile(files[0]);by_group=defaultdict(list)
        offsets=[0]
        for group in range(parquet.num_row_groups):offsets.append(offsets[-1]+parquet.metadata.row_group(group).num_rows)
        for row in records:by_group[int(row['row_group'])].append(row)
        for group,selected in sorted(by_group.items()):
            content=parquet.read_row_group(group,columns=['image'],use_threads=False)['image'].to_pylist()
            for row in selected:
                value=content[int(row['shard_row'])-offsets[group]]
                data=value.get('bytes')
                if data is None or hashlib.sha256(data).hexdigest()!=row['sha256']:
                    raise ValueError('Pinned image bytes differ: '+row['sample_id'])
                with Image.open(io.BytesIO(data)) as image:
                    rgb=image.convert('RGB')
                    if rgb.size!=(96,96) or hashlib.sha256(rgb.tobytes()).hexdigest()!=row['pixel_sha256']:
                        raise ValueError('Decoded patch differs: '+row['sample_id'])
                path=(destination/safe_relative(row['image_path'])).resolve()
                if not path.is_relative_to(destination):raise ValueError('Unsafe destination')
                if path.exists():
                    if sha256(path)!=row['sha256']:raise ValueError('Existing patch differs')
                else:
                    path.parent.mkdir(parents=True,exist_ok=True)
                    with path.open('xb') as out:out.write(data)
        print('Verified registered patches from',shard,flush=True)
    write_json(destination/'STAGED.json',{'images':len(rows),'dataset':'camelyon',
        'manifest_sha256':definition['manifest_sha256'],'all_image_bytes_verified':True,
        'scope':'registered custom cohort, not full official WILDS'})


if __name__=='__main__':main()
