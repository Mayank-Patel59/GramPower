# -*- coding: utf-8 -*-

import logging
from logging import config as cfg
import os
from pathlib import Path


class Loggers(object):
    path = Path(str(Path.cwd()))
    path = path / 'logs'
    if not os.path.exists(path):
        os.makedirs(path)

    cfg.fileConfig('./docs/conf.ini')

    @property
    def logger1(self):
        # name = __class__.__name__
        logger = logging.getLogger("logger_info")
        return logger

    @property
    def logger2(self):
        # name = __class__.__name__
        logger = logging.getLogger("logger_err")

        return logger
