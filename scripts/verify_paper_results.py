"""Verify small tracked summaries and print the paper's matched4 histology comparison."""
import csv
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    folder=ROOT/'results/paper';checks=json.loads((folder/'SHA256.json').read_text())
    for name,digest in checks.items():
        if hashlib.sha256((folder/name).read_bytes()).hexdigest()!=digest:
            raise ValueError('Recorded paper summary changed: '+name)
    rows=list(csv.DictReader((folder/'histology_image_metrics.csv').open(encoding='utf-8',newline='')))
    print('Primary target H2; matched4 grids; ten-seed mean balanced accuracy (%)')
    for encoder in ('ResNet18','UNI','CONCH'):
        values=[]
        for method in ('cbmp','linear_logistic','trainable_cosine'):
            row=next(r for r in rows if r['encoder']==encoder and r['protocol']=='matched4' and r['center']=='2' and r['method']==method)
            values.append(f"{100*float(row['balanced_accuracy']):.2f}")
        print(encoder+': CBMP / linear / cosine = '+' / '.join(values))
    print('Verified summary file hashes. This does not reconstruct predictions or refit models.')


if __name__=='__main__':main()
