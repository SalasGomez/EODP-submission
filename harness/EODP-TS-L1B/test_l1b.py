# EODP-TS-L1B
# Runs the L1B with and without equalization, cross-validates with the
# reference outputs and generates the calibration plot.

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
from harness_utils import *

from l1b.src.l1b import l1b

TEST = 'EODP-TS-L1B'
INDIR = os.path.join(DATA, TEST, 'input')
REFDIR = os.path.join(DATA, TEST, 'output')


def runL1b(dirs, logger, equalization):
    '''
    Runs the L1B. Outputs in output/eq or output/noeq
    '''
    outdir = os.path.join(dirs['output'], 'eq' if equalization else 'noeq')
    logger.info('Running the L1B with do_equalization=' + str(equalization))
    myL1b = l1b(AUX, INDIR, outdir)
    myL1b.l1bConfig.do_equalization = equalization
    myL1b.processModule()
    moduleDone(logger, dirs, outdir, 'L1B')
    if not equalization:
        os.replace(os.path.join(dirs['log'], 'L1B.log'), os.path.join(dirs['log'], 'L1B_noeq.log'))
    return outdir


def crossValidation(dirs, eqdir, logger):
    rows = crossValidate(REFDIR, eqdir, ['l1b_toa_eq_', 'l1b_toa_'], logger)
    writeTables(rows, 'l1b_crossval', 'L1B cross-validation with equalization. Maximum relative difference [\\%] per band.')
    ok = all(r[3] for r in rows)
    logger.info('L1B cross-validation ' + ('PASSED' if ok else 'FAILED'))
    return ok


if __name__ == '__main__':
    dirs = testDirs(TEST)
    logger = harnessLogger(dirs, TEST)
    noeqdir = runL1b(dirs, logger, False)
    eqdir = runL1b(dirs, logger, True)
    crossValidation(dirs, eqdir, logger)
    logger.info('End of ' + TEST)
