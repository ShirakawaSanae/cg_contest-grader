import time
import unittest
import pygrading as gg
from pygrading import Job, TestCases
from pygrading.exception import FunctionArgsError

from datetime import datetime


class TestRun(unittest.TestCase):
    def test_Run(self):

        def prework(job: Job):
            print("I am in prework!")

            testcases = gg.create_testcase()
            testcases.append("TestCase1", 20)
            testcases.append("TestCase2", 20)
            testcases.append("TestCase3", 20)
            testcases.append("TestCase4", 20)
            job.set_testcases(testcases)

        def run(job: Job, case: TestCases.SingleTestCase):
            print("I am in run!")
            time.sleep(0.05)
            return "123"

        def postwork(job):
            print("I am in postwork!")
            results = job.get_summary()

            for i in results:
                print(i)

        job = gg.Job(prework=prework, run=run, postwork=postwork)

        start_time = datetime.now()
        job.start(4)
        end_time = datetime.now()
        time_with_thread = (end_time - start_time).total_seconds()

        start_time = datetime.now()
        job.start()
        end_time = datetime.now()
        time_without_thread = (end_time - start_time).total_seconds()

        print(f"time_with_thread: {time_with_thread}")
        print(f"time_without_thread: {time_without_thread}")

        if time_without_thread // time_with_thread < 3:
            raise Exception("多线程模式启动失败")

        job.print()
        print("测试任务基本运行通过")

    def test_prework_agrs(self):

        def prework():
            print("I am in prework!")

        job = gg.Job(prework=prework)
        job.start()
        print("Prework空参数测试通过")

        def prework(job: Job):
            print("I am in prework!")

        job = gg.Job(prework=prework)
        job.start()
        print("Prework带参数测试通过")

        try:
            def prework(job: Job, asd):
                print("I am in prework!")

            job = gg.Job(prework=prework)
            job.start()
        except FunctionArgsError:
            print("Prework多参数异常测试通过")

    def test_run_args(self):
        def run():
            print("I am in run!")

        job = gg.Job(run=run)
        job.start()
        print("run不带参数测试通过")

        def run(job: Job):
            print("I am in run!" + job.get_total_score())

        job = gg.Job(run=run)
        job.start()
        print("run带job参数测试通过")

        testcase = gg.create_testcase(100)
        testcase.append("test1", 100)

        def run(case: TestCases.SingleTestCase):
            print("I am in run!" + case.name)

        job = gg.Job(run=run)
        job.set_testcases(testcase)
        job.start()
        print("run带test参数测试通过")

        def run(job: Job, case: TestCases.SingleTestCase):
            print("I am in run!" + case.name)

        job = gg.Job(run=run)
        job.set_testcases(testcase)
        job.start()
        print("run带两个参数测试通过")

        try:
            def run(job: Job, case: TestCases.SingleTestCase, qwewqe):
                print("I am in run!" + case.name)

            job = gg.Job(run=run)
            job.set_testcases(testcase)
            job.start()
            print(job.get_summary())
        except FunctionArgsError:
            print("run多参数异常测试通过")

    def test_post_args(self):
        def postwork():
            print("I am in postwork!")

        job = gg.Job(postwork=postwork)
        job.start()
        print("Postwork空参数测试通过")

        def postwork(job: Job):
            print("I am in postwork!")

        job = gg.Job(postwork=postwork)
        job.start()
        print("Postwork带参数测试通过")

        try:
            def postwork(job: Job, asd):
                print("I am in prework!")

            job = gg.Job(postwork=postwork)
            job.start()
        except FunctionArgsError:
            print("Postwork多参数异常测试通过")
