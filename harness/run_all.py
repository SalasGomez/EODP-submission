# RUN ALL THE TESTS
# Runs the four tests and the environment script in order. Stops on the first error.

import os
import sys
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = [os.path.join('EODP-TS-ISM', 'test_ism.py'),
           os.path.join('EODP-TS-L1B', 'test_l1b.py'),
           os.path.join('EODP-TS-L1C', 'test_l1c.py'),
           os.path.join('EODP-TS-E2E', 'test_e2e.py'),
           os.path.join('common', 'environment.py')]

if __name__ == '__main__':
    for s in SCRIPTS:
        print('==== Running ' + s)
        res = subprocess.run([sys.executable, os.path.join(HERE, s)], cwd=os.path.dirname(HERE))
        if res.returncode != 0:
            sys.exit('Error in ' + s)
    print('==== All tests finished')
