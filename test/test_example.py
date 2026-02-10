import unittest
import pygrading as gg

from pygrading import Job
from pygrading import TestCases


class TestExample(unittest.TestCase):
    def test_complex(self):

        import multiprocessing

        cpu_core_num = multiprocessing.cpu_count()

        def prework(job: Job):
            testcase = gg.create_testcase(100)
            testcase.append("TestCase1", 25)
            testcase.append("TestCase2", 25)
            testcase.append("TestCase3", 25)
            testcase.append("TestCase4", 25)

            job.set_testcases(testcase)

        def run(job: Job, case: TestCases.SingleTestCase):
            result = {"verdict": "WA", "score": 0}
            if case.score == 25:
                result["verdict"] = "AC"
                result["score"] = 25

            gg.exec("sleep 1", time_out=2)

            return result

        def postwork(job: Job):

            total_score = job.get_total_score()

            job.score(total_score)
            if total_score == 100:
                job.verdict("AC")

            comment = ""
            for ret in job.get_summary():
                comment += str(ret)

            job.comment(comment)
            job.detail("Well Done in detail!")
            job.secret("Well Done in secret")

        new_job = gg.Job(prework=prework, run=run, postwork=postwork)
        new_job.start(max_workers=cpu_core_num)
        new_job.print()
