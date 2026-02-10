import unittest
import pygrading as gg

from cg_learning.models import Verb, Statement, Activity
from cg_learning.tracker import track_grading_enable_config_key, \
    new_statement_instance, get_current_statement, track_debug_config_key, \
    get_statements_queue, clear_statements_queue, \
    track_auth_jwt_config_key, default_concept_domain, build_the_verb, submit_statement, track_lrs_endpoint_config_key
from pygrading import Job, TestCases

test_track_config = {track_grading_enable_config_key: True,
                     track_auth_jwt_config_key: "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9."
                                                "eyJpc3MiOiJodHRwOi8vbGVhcm5pbmcuZWR1Y2"
                                                "cubmV0IiwibmFtZSI6IlB5dGhvbiBHcmFkaW5n"
                                                "IEtlcm5lbCJ9.pf0vDkYc4TTgCUhxpCIobv7ST7NcMPovDWihidxzYBg",
                     track_debug_config_key: True}


def prework(job: Job):
    testcases = gg.create_testcase()
    testcases.append("TestCase1", 20)
    testcases.append("TestCase2", 30)
    testcases.append("TestCase3", 25)
    testcases.append("TestCase4", 25)
    job.set_testcases(testcases)


def run_with_only_case_param(case: TestCases.SingleTestCase):
    import random
    score = random.uniform(0, case.score)
    print(f"{case.name} get score : {score}")
    return score


def run_with_job_and_case_params(job: Job, case: TestCases.SingleTestCase):
    return run_with_only_case_param(case)


def run_with_only_job_param(job: Job):
    return True


def run_with_no_params():
    return True


def basic_check_track_result(job: Job):
    testcases = job.get_testcases()
    statements = get_statements_queue()
    statements_len = len(list(statements))
    # all statement id should be unique
    assert len(set(statement.statement_id for statement in statements)) == statements_len
    # a root statement and all case statement
    assert statements_len == len(testcases) + 1


class TestTracker(unittest.TestCase):

    def tearDown(self):
        clear_statements_queue()

    def test_multi_form_run_def(self):
        job = gg.Job(prework=prework, run=run_with_no_params, config=test_track_config)
        job.start()
        job.print()
        basic_check_track_result(job)
        clear_statements_queue()

        job = gg.Job(prework=prework, run=run_with_only_case_param, config=test_track_config)
        job.start()
        job.print()
        basic_check_track_result(job)
        clear_statements_queue()

        job = gg.Job(prework=prework, run=run_with_only_job_param, config=test_track_config)
        job.start()
        job.print()
        basic_check_track_result(job)
        clear_statements_queue()

        job = gg.Job(prework=prework, run=run_with_job_and_case_params, config=test_track_config)
        job.start()
        job.print()
        basic_check_track_result(job)

    def test_run_in_multi_busy_thread(self):
        job = gg.Job(prework=prework, run=run_with_only_case_param, config=test_track_config)
        job.start(2)
        job.print()
        basic_check_track_result(job)

    def test_run_in_multi_idle_thread(self):
        job = gg.Job(prework=prework, run=run_with_only_case_param, config=test_track_config)
        job.start(10)
        job.print()
        basic_check_track_result(job)

    def test_with_custom_statistics(self):
        def prework_with_custom_statistics(job: Job):
            prework(job)
            # collect ip of Raspberry Pi
            statement = get_current_statement()
            statement.add_context_extensions("RPI_ip", "192.168.123.123")

        def run_with_custom_statistics(case: TestCases.SingleTestCase):
            statement = get_current_statement()
            result = {"score": run_with_only_case_param(case)}
            if case.name == "TestCase4":
                # mark TestCase4 as performance test
                statement.add_context_extensions("case_type", "performance")
                # collect elapsed time in performance test
                result["time"] = 10.23
            return result
        job = gg.Job(prework=prework_with_custom_statistics, run=run_with_custom_statistics, config=test_track_config)
        job.start()
        basic_check_track_result(job)

    def test_with_custom_event(self):

        def run_with_custom_event(case: TestCases.SingleTestCase):
            current_statement = get_current_statement()
            command = "sleep 2"
            result = gg.exec(command)
            # create new statement
            new_statement = new_statement_instance()
            # set the context
            new_statement.add_context_activity(
                Statement.ContextActivityType.Parent, current_statement.object_activity.activity_id)
            new_statement.context_statement_id = current_statement.statement_id
            # set the verb
            new_statement.verb = build_the_verb("执行")
            # set the activity
            from urllib.parse import quote
            new_statement.object_activity = Activity(quote(f'{default_concept_domain}/activity#{command}'),
                                                     activity_type=f'{default_concept_domain}/activity/type#command',
                                                     description={
                                                         'en': 'execute this command to sleep two seconds',
                                                         'zh': '执行该命令使得当前线程睡眠2秒'}
                                                     )
            new_statement.add_result_extension('cmd', command)
            new_statement.add_result_extension('stdout', result.stdout)
            new_statement.add_result_extension('stderr', result.stderr)
            new_statement.add_result_extension('exec_time', result.exec_time)
            new_statement.add_result_extension('returncode', result.returncode)
            return {"score": run_with_only_case_param(case)}
        job = gg.Job(prework=prework, run=run_with_custom_event, config=test_track_config)
        job.start()
        testcases = job.get_testcases()
        statements = get_statements_queue()
        statements_len = len(list(statements))
        # all statement id should be unique
        assert len(set(statement.statement_id for statement in statements)) == statements_len
        # a root statement and all case statement
        assert statements_len == len(testcases) * 2 + 1

    def test_exception_outside_case(self):
        info = "Grading Exception!!!!"

        def prework_exception(job: Job):
            prework(job)
            raise Exception(info)
        # test_track_config[track_grading_enable_config_key] = False
        job = gg.Job(prework=prework_exception, run=run_with_no_params, config=test_track_config)
        try:
            job.start()
        except Exception as ex:
            assert str(ex) == info
        statements = get_statements_queue()
        statements_len = len(list(statements))
        # since an exception was raise in pre_work , only one statement was generated
        assert statements_len == 1
        for statement in statements:
            assert statement.result_extensions["exception"] == info
        clear_statements_queue()

    def test_exception_inside_case(self):
        info = "Case Exception!!!!"

        def run_exception(case: TestCases.SingleTestCase):
            if case.name == "TestCase3":
                raise Exception(info)
            return run_with_only_case_param(case)

        # test_track_config[track_grading_enable_config_key] = False
        job = gg.Job(prework= prework, run=run_exception, config=test_track_config)
        try:
            job.start()
        except Exception as ex:
            assert str(ex) == info
        statements = get_statements_queue()
        for statement in statements:
            if statement.object_activity.activity_id == f"{default_concept_domain}/testcase/TestCase3":
                assert statement.result_extensions["exception"] == info
        basic_check_track_result(job)

    def test_models(self):
        verb = Verb("http://verb.educg.net//测试")
        assert str(verb) == '{"id": "http://verb.educg.net//测试"}'

    def test_new_instance(self):
        statements = []
        nums = 10000
        for i in range(nums):
            statements.append(new_statement_instance())
        ans = set(statement.statement_id for statement in statements)
        # all statement id should be unique
        assert len(ans) == nums
        clear_statements_queue()
