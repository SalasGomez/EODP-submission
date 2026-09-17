
from config.loadConfig import loadConfig
from common.src.baseModule import baseModule
from common.io.fileExists import fileExists, addFileSep
import os


class initL1b(baseModule):
    def __init__(self, auxdir, indir, outdir):

        # Initialise baseModule (the log, etc.)
        super().__init__(auxdir, indir, outdir, "L1B")

        # Init Local config
        self.l1bConfig = loadConfig("l1bConfig")

        # Make sure the logger is enabled
        self.logger.disabled = False
