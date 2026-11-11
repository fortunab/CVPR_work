"""Export original diagnostic tables and current three-encoder pathology figures."""
import argparse
from pathlib import Path

from export_review_tables import export as export_original
from review_protocol import read_csv,sha256,write_csv,write_json


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report-dir',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    if args.output_dir.exists():raise FileExistsError('Choose a new export directory')
    # Original-group diagnostics require both PolypGen encoders in the report.
    rows=read_csv(args.report_dir/'image_metrics_seed_means.csv')
    tasks={r['task'] for r in rows}
    if {'polypgen_resnet18','polypgen_dinov2','camelyon_resnet18'}<=tasks:
        export_original(args.report_dir,args.output_dir/'original')
    mapping={'camelyon_resnet18':'ResNet18','camelyon_custom_uni':'UNI','camelyon_custom_conch':'CONCH'}
    if not set(mapping)<=tasks:raise ValueError('All three histology encoders are needed for the foundation comparison')
    from export_foundation_figures import figure
    patch=[]
    for source,output,label,endpoint,figure_label in (
        ('image_metrics_seed_means.csv','patch','Patch balanced accuracy','Patch-level balanced accuracy','fig:pathology_encoders_patch'),
        ('patient_macro_seed_means.csv','patient_macro','Patient-macro patch BA',
         'Equal-patient patch metrics, not patient-diagnosis scores','fig:pathology_encoders_patient_macro')):
        values=[dict(encoder=mapping[r['task']],**r) for r in read_csv(args.report_dir/source) if r['task'] in mapping]
        if any(int(r['fitting_seeds'])!=10 for r in values):raise ValueError('Paper exports require ten fitting seeds')
        write_csv(args.output_dir/(output+'_summary.csv'),values)
        if output=='patch':patch=values
        (args.output_dir/(output+'_balanced_accuracy.tex')).write_text(
            figure(values,'balanced_accuracy',label,endpoint,figure_label),encoding='utf-8')
    cells={(r['encoder'],r['protocol'],r['center'],r['method']):r for r in patch}
    from export_review_tables import HEADS
    for protocol in sorted({r['protocol'] for r in patch}):
        for metric in ('balanced_accuracy','auroc'):
            tex=[r'\begin{table*}[t]',r'\centering\small',r'\begin{tabular}{lrrrrrr}',r'\hline',
                 r'Head & ResNet18 H2 & UNI H2 & CONCH H2 & ResNet18 H1 & UNI H1 & CONCH H1 \\',r'\hline']
            for method in sorted({r['method'] for r in patch if r['protocol']==protocol}):
                numbers=[]
                for center in ('2','1'):
                    for encoder in ('ResNet18','UNI','CONCH'):
                        row=cells[encoder,protocol,center,method]
                        numbers.append(f"${100*float(row[metric]):.2f}\\pm{100*float(row[metric+'_seed_sd']):.2f}$")
                tex.append(HEADS.get(method,method.replace('_',r'\_'))+' & '+' & '.join(numbers)+r' \\')
            tex.extend([r'\hline',r'\end{tabular}',r'\caption{Custom-cohort '+metric.replace('_',' ')+
                ', percent; ten-seed means and fitting-seed SD. '+protocol+' grids. Not full official WILDS.}',
                r'\label{tab:foundation_'+protocol+'_'+metric+'}',r'\end{table*}'])
            (args.output_dir/f'foundation_{protocol}_{metric}.tex').write_text('\n'.join(tex)+'\n',encoding='utf-8')
    write_json(args.output_dir/'provenance.json',{'report_sha256':sha256(args.report_dir/'provenance.json'),
        'scope':'generated paper exports; same custom cohort and fixed protocol labels'})
    print('Exported three-encoder summaries and native TikZ; original diagnostic exports where supported')


if __name__=='__main__':main()
