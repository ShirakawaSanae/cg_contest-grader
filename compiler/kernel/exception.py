from pygrading import Job

"""
相比 xiji-pygrading 提供更丰富的报错信息/功能
"""

class Verdict:
    AC = "Accept"
    WA = "Wrong Answer"
    CE = "Compile Error"
    RE = "Runtime Error"
    TLE = "Time Limit Exceeded"
    UE = "Unknown Error"

    Accept = AC
    WrongAnswer = WA
    CompileError = CE
    RuntimeError = RE
    TimeLimitError = TLE
    UnknownError = UE

class CG:
    class Exception(Exception):
        def __init__(self, verdict: str, comment: str):
            self.verdict = verdict
            self.comment = comment

    class RuntimeError(Exception):
        def __init__(self, comment: str):
            CG.Exception.__init__(self, Verdict.RE, comment)

    class CompileError(Exception):
        def __init__(self, comment: str):
            CG.Exception.__init__(self, Verdict.CE, comment)

    class WrongAnswer(Exception):
        def __init__(self, comment: str):
            CG.Exception.__init__(self, Verdict.WA, comment)

    class UnknownError(Exception):
        def __init__(self, comment: str):
            CG.Exception.__init__(self, Verdict.UE, comment)

    @staticmethod
    def catch(fun):
        def wrapper(job: Job, *args, **kwargs):
            try:
                return fun(job, *args, **kwargs)
            except CG.Exception as e:
                job.verdict(e.verdict)
                job.comment(html.str2html(e.comment))
                job.score(0)
                job.is_terminate = True
                # job.terminate()
        return wrapper
