import unittest
import pygrading as gg

from pygrading.exception import FunctionsTypeError, DataTypeError, FieldMissingError


class TestJob(unittest.TestCase):
    def test_job_create(self):
        try:
            gg.Job(prework=123)
        except gg.exception.FunctionsTypeError as e:
            print("捕获传入函数类型错误成功！" + str(e))

        try:
            gg.Job(run="1231")
        except gg.exception.FunctionsTypeError as e:
            print("捕获传入函数类型错误成功！" + str(e))

        try:
            gg.Job(postwork=True)
        except gg.exception.FunctionsTypeError as e:
            print("捕获传入函数类型错误成功！" + str(e))

        try:
            gg.Job(prework=None, run=None, postwork=None)
            print("Job接收空参数任务成功")
        except FunctionsTypeError as e:
            raise e

        def prework():
            print("I am from prework!")

        def run():
            print("I an from run!")

        def postwork():
            print("I am from postwork")

        try:
            gg.Job(prework=prework, run=run, postwork=postwork)
            print("Job接收正常参数任务成功")
        except FunctionsTypeError as e:
            raise e

    def test_job_json(self):
        job = gg.Job()
        job.print()

        self.assertEqual(
            job.print(return_str=True),
            """{"verdict": "Unknown", "score": "0", "rank": {"rank": "-1.0"}, "HTML": "enable"}"""
        )

        job.verdict("Accepted")
        job.print()

        self.assertEqual(
            job.print(return_str=True),
            """{"verdict": "Accepted", "score": "0", "rank": {"rank": "-1.0"}, "HTML": "enable"}"""
        )

        job.score(100)
        job.print()

        self.assertEqual(
            job.print(return_str=True),
            """{"verdict": "Accepted", "score": "100", "rank": {"rank": "-1.0"}, "HTML": "enable"}"""
        )

        try:
            job.score(100.00)
        except DataTypeError:
            print("检测score字段为浮点数的错误成功")
            job.score(100)

        job.rank({"rank": "-1", "test1": "0.5"})
        job.print()

        self.assertEqual(
            job.print(return_str=True),
            """{"verdict": "Accepted", "score": "100", "rank": {"rank": "-1.0", "test1": "0.5"}, "HTML": "enable"}"""
        )

        try:
            job.rank({"test1": "0.5"})
        except FieldMissingError:
            print("捕获缺失rank值错误成功！")

        try:
            job.rank({"rank": "-1", "test1": "hello"})
        except DataTypeError:
            print("捕获rank值不为浮点数错误成功！")

        job.rank({"rank": "-1"})
        job.comment("test")
        job.print()

        self.assertEqual(
            job.print(return_str=True),
            """{"verdict": "Accepted", "score": "100", "rank": {"rank": "-1.0"}, "HTML": "enable", "comment": "test"}"""
        )

        job.comment("123")
        job.print()

        self.assertEqual(
            job.print(return_str=True),
            """{"verdict": "Accepted", "score": "100", "rank": {"rank": "-1.0"}, "HTML": "enable", "comment": "123"}"""
        )
        print("正确将comment中数字类型转化为字符串")

        job.comment("")
        job.print()

        self.assertEqual(
            job.print(return_str=True),
            """{"verdict": "Accepted", "score": "100", "rank": {"rank": "-1.0"}, "HTML": "enable"}"""
        )
        print("正确删除comment字段")

        job.detail("test")
        job.print()

        self.assertEqual(
            job.print(return_str=True),
            """{"verdict": "Accepted", "score": "100", "rank": {"rank": "-1.0"}, "HTML": "enable", "detail": "test"}"""
        )

        job.detail("123")
        job.print()

        self.assertEqual(
            job.print(return_str=True),
            """{"verdict": "Accepted", "score": "100", "rank": {"rank": "-1.0"}, "HTML": "enable", "detail": "123"}"""
        )
        print("正确将detail中数字类型转化为字符串")

        job.detail("")
        job.print()

        self.assertEqual(
            job.print(return_str=True),
            """{"verdict": "Accepted", "score": "100", "rank": {"rank": "-1.0"}, "HTML": "enable"}"""
        )
        print("正确删除detail字段")

        job.secret("test")
        job.print()

        self.assertEqual(
            job.print(return_str=True),
            """{"verdict": "Accepted", "score": "100", "rank": {"rank": "-1.0"}, "HTML": "enable", "secret": "test"}"""
        )

        job.secret("123")
        job.print()

        self.assertEqual(
            job.print(return_str=True),
            """{"verdict": "Accepted", "score": "100", "rank": {"rank": "-1.0"}, "HTML": "enable", "secret": "123"}"""
        )
        print("正确将secret中数字类型转化为字符串")

        job.secret("")
        job.print()

        self.assertEqual(
            job.print(return_str=True),
            """{"verdict": "Accepted", "score": "100", "rank": {"rank": "-1.0"}, "HTML": "enable"}"""
        )
        print("正确删除secret字段")

        job.comment("test")
        job.detail("test")
        job.secret("test")
        job.print()
        self.assertEqual(
            job.print(return_str=True),
            """{"verdict": "Accepted", "score": "100", "rank": {"rank": "-1.0"}, """ +
            """"HTML": "enable", "comment": "test", "detail": "test", "secret": "test"}"""
        )
        print("正确添加所有字段字段")
