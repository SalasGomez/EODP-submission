# MAIN FUNCTION TO CALL THE L1B MODULE

import os
import sys

# Code root and repo root
codedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rootdir = os.path.dirname(codedir)
sys.path.insert(0, codedir)

from l1b.src.l1b import l1b

# Directory - this is the common directory for the execution of the E2E, all modules
auxdir = os.path.join(codedir, 'auxiliary')
indir = os.path.join(rootdir, 'EODP_TER_2021', 'EODP-TS-L1B', 'input')
outdir = os.path.join(rootdir, 'EODP_TER_2021', 'EODP-TS-L1B', 'myoutput')

# Initialise the L1B
myL1b = l1b(auxdir, indir, outdir)
myL1b.processModule()
