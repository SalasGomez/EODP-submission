# TEST ENVIRONMENT
# Writes the Python and library versions and the git commit to the report

import os
import sys
import platform
import subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness_utils import ROOT, REPORT

import numpy, scipy, matplotlib, netCDF4, mgrs, pyproj


def gitHash():
    try:
        return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], cwd=ROOT).decode().strip()
    except Exception:
        return 'unknown'


if __name__ == '__main__':
    rows = [('Operating system', platform.platform()),
            ('Python', platform.python_version()),
            ('NumPy', numpy.__version__),
            ('SciPy', scipy.__version__),
            ('Matplotlib', matplotlib.__version__),
            ('netCDF4', netCDF4.__version__),
            ('mgrs', getattr(mgrs, '__version__', '1.5.0')),
            ('pyproj', pyproj.__version__),
            ('Git commit', gitHash())]
    os.makedirs(os.path.join(REPORT, 'tables'), exist_ok=True)
    with open(os.path.join(REPORT, 'tables', 'environment.tex'), 'w') as fid:
        fid.write('\\begin{tabular}{ll}\n\\toprule\nItem & Version \\\\\n\\midrule\n')
        for k, v in rows:
            fid.write(k + ' & \\texttt{' + v.replace('_', '\\_') + '} \\\\\n')
        fid.write('\\bottomrule\n\\end{tabular}\n')
    for k, v in rows:
        print(k, v)
