# EODP-TS-E2E
# End-to-end run on the FLEX scene over the Pyrenees: ISM -> L1B -> L1C,
# each module reading the outputs of the previous one.
# Uses the E2E configuration (EODP-TS-E2E/config). No reference comparison.

import os
import sys
import time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
from harness_utils import *

# E2E configuration, set before the modules load their config
os.environ['EODP_CONFIG_DIR'] = os.path.join(E2E, 'config')

from ism.src.ism import ism
from l1b.src.l1b import l1b
from l1c.src.l1c import l1c
from config.loadConfig import loadConfig

TEST = 'EODP-TS-E2E'
SGMDIR = os.path.join(E2E, 'sgm_out')
GMDIR = os.path.join(E2E, 'gm_out')


def runChain(dirs, logger, run_l1c=True):
    '''
    ISM, L1B and L1C in a row. Outputs in output/ism, output/l1b, output/l1c
    '''
    conf = loadConfig('ismConfig')
    logger.info('E2E config: pix_size %.1e m, t_int %.4f s, D %.5f m, f %.4f m, PRNU %s, DS %s, bad/dead %s' %
                (conf.pix_size, conf.t_int, conf.D, conf.f, conf.apply_prnu, conf.apply_dark_signal, conf.apply_bad_dead))
    logger.info('L1B do_equalization %s' % loadConfig('l1bConfig').do_equalization)

    out = {m: os.path.join(dirs['output'], m) for m in ['ism', 'l1b', 'l1c']}

    t0 = time.time()
    logger.info('Running the ISM. Input ' + SGMDIR)
    ism(AUX, SGMDIR, out['ism']).processModule()
    moduleDone(logger, dirs, out['ism'], 'ISM')
    logger.info('ISM time %.0f s' % (time.time() - t0))

    t0 = time.time()
    logger.info('Running the L1B. Input ' + out['ism'])
    l1b(AUX, out['ism'], out['l1b']).processModule()
    moduleDone(logger, dirs, out['l1b'], 'L1B')
    logger.info('L1B time %.0f s' % (time.time() - t0))

    if run_l1c:
        t0 = time.time()
        logger.info('Running the L1C. Inputs ' + GMDIR + ' and ' + out['l1b'])
        l1c(AUX, GMDIR + ',' + out['l1b'], out['l1c']).processModule()
        moduleDone(logger, dirs, out['l1c'], 'L1C')
        logger.info('L1C time %.0f s' % (time.time() - t0))
    return out


if __name__ == '__main__':
    dirs = testDirs(TEST, clean='--plots-only' not in sys.argv)
    logger = harnessLogger(dirs, TEST)
    if '--plots-only' not in sys.argv:
        out = runChain(dirs, logger, run_l1c='--no-l1c' not in sys.argv)
    logger.info('End of ' + TEST)
