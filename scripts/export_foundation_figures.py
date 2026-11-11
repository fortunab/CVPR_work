from review_protocol import read_csv

ENCODERS = ('ResNet18', 'UNI', 'CONCH')
HEADS = (('cbmp', 'CBMP'), ('linear_logistic', 'Linear'), ('trainable_cosine', 'Cosine'))
COLORS = ('pathologyResnetBlue', 'pathologyUniOrange', 'pathologyConchGreen')


def figure(records, metric, label, endpoint, figure_label):
    cells = {(r['encoder'], r['protocol'], r['center'], r['method']): r for r in records}
    lines = [r'\begin{figure*}[t]', r'\centering', r'\begin{tikzpicture}[font=\scriptsize]',
             r'\definecolor{pathologyResnetBlue}{HTML}{0072B2}',
             r'\definecolor{pathologyUniOrange}{HTML}{E69F00}',
             r'\definecolor{pathologyConchGreen}{HTML}{009E73}']
    for index, (encoder, color) in enumerate(zip(ENCODERS, COLORS)):
        x = 4.1 + index*2.2
        lines.extend([f'\\fill[{color}] ({x:.2f},5.05) rectangle ({x+.22:.2f},5.23);',
                      f'\\node[anchor=west] at ({x+.30:.2f},5.14) {{{encoder}}};'])
    for panel, (center, title) in enumerate((('2', 'H2 (primary)'), ('1', 'H1 (secondary)'))):
        lines.append(f'\\begin{{scope}}[xshift={panel*8.1:.2f}cm]')
        lines.append(f'\\node[font=\\small\\bfseries] at (3.9,4.58) {{{title}}};')
        for tick in range(0, 101, 20):
            y = tick*.04
            lines.extend([f'\\draw[black!15] (.9,{y:.3f}) -- (7.0,{y:.3f});',
                          f'\\node[anchor=east] at (.8,{y:.3f}) {{{tick}}};'])
        lines.append(f'\\node[rotate=90] at (.12,2) {{{label} (\\%)}};')
        for h, (method, head_label) in enumerate(HEADS):
            middle = 1.95 + h*2.0
            for e, (encoder, color) in enumerate(zip(ENCODERS, COLORS)):
                row = cells[encoder, 'matched4', center, method]
                mean, sd = 100*float(row[metric]), 100*float(row[metric+'_seed_sd'])
                x = middle + (e-1)*.48
                y, low, high = .04*mean, .04*(mean-sd), .04*(mean+sd)
                lines.append(f'\\fill[{color}] ({x-.20:.3f},0) rectangle ({x+.20:.3f},{y:.5f});')
                lines.append(f'\\draw[black!80] ({x:.3f},{low:.5f}) -- ({x:.3f},{high:.5f});')
                lines.append(f'\\draw[black!80] ({x-.09:.3f},{low:.5f}) -- ({x+.09:.3f},{low:.5f});')
                lines.append(f'\\draw[black!80] ({x-.09:.3f},{high:.5f}) -- ({x+.09:.3f},{high:.5f});')
            lines.append(f'\\node at ({middle:.3f},-.30) {{{head_label}}};')
        lines.extend([r'\draw (.9,0) -- (7,0);', r'\draw (.9,0) -- (.9,4);', r'\end{scope}'])
    lines.extend([r'\end{tikzpicture}', r'\caption{' + endpoint +
                  ' on the identical custom CAMELYON subset under four-candidate source-only selection. '
                  'Bars show ten-seed means; whiskers show fitting-seed standard deviation, not patient- or hospital-population uncertainty. '
                  'CBMP, linear logistic and trained cosine are prespecified views; all nine heads appear in the accompanying tables.}',
                  r'\label{' + figure_label + '}', r'\end{figure*}'])
    return '\n'.join(lines)+'\n'


