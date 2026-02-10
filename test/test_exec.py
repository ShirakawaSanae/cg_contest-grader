import unittest
import pygrading as gg
from subprocess import TimeoutExpired
from pygrading.exception import ExecError


class TestExec(unittest.TestCase):
    def test_exec(self):
        try:
            gg.exec("sleep 2", time_out=1)
        except TimeoutExpired:
            print("exec超时功能正常")

        gg.exec("asdsad", queit=True)
        print("exec静默模式正常")

        try:
            gg.exec("asdsad", queit=False)
        except ExecError as e:
            print("exec关闭静默模式正常")
            print(e)

    def test_dict(self):
        stdout = "a=1\nb = 2\nc=3\neafafd"
        dic = gg.utils.get_result_dict(stdout, "=")
        print(dic)
