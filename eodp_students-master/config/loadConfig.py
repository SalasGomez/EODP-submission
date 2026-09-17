# CONFIGURATION LOADER
# Uses the config files in EODP_CONFIG_DIR if set, else the default ones

import os
import importlib
import importlib.util

def loadConfig(name):
    '''
    Returns an instance of the config class
    :param name: config class name (same as the file), e.g. 'ismConfig'
    :return: config object
    '''
    confdir = os.environ.get('EODP_CONFIG_DIR')
    if confdir:
        spec = importlib.util.spec_from_file_location(name, os.path.join(confdir, name + '.py'))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    else:
        mod = importlib.import_module('config.' + name)
    return getattr(mod, name)()
