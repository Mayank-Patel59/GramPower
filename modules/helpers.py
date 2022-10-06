# -*- coding: utf-8 -*-

from types import SimpleNamespace
import configparser
import re
import json

from pathlib import Path

import logging
from modules.loggers import Loggers


class Helper(Loggers):

    def __init__(self):
        super().__init__()

        # Purpose of taking the path & json file
        path = Path(str(Path.cwd()))
        path = path / 'docs'
        self.config_file = path / 'conf.ini'
        self.json_schema_file = path / "new_MR_schema_1.json"

        name = __class__.__name__

        extra = {'className': name}

        self.logger_info = logging.LoggerAdapter(self.logger1, extra)

        self.logger_err = logging.LoggerAdapter(self.logger2, extra)

    def read_config(self):
        config = configparser.ConfigParser()
        ini_file = self.config_file
        config.read(ini_file)
        return config

    def get_Schema(self):
        file = self.json_schema_file
        with open(file, 'r') as f:
            schema = json.load(f)

        # filename2=path/"new_MR_schema_2.json"
        # with open(filename2, 'r') as f:
        #     schema2 = json.load(f)

        return schema

    def clean(self, fields):
        new_fields = []

        for f in fields:
            # Remove invalid characters
            s = re.sub('[^0-9a-zA-Z_]', '', f)

            # Remove leading characters until we find a letter or underscore
            s = re.sub('^[^a-zA-Z_]+', '', s)
            new_fields.append(s)

            self.meterRaw_doc[f] = s

        new_dict = dict.fromkeys(new_fields, None)

        self.doc = SimpleNamespace(**new_dict)
