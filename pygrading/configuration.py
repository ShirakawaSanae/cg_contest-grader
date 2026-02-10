"""
    Name: configuration.py
    Author: Charles Zhang <694556046@qq.com>
    Propose: A module to load config file.
    Coding: UTF-8
"""

import json
import os
from typing import Dict


def load_config(source: str) -> Dict:
    """Load Configuration File

    Reads the configuration file and returns it as a dictionary.

    Args:
        source: Configuration file path.

    Returns:
        A dict of config information.

        For example:
        {'testcase_num': '3',
        'testcase_dir': 'example/testdata',
        'submit_path': 'example/submit/*',
        'exec_path': 'example/exec/student.exec'}

    Raises:
        IOError: A error occurred when missing config file.
    """
    f = open(source, encoding='utf-8')
    return json.load(f)


class Config(dict):
    SUBMIT = "submit_dir"
    TESTCASE = "testcase_dir"

    def __init__(self, config=None):
        super().__init__()
        self[self.SUBMIT] = "/coursegrader/submit"
        self[self.TESTCASE] = "/coursegrader/testdata"
        self["debug"] = False
        if config:
            self.update(config)

    def load(self, config_src: str = None):
        if os.environ.get("CONFIG_SRC"):
            self.update(load_config(os.environ.get("CONFIG_SRC")))
        if not config_src:
            config_src = os.path.join(self[self.TESTCASE], "config.json")
        if os.path.exists(config_src):
            self.update(load_config(config_src))

    @property
    def is_debug(self):
        return self['debug']

    @property
    def testcase_dir(self):
        return self[self.TESTCASE]

    @property
    def submit_dir(self):
        return self[self.SUBMIT]

