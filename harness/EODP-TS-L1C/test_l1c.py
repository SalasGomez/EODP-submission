# EODP-TS-L1C
# Runs the L1C, compares with the reference matching the points by
# coordinates, plots the L1B/L1C grids and computes the L1B GSD.

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
from harness_utils import *

from scipy.spatial import cKDTree
from l1c.src.l1c import l1c
from common.io.l1cProduct import readL1c
from common.io.readGeodetic import readGeodetic
from common.src.auxGeom import haversine

TEST = 'EODP-TS-L1C'
GMDIR = os.path.join(DATA, TEST, 'input', 'gm_alt100_act_150')
L1BDIR = os.path.join(DATA, TEST, 'input', 'l1b_output')
REFDIR = os.path.join(DATA, TEST, 'output')


def runL1c(dirs, logger):
    logger.info('Running the L1C. Inputs ' + GMDIR + ' and ' + L1BDIR)
    myL1c = l1c(AUX, GMDIR + ',' + L1BDIR, dirs['output'])
    myL1c.processModule()
    moduleDone(logger, dirs, dirs['output'], 'L1C')
    return myL1c.l1cConfig


def crossValidation(dirs, logger):
    '''
    The order of the L1C points changes in each run (set of MGRS tiles),
    so each reference point is matched with the closest output point.
    '''
    rows = []
    for band in BANDS:
        name = 'l1c_toa_' + band + '.nc'
        t0, la0, lo0 = readL1c(REFDIR, name)
        t1, la1, lo1 = readL1c(dirs['output'], name)
        dist, idx = cKDTree(np.c_[la1, lo1]).query(np.c_[la0, lo0])
        unique = len(np.unique(idx)) == len(t0) == len(t1)
        d = relDiff(t0, t1[idx])
        dmax = np.max(dist) * np.pi / 180 * 6378137 # [m] approx.
        ok = unique and d < TOL
        rows.append((band, len(t0), len(t1), dmax, d, ok))
        logger.info('%s points ref %d mine %d, max coord. distance %.3e m, max rel diff %.3e %% %s' %
                    (band, len(t0), len(t1), dmax, d, 'PASS' if ok else 'FAIL'))

    with open(os.path.join(REPORT, 'tables', 'l1c_crossval.tex'), 'w') as fid:
        fid.write('\\begin{tabular}{lccccc}\n\\toprule\n')
        fid.write('Band & Points ref. & Points output & Max. distance [m] & Max. rel. diff. [\\%] & Result \\\\\n\\midrule\n')
        for r in rows:
            fid.write('%s & %d & %d & %s & %s & %s \\\\\n' %
                      (r[0], r[1], r[2], fmtSci(r[3]), fmtSci(r[4]), 'Pass' if r[5] else 'Fail'))
        fid.write('\\bottomrule\n\\end{tabular}\n')
    logger.info('L1C cross-validation ' + ('PASSED' if all(r[5] for r in rows) else 'FAILED'))


if __name__ == '__main__':
    dirs = testDirs(TEST)
    logger = harnessLogger(dirs, TEST)
    conf = runL1c(dirs, logger)
    crossValidation(dirs, logger)
    logger.info('End of ' + TEST)
