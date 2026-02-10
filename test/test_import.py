import unittest
import pygrading as gg


class TestImport(unittest.TestCase):
    def test_import(self):
        try:
            print(gg.__version__)
        except Exception:
            raise AssertionError("Import PyGrading Failed!")
