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


def readGeo():
    '''
    Latitude, longitude and altitude of the scene
    '''
    dset = Dataset(os.path.join(GMDIR, 'geolocation.nc'))
    proj = dset.groups['projection']
    lat = np.array(proj.variables['latitude'][:])
    lon = np.array(proj.variables['longitude'][:])
    alt = np.array(proj.variables['altitude'][:])
    dset.close()
    return lat, lon, alt


def plotAltitude(dirs, logger):
    '''
    Altitude on the map. Common to all the bands.
    '''
    lat, lon, alt = readGeo()
    fig = plt.figure(figsize=(10, 8))
    pc = plt.pcolormesh(lon, lat, alt, cmap='terrain', shading='auto', rasterized=True)
    plt.colorbar(pc, label='Altitude [m]')
    plt.title('Scene altitude')
    plt.xlabel('Longitude [deg]')
    plt.ylabel('Latitude [deg]')
    saveFig(fig, dirs, 'e2e_altitude')
    logger.info('Altitude min %.1f m, max %.1f m. Lat [%.3f, %.3f], lon [%.3f, %.3f]' %
                (np.min(alt), np.max(alt), np.min(lat), np.max(lat), np.min(lon), np.max(lon)))


def plotL1bBands(dirs, logger):
    '''
    For each band, the L1B TOA on the map and its histogram (bins of 0.1)
    '''
    lat, lon, alt = readGeo()
    l1bdir = os.path.join(dirs['output'], 'l1b')
    for band in BANDS:
        toa = readVar(os.path.join(l1bdir, 'l1b_toa_' + band + '.nc'))
        fig, axs = plt.subplots(1, 2, figsize=(16, 6.5), gridspec_kw={'width_ratios': [1.1, 1]})
        pc = axs[0].pcolormesh(lon, lat, toa, cmap='jet', shading='auto', rasterized=True)
        fig.colorbar(pc, ax=axs[0], label=r'TOA [mW/m$^2$/sr]')
        axs[0].set_title('L1B TOA ' + band)
        axs[0].set_xlabel('Longitude [deg]')
        axs[0].set_ylabel('Latitude [deg]')

        bins = np.arange(np.floor(np.min(toa)), np.max(toa) + 0.1, 0.1)
        axs[1].hist(toa.flatten(), bins=bins, color='b', edgecolor='none')
        axs[1].set_title('Histogram L1B TOA ' + band + ' (bin 0.1)')
        axs[1].set_xlabel(r'TOA [mW/m$^2$/sr]')
        axs[1].set_ylabel('Number of pixels [-]')
        axs[1].grid(True)
        saveFig(fig, dirs, 'e2e_l1b_' + band)
        logger.info('%s L1B TOA min %.3f, max %.3f, mean %.3f mW/m2/sr' %
                    (band, np.min(toa), np.max(toa), np.mean(toa)))


def radiometricCheck(dirs, logger):
    '''
    The L1B should recover the input radiance: mean ism_toa_isrf vs mean l1b_toa
    '''
    rows = []
    for band in BANDS:
        isrf = readVar(os.path.join(dirs['output'], 'ism', 'ism_toa_isrf_' + band + '.nc'))
        toa = readVar(os.path.join(dirs['output'], 'l1b', 'l1b_toa_' + band + '.nc'))
        dn = readVar(os.path.join(dirs['output'], 'ism', 'ism_toa_' + band + '.nc'))
        d = (np.mean(toa) - np.mean(isrf)) / np.mean(isrf) * 100
        sat = np.mean(dn >= 4095) * 100
        rows.append((band, np.mean(isrf), np.mean(toa), d, sat))
        logger.info('%s mean ISRF TOA %.4f, mean L1B TOA %.4f, diff %.3f %%, saturated %.2f %%' % rows[-1])
    with open(os.path.join(REPORT, 'tables', 'e2e_radiometry.tex'), 'w') as fid:
        fid.write('\\begin{tabular}{lcccc}\n\\toprule\n')
        fid.write('Band & Mean ISRF TOA & Mean L1B TOA & Difference [\\%] & Saturated [\\%] \\\\\n\\midrule\n')
        for r in rows:
            fid.write('%s & %.4f & %.4f & %.3f & %.2f \\\\\n' % r)
        fid.write('\\bottomrule\n\\end{tabular}\n')


def extraCheck(dirs, logger):
    '''
    Optional. Compares with the ISM and L1B outputs provided in EODP-TS-E2E,
    when they are available. Not required for the E2E test.
    '''
    rows = []
    for mod, prefixes in [('ism', ['ism_toa_isrf_', 'ism_toa_optical_', 'ism_toa_e_', 'ism_toa_detection_', 'ism_toa_']),
                          ('l1b', ['l1b_toa_'])]:
        refdir = os.path.join(E2E, mod + '_out')
        if not os.path.isdir(refdir):
            logger.info('No provided outputs in ' + refdir)
            return
        rows += crossValidate(refdir, os.path.join(dirs['output'], mod), prefixes, logger)
    writeTables(rows, 'e2e_crossval', 'E2E. Comparison with the ISM and L1B outputs provided with the E2E data. Maximum relative difference [\\%] per band.')


if __name__ == '__main__':
    dirs = testDirs(TEST, clean='--plots-only' not in sys.argv)
    logger = harnessLogger(dirs, TEST)
    if '--plots-only' not in sys.argv:
        out = runChain(dirs, logger, run_l1c='--no-l1c' not in sys.argv)
    plotAltitude(dirs, logger)
    plotL1bBands(dirs, logger)
    radiometricCheck(dirs, logger)
    extraCheck(dirs, logger)
    logger.info('End of ' + TEST)
