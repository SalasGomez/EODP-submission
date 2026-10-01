# HARNESS UTILITIES
# Paths, logging, figures and cross-validation shared by all the tests

import os
import sys
import shutil
from datetime import datetime
import numpy as np
from netCDF4 import Dataset

# Repo paths
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CODE = os.path.join(ROOT, 'eodp_students-master')
AUX = os.path.join(CODE, 'auxiliary')
DATA = os.path.join(ROOT, 'EODP_TER_2021')
E2E = os.path.join(ROOT, 'EODP-TS-E2E')
REPORT = os.path.join(ROOT, 'report')
BANDS = ['VNIR-0', 'VNIR-1', 'VNIR-2', 'VNIR-3']

# Make the EODP code importable
if CODE not in sys.path:
    sys.path.insert(0, CODE)

from common.plot.style import setStyle, tex
import matplotlib.pyplot as plt

TOL = 1e-3 # [%] cross-validation threshold


def testDirs(testname, clean=True):
    '''
    Creates the test folders: output, log, figures
    :param testname: e.g. 'EODP-TS-ISM'
    :param clean: remove previous outputs
    :return: dict with the paths
    '''
    base = os.path.join(ROOT, 'harness', testname)
    dirs = {'base': base}
    for d in ['output', 'log', 'figures']:
        dirs[d] = os.path.join(base, d)
        if clean and d != 'figures' and os.path.isdir(dirs[d]):
            shutil.rmtree(dirs[d])
        os.makedirs(dirs[d], exist_ok=True)
    os.makedirs(os.path.join(REPORT, 'figures'), exist_ok=True)
    os.makedirs(os.path.join(REPORT, 'tables'), exist_ok=True)
    return dirs


class HarnessLog:
    '''
    Logger of the test script (file + console).
    Independent of the logging module, which the EODP modules reconfigure.
    '''
    def __init__(self, logfile, name):
        self.logfile = logfile
        self.name = name
        open(self.logfile, 'w').close()

    def write(self, level, msg):
        line = '%s - %s - %-8s - %s' % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), self.name, level, msg)
        print(line)
        with open(self.logfile, 'a') as fid:
            fid.write(line + '\n')

    def info(self, msg):
        self.write('INFO', msg)

    def warning(self, msg):
        self.write('WARNING', msg)


def harnessLogger(dirs, testname):
    '''
    Logger of the test script, saved in the log folder
    '''
    return HarnessLog(os.path.join(dirs['log'], testname + '.log'), 'harness.' + testname)


def moduleDone(logger, dirs, outdir, module):
    '''
    After a module run. Copies the module log.
    '''
    copyModuleLog(dirs, outdir, module)
    logger.info(module + ' finished. Outputs in ' + outdir)


def copyModuleLog(dirs, outdir, module):
    '''
    Copies the module log (e.g. ISM.log) into the log folder
    '''
    src = os.path.join(outdir, module + '.log')
    if os.path.isfile(src):
        shutil.copy(src, os.path.join(dirs['log'], module + '.log'))


def saveFig(fig, dirs, name):
    '''
    Saves a figure in the test figures folder (png) and in the report (pdf)
    '''
    fig.savefig(os.path.join(dirs['figures'], name + '.png'))
    fig.savefig(os.path.join(REPORT, 'figures', name + '.pdf'))
    plt.close(fig)


def readVar(ncfile):
    '''
    Reads the first variable of a NetCDF file
    '''
    dset = Dataset(ncfile)
    var = list(dset.variables)[0]
    mat = np.array(dset.variables[var][:])
    dset.close()
    return mat


def relDiff(ref, mine):
    '''
    Maximum relative difference [%]. Where the reference is 0 the absolute difference is used.
    '''
    ref = np.asarray(ref, dtype=np.float64)
    mine = np.asarray(mine, dtype=np.float64)
    if ref.shape != mine.shape:
        return np.inf
    nz = ref != 0
    d = 0.0
    if np.any(nz):
        d = np.max(np.abs(mine[nz] - ref[nz]) / np.abs(ref[nz])) * 100
    if np.any(~nz):
        d = max(d, np.max(np.abs(mine[~nz])) * 100)
    return d


def crossValidate(refdir, mydir, prefixes, logger):
    '''
    Compares each prefix + band file with the reference
    :return: list of (prefix, band, max rel diff [%], pass)
    '''
    rows = []
    for prefix in prefixes:
        for band in BANDS:
            name = prefix + band + '.nc'
            ref = readVar(os.path.join(refdir, name))
            mine = readVar(os.path.join(mydir, name))
            d = relDiff(ref, mine)
            rows.append((prefix, band, d, d < TOL))
            logger.info('Cross-validation %-22s %s max rel diff %.3e %% %s' %
                        (prefix, band, d, 'PASS' if d < TOL else 'FAIL'))
    return rows


def writeTables(rows, name, caption):
    '''
    Writes the cross-validation results as CSV (harness) and LaTeX (report)
    '''
    with open(os.path.join(REPORT, 'tables', name + '.csv'), 'w') as fid:
        fid.write('file,band,max_rel_diff_percent,pass\n')
        for r in rows:
            fid.write('%s,%s,%.6e,%s\n' % (r[0], r[1], r[2], r[3]))

    # One row per file, one column per band
    prefixes = list(dict.fromkeys(r[0] for r in rows))
    with open(os.path.join(REPORT, 'tables', name + '.tex'), 'w') as fid:
        fid.write('\\begin{longtable}{l' + 'c' * len(BANDS) + 'c}\n')
        fid.write('\\caption{' + caption + '}\\label{tab:' + name + '}\\\\\n\\toprule\n')
        fid.write('File & ' + ' & '.join(BANDS) + ' & Result \\\\\n\\midrule\n\\endfirsthead\n')
        fid.write('\\toprule\nFile & ' + ' & '.join(BANDS) + ' & Result \\\\\n\\midrule\n\\endhead\n')
        for p in prefixes:
            vals = [r for r in rows if r[0] == p]
            ok = all(r[3] for r in vals)
            fid.write('\\texttt{' + p.replace('_', '\\_') + '} & ' +
                      ' & '.join(fmtSci(r[2]) for r in vals) +
                      ' & ' + ('Pass' if ok else 'Fail') + ' \\\\\n')
        fid.write('\\bottomrule\n\\end{longtable}\n')


def fmtSci(x):
    '''
    Number in LaTeX scientific notation
    '''
    if x == 0:
        return '$0$'
    m, e = ('%.2e' % x).split('e')
    return '$' + m + '\\times10^{' + str(int(e)) + '}$'
