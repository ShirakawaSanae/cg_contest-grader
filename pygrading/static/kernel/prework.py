import pygrading as gg
from pygrading import Job
from pygrading.verdict import Verdict
from pygrading.html import str2html
import re
import os
import sys


def prework(job: Job):
    """任务预处理函数

    通常用于创建测试用例和创建配置信息

    参数:
        job: 传入的当前任务对象

    返回值:
        返回值为空，预处理内容需要更新到job对象中
    """

    # 检查测试样例
    testcase_dir = job.get_config().testcase_dir
    input_pattern = re.compile(r"input(\d+)\.txt")
    inputs_num = [input_pattern.findall(x) for x in os.listdir(testcase_dir)]
    inputs_num = [x[0] for x in inputs_num if len(x) > 0]
    inputs_src = [os.path.join(testcase_dir, f"input{x}.txt") for x in inputs_num]
    outputs_src = [os.path.join(testcase_dir, f"output{x}.txt") for x in inputs_num]
    check_outputs = [x for x in outputs_src if not os.path.exists(x)]
    if check_outputs:
        job.verdict(Verdict.UnknownError)
        job.comment(f"测试样例<br/>{'<br/>'.join(check_outputs)}<br/>不存在，请联系管理员。")
        job.is_terminate = True
        return


    # 创建测试用例和配置信息
    testcases = gg.create_testcase(100)
    for i, v in enumerate(zip(inputs_src, outputs_src)):
        input_src, output_src = v
        testcases.append(name=f"TestCase{i + 1}", score=100 / len(inputs_src), input_src=input_src, output_src=output_src)

    # 更新测试用例和配置信息到任务
    job.set_testcases(testcases)

    
    # 编译提交程序
    submit_dir = job.get_config().submit_dir
    sources = [os.path.join(submit_dir, x) for x in os.listdir(submit_dir) if x[-2:] == '.c']
    if not sources:
        job.verdict(Verdict.CompileError)
        job.comment("未找到有效的提交文件")
        job.is_terminate = True
        return

    run_file = os.path.join(submit_dir, "run")
    compile_result = gg.exec(f"gcc {' '.join(sources)} -o {run_file}")
    if compile_result.returncode != 0 or not os.path.exists(run_file):
        job.verdict(Verdict.CompileError)
        job.comment(str2html(compile_result.stderr))
        job.is_terminate = True
        return
    job.get_config()["run_file"] = run_file
