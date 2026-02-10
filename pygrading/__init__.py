"""
    Name: __init__.py
    Author: Charles Zhang <694556046@qq.com>
    Propose: A Python ToolBox for CourseGrading platform
    Coding: UTF-8
"""

from pygrading.job import Job
from pygrading.utils import exec, loge
from pygrading.render import render_template
from pygrading.configuration import load_config
from pygrading.testcase import create_testcase, create_std_testcase, TestCases

__all__ = ["Job", "load_config", "create_testcase", "create_std_testcase", "TestCases",
           "exec", "loge", "render_template", "__main__"]
__version__ = "1.1.8.dev0"
