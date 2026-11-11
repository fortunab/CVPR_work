"""Download only pinned public ResNet18/DINOv2 assets; no model execution."""
import argparse
import json
from pathlib import Path
import shutil
import urllib.request

from review_protocol import ROOT,sha256


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination',type=Path,default=ROOT/'artifacts/checkpoints/vision')
    args=parser.parse_args();args.destination.mkdir(parents=True,exist_ok=True)
    assets=json.loads((ROOT/'configs/vision_assets.json').read_text(encoding='utf-8'))['assets']
    for name,record in assets.items():
        target=args.destination/name
        if not target.exists():
            temporary=target.with_suffix(target.suffix+'.partial')
            with urllib.request.urlopen(record['url']) as source,temporary.open('xb') as output:
                shutil.copyfileobj(source,output)
            if sha256(temporary)!=record['sha256']:raise ValueError('Downloaded asset checksum differs: '+name)
            temporary.replace(target)
        if sha256(target)!=record['sha256']:raise ValueError('Existing asset differs: '+name)
        print('Verified public checkpoint component:',name)


if __name__=='__main__':main()
