# MAIN FUNCTION TO CALL THE L1C MODULE

import os
import sys

# Code root and repo root
codedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rootdir = os.path.dirname(codedir)
sys.path.insert(0, codedir)

from l1c.src.l1c import l1c

# Directory - this is the common directory for the execution of the E2E, all modules
auxdir = os.path.join(codedir, 'auxiliary')
# GM dir + L1B dir
testdir = os.path.join(rootdir, 'EODP_TER_2021', 'EODP-TS-L1C')
indir = os.path.join(testdir, 'input', 'gm_alt100_act_150') + ',' + os.path.join(testdir, 'input', 'l1b_output')
outdir = os.path.join(testdir, 'myoutput')

# Initialise the L1C
myL1c = l1c(auxdir, indir, outdir)
myL1c.processModule()
