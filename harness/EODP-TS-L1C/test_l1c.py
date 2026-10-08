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


def plotGrids(dirs, logger):
    '''
    L1B and L1C grids in the same plot, full scene and zoom on a corner
    '''
    lat, lon = readGeodetic(GMDIR, 'geolocation.nc')
    t1, la1, lo1 = readL1c(dirs['output'], 'l1c_toa_VNIR-0.nc')
    fig, axs = plt.subplots(1, 2, figsize=(15, 7))
    for ax in axs:
        ax.plot(lon.flatten(), lat.flatten(), '.b', markersize=3, label='L1B grid')
        ax.plot(lo1, la1, '.r', markersize=3, label='L1C grid (MGRS 100 m)')
        ax.set_xlabel('Longitude [deg]')
        ax.set_ylabel('Latitude [deg]')
        ax.grid(True)
    axs[0].set_title('L1B and L1C grids')
    axs[0].legend(loc='upper right', numpoints=1, markerscale=4, fontsize=11)
    # Zoom on the corner of the last line and first column
    axs[1].set_xlim(lon[-1, 0] - 0.002, lon[-1, 0] + 0.008)
    axs[1].set_ylim(lat[-1, 0] - 0.003, lat[-1, 0] + 0.007)
    axs[1].set_title('Zoom on the west corner')
    saveFig(fig, dirs, 'l1c_grids')
    logger.info('L1B points %d, L1C points %d' % (lat.size, la1.size))


def gsd(dirs, logger):
    '''
    L1B ground sampling distance ACT (central line) and ALT (central column)
    with the Haversine distance between consecutive pixels
    '''
    lat, lon = readGeodetic(GMDIR, 'geolocation.nc')
    ialt, iact = int(lat.shape[0] / 2), int(lat.shape[1] / 2)
    gsd_act = np.array([haversine(lat[ialt, i], lon[ialt, i], lat[ialt, i + 1], lon[ialt, i + 1])
                        for i in range(lat.shape[1] - 1)])
    gsd_alt = np.array([haversine(lat[i, iact], lon[i, iact], lat[i + 1, iact], lon[i + 1, iact])
                        for i in range(lat.shape[0] - 1)])

    fig = plt.figure(figsize=(10, 6))
    plt.plot(gsd_act, '-b', label='ACT, central line %d' % ialt)
    plt.plot(gsd_alt, '-r', label='ALT, central column %d' % iact)
    plt.title('L1B ground sampling distance')
    plt.xlabel('Pixel index [-]')
    plt.ylabel('Distance between consecutive pixels [m]')
    plt.legend(loc='best', fontsize=11)
    plt.grid(True)
    saveFig(fig, dirs, 'l1c_gsd')

    with open(os.path.join(REPORT, 'tables', 'l1c_gsd.tex'), 'w') as fid:
        fid.write('\\begin{tabular}{lccc}\n\\toprule\n')
        fid.write('Direction & Mean [m] & Min. [m] & Max. [m] \\\\\n\\midrule\n')
        for lab, g in [('ACT', gsd_act), ('ALT', gsd_alt)]:
            fid.write('%s & %.2f & %.2f & %.2f \\\\\n' % (lab, np.mean(g), np.min(g), np.max(g)))
            logger.info('GSD %s mean %.3f m, min %.3f m, max %.3f m' % (lab, np.mean(g), np.min(g), np.max(g)))
        fid.write('\\bottomrule\n\\end{tabular}\n')


if __name__ == '__main__':
    dirs = testDirs(TEST)
    logger = harnessLogger(dirs, TEST)
    conf = runL1c(dirs, logger)
    crossValidation(dirs, logger)
    plotGrids(dirs, logger)
    gsd(dirs, logger)
    logger.info('End of ' + TEST)
