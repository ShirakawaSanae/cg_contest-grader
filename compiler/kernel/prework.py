from logging import log
import math
import re
import os
import sys
import json

from operator import itemgetter
from exception import Verdict, CG

import pygrading as gg
from pygrading import Job, loge, exec
from pygrading.utils import makedirs
from pygrading.html import str2html
from pygrading.exception import ExecError


@CG.catch
def prework(job: Job):
    config_file = os.path.join(
        job.get_config().testcase_dir, "caseconfig.json" # 本地测试可以改成testcases/caseconfig.json
    )
    loge(job.get_config().testcase_dir)
    loge("prework config_file " + config_file)
    if not os.path.exists(config_file):
        loge("prework config_file not exist")
        testdata = job.get_config().testcase_dir
        testcases = os.path.join(testdata, "testcases")
        loge(testcases)
        detail = {
            "pwd": os.curdir,
            testdata: os.listdir(testdata),
            # testcases: os.listdir(testcases),

        }
        job.verdict(Verdict.UnknownError)
        job.detail(str(detail))
        job.is_terminate = True
        return

        # # loge(os.listdir(testdata))
        # loge(os.listdir(testcases))
        # info = {
        #     testdata: os.listdir(testdata),
        #     testcases: os.listdir(testcases)
        # }
        # raise FileNotFoundError(str(info))
    with open(config_file) as conf:
        raw_data = conf.read()
    files_config = json.loads(raw_data)
    phase = job.get_config()["phase"] = files_config["phase"]
    loge("prework...")
    eval("prework_" + phase + "(job)")
    loge("prework...done")

def prework_pagedattn(job: Job):
    # 获取测试点和配置信息
    testcase_dir = job.get_config().testcase_dir
    files_config = {}
    config_file = os.path.join(testcase_dir, "caseconfig.json")
    loge(f"--- config_file: {config_file}")
    with open(config_file) as conf:
        raw_data = conf.read()
        files_config = json.loads(raw_data)
    testcaseList = files_config.get("testcaseList")
    # 设置满分
    testcases = gg.create_testcase(100)
    submit_dir = job.get_config().submit_dir
    loge(f"--- submit_dir: {submit_dir}, {job.get_config()}")
    try:
        # 建立 Ascend 环境
        compile_result = gg.exec(f"bash -lc 'cd {submit_dir} && source setup_env.sh'")
        loge(f"-> executed setup_env.sh and get result {compile_result.returncode}")
        gg.exec("sleep 5s")
        if compile_result.returncode != 0:
            raise CG.CompileError(compile_result.stderr)
    # 异常编译错误
    except CG.CompileError as e:
        job.verdict(Verdict.CompileError)
        job.comment(str(e))
        job.is_terminate = True
        return
    # 异常系统错误
    except OSError as e:
        job.verdict(Verdict.CompileError)
        job.comment(f"OSError: {e}")
        job.is_terminate = True
        return
    for itemCase in sorted(testcaseList, key=itemgetter('name')):
        name = itemCase["name"]
        score : int = int(itemCase["score"])
        submit_path = itemCase["submit_path"]
        testcases.append(name = name, score = score, extension={"submit_path": submit_path})
    # 更新测试用例和配置信息到任务
    job.set_testcases(testcases)

def prework_softmax(job:Job):
    # 获取测试点和配置信息
    testcase_dir = os.path.join(job.get_config().testcase_dir, "testcases")
    files_config = {}
    config_file = os.path.join(testcase_dir, "caseconfig.json")
    with open(config_file) as conf:
        raw_data = conf.read()
        files_config = json.loads(raw_data)
    testcaseList = files_config.get("testcaseList")
    # 设置满分
    testcases = gg.create_testcase(100)
    # 更新测试点和配置信息到任务
    job.set_testcases(testcases)
    # 编译学生提交的程序
    submit_dir = job.get_config().submit_dir
    loge(f"--- submit_dir: {submit_dir}, {job.get_config()}")
    try:
        # 建立 Ascend 环境
        compile_result = gg.exec(f"bash -lc 'cd {submit_dir} && source setup_env.sh'")
        loge(f"-> executed setup_env.sh and get result {compile_result.returncode}")
        gg.exec("sleep 5s")
        if compile_result.returncode != 0:
            raise CG.CompileError(compile_result.stderr)
    # 异常编译错误
    except CG.CompileError as e:
        job.verdict(Verdict.CompileError)
        job.comment(str(e))
        job.is_terminate = True
        return
    # 异常系统错误
    except OSError as e:
        job.verdict(Verdict.CompileError)
        job.comment(f"OSError: {e}")
        job.is_terminate = True
        return
    # 加载测试点到希冀 testcases
    gg.exec("sleep 5s")
    for itemCase in testcaseList:
        name = itemCase["name"]
        score = itemCase["score"]
        itemCaseDir = itemCase["output"]
        loge(f"--- expected output file: {itemCaseDir}")
        if os.path.exists(itemCaseDir):
            testcases.append(name = name, output_src = itemCaseDir, score = score, extension = {"detail": "", "submit_dir": submit_dir})
        else:
            detail = "Error: Cannot find testcase "+ name
            testcases.append(name=name, output_src = itemCaseDir, score=score, extension = {"detail": detail})

    

def prework_lab2_warmup(job: Job):
    testcase_dir = os.path.join(job.get_config().testcase_dir, "testcases")
    files_config = {}
    config_file = os.path.join(testcase_dir, "caseconfig.json")
    with open(config_file) as conf:
        raw_data = conf.read()
        files_config = json.loads(raw_data)

    testcaseList = files_config.get("testcaseList")
    testcaseList_hand = files_config.get("testcaseList_hand")

    testcases = gg.create_testcase(100)
    # 更新测试用例和配置信息到任务
    job.set_testcases(testcases)

    # 编译提交程序
    submit_dir = job.get_config().submit_dir
    try:
        compile_result = gg.exec(
            f"mkdir -p /root/build && cd /root/build && cmake {submit_dir} && cd /root/build && make -j")

    except OSError:
        job.verdict(Verdict.CompileError)
        job.comment("Error: Cannot find cmake")
        job.is_terminate = True
        return

    compile_result = gg.exec("cd /root/build && make -j2")
    if compile_result.returncode != 0:
        raise CG.CompileError(compile_result.stderr)

    for itemCase in testcaseList:
        name = itemCase["name"]
        score = itemCase["score"]
        answer = itemCase["answer"]
        itemCaseDir = os.path.join("/root/build/", name)
        # print(itemCaseDir)
        if os.path.exists(itemCaseDir):
            re = gg.exec(itemCaseDir)
            input_str = re.stdout
            input_src = itemCaseDir+"_ll"
            fh = open(input_src, 'w')
            fh.write(input_str)
            fh.close()
            testcases.append(name=name, input_src=input_src, score=score, extension={
                             "answer": answer, "detail": ""})
        else:
            detail = "Error: Cannot find itemcase "+name
            testcases.append(name=name, input_src='', score=score, extension={
                             "answer": answer, "detail": detail})
    for itemCase_hand in testcaseList_hand:
        name = itemCase_hand["name"]
        score = itemCase_hand["score"]
        answer = itemCase_hand["answer"]
        itemCaseDir = os.path.join(
            submit_dir, itemCase_hand["submit_relative_path"])
        # loge(itemCaseDir)
        if os.path.exists(itemCaseDir):
            testcases.append(name=name, input_src=itemCaseDir, score=score, extension={
                             "answer": answer, "detail": ""})
        else:
            detail = "Error: Cannot find itemcase_hand "+name
            testcases.append(name=name, input_src=input_src, score=score, extension={
                             "answer": answer, "detail": detail})
    job.get_config()["run_file"] = "lli "


class Lab4Data:
    def __init__(self, base_val: int, max_val: int, idx: int, base_score: int):
        self.base_val = base_val
        self.max_val = max_val
        self.idx = idx
        self.base_score = base_score

    def get_base_val(self) -> int:
        return self.base_val

    def get_max_val(self) -> int:
        return self.max_val
    
    def get_idx(self) -> int:
        return self.idx

    def get_base_score(self) -> int:
        return self.base_score

    def __str__(self) -> str:
        return f"Lab4Data base_val {self.base_val}, max_val {self.max_val}, idx {self.idx}, base_score {self.base_score}"


def prework_lab4_mem2reg(job: Job):
    # 编译
    loge("compile cminusfc")
    compile_project(job)
    loge("compile cminusfc done")
    # 设置测试数据
    testcases = gg.create_testcase(total_score=76)  # 总分 70
    loge("prework_lab4 testcases created")
    testdata_dir = job.get_config().testcase_dir
    loge("prework_lab4 testdata_dir " + testdata_dir)
    with open(os.path.join(testdata_dir, "caseconfig.json")) as conf:
        files_config = json.loads(s=conf.read())
    testcaseList = files_config.get("testcaseList")
    idx = int(files_config["idx"])
    score_multiplier: int = int(files_config["base_fraction"])
    for itemCase in sorted(testcaseList, key=itemgetter('name')):
        name = itemCase["name"]
        score : int = int(itemCase["score"])
        input_src = itemCase["input"]
        output_src = itemCase["output"]
        l4d = Lab4Data(int(itemCase["min"]), int(itemCase["max"]), idx, score_multiplier * score)
        testcases.append(name, score, input_src, output_src,l4d)
    # 更新测试用例和配置信息到任务
    job.set_testcases(testcases)



def prework_lab4_licm(job: Job):
    # 编译
    loge("compile cminusfc")
    compile_project(job)
    loge("compile cminusfc done")
    # 设置测试数据
    testcases = gg.create_testcase(total_score=76)  # 总分 70
    loge("prework_lab4 testcases created")
    testdata_dir = job.get_config().testcase_dir
    loge("prework_lab4 testdata_dir " + testdata_dir)
    with open(os.path.join(testdata_dir, "caseconfig.json")) as conf:
        files_config = json.loads(s=conf.read())
    testcaseList = files_config.get("testcaseList")
    idx = int(files_config["idx"])
    score_multiplier: int = int(files_config["base_fraction"])
    for itemCase in sorted(testcaseList, key=itemgetter('name')):
        name = itemCase["name"]
        score : int = int(itemCase["score"])
        input_src = itemCase["input"]
        output_src = itemCase["output"]
        l4d = Lab4Data(int(itemCase["min"]), int(itemCase["max"]), idx, score_multiplier * score)
        testcases.append(name, score, input_src, output_src,l4d)
    # 更新测试用例和配置信息到任务
    job.set_testcases(testcases)

def get_testcase_list(job: Job):
    testcase_dir = os.path.join(job.get_config().testcase_dir, "testcases")
    files_config = {}
    config_file = os.path.join(job.get_config().testcase_dir, "caseconfig.json")
    with open(config_file) as conf:
        raw_data = conf.read()
        files_config = json.loads(raw_data)

    testcaseList, baselineList = files_config.get("testcaseList"), files_config.get("baselineList")
    return testcaseList, baselineList


def prework_lab5_const_prop(job: Job):
    testcaseList, baselineList = get_testcase_list(job)
    testcases = gg.create_testcase(100)
    # 更新测试用例和配置信息到任务
    job.set_testcases(testcases)

    # 编译提交程序
    submit_dir = job.get_config().submit_dir
    try:
        compile_result = gg.exec(
            f"mkdir -p /root/build && cd /root/build && cmake {submit_dir} && make -j"
        )

    except OSError:
        job.verdict(Verdict.CompileError)
        job.comment("Compile Jianmu project Error")
        job.is_terminate = True
        return

    run_file = "/root/build/cminusfc"
    if compile_result.returncode != 0 or not os.path.exists(run_file):
        raise CG.CompileError(compile_result.stderr)
    job.get_config()["run_file"] = run_file

    # 更新测试用例
    for itemCase, baseline in zip(testcaseList, baselineList):
        if not os.path.exists(baseline):
            job.comment("File not found")
            job.is_terminate = True
            return

        # 运行 baseline 并计算时间
        exec_file = os.path.splitext(os.path.basename(baseline))[0]
        compile_command = f"cd /root/build && clang -O0 -w -no-pie {baseline} -o ./{exec_file} -L . -lcminus_io"
        baseline_result = gg.exec(compile_command)
        if baseline_result.returncode != 0:
            job.comment("Compile Baseline Error\n" + baseline_result.stderr)
            job.is_terminate = True
            return

        try:
            result = gg.exec(f"cd /root/build && ./{exec_file}")
        except Exception as e:
            job.comment("Run Baseline Error\n" + str(e))
            job.is_terminate = True
            return
        name = itemCase["name"]
        output = itemCase["output"]
        if os.path.exists(name):
            testcases.append(
                name=os.path.splitext(os.path.basename(name))[0],
                input_src=name,
                output_src=output,
                score=0,
                extension={
                    "input": None,
                    "score": 25,
                    "hide": False,
                    "time": result.exec_time,
                    "detail": "",
                },
            )
        else:
            detail = "Error: Cannot find itemcase " + name
            testcases.append(
                name=os.path.splitext(os.path.basename(name))[0],
                input_src=name,
                output_src=output,
                score=0,
                extension={"input": None, "score": 0, "hide": False, "detail": detail},
            )


def prework_lab5_loop_inv(job: Job):
    return prework_lab5_const_prop(job)

def prework_lab5_gvn(job: Job):
    testcase_dir = os.path.join(job.get_config().testcase_dir, "testcases")
    files_config = {}
    config_file = os.path.join(job.get_config().testcase_dir, "caseconfig.json")
    with open(config_file) as conf:
        raw_data = conf.read()
        files_config = json.loads(raw_data)
    testcaseList = files_config.get("testcaseList")
    testcases = gg.create_testcase(100)
    # 更新测试用例和配置信息到任务
    job.set_testcases(testcases)

    # 编译提交程序
    submit_dir = job.get_config().submit_dir
    try:
        compile_result = gg.exec(
            f"mkdir -p /root/build && cd /root/build && cmake {submit_dir} && make -j"
        )

    except OSError:
        job.verdict(Verdict.CompileError)
        job.comment("Compile Jianmu project Error")
        job.is_terminate = True
        return

    run_file = "/root/build/cminusfc"
    if compile_result.returncode != 0 or not os.path.exists(run_file):
        raise CG.CompileError(compile_result.stderr)
    job.get_config()["run_file"] = run_file

    # 更新测试用例
    for itemCase in testcaseList:
        name = itemCase["name"]
        output = itemCase["output"]
        if os.path.exists(name):
            testcases.append(
                name=os.path.splitext(os.path.basename(name))[0],
                input_src=name,
                output_src=output,
                score=10, #itemCase["score"],
                extension={
                    "input": None,
                    "hide": False,
                    "detail": "",
                },
            )
        else:
            detail = "Error: Cannot find itemcase " + name
            testcases.append(
                name=os.path.splitext(os.path.basename(name))[0],
                input_src=name,
                output_src=output,
                score=10, #itemCase["score"],
                extension={"input": None, "hide": False, "detail": detail},
            )

def prework_lab6(job: Job):
    # 编译
    compile_project(job)
    loge("compile cminusfc done")
    # 设置测试数据
    testcases = gg.create_testcase(30)  # 总分 70
    testdata_dir = job.get_config().testcase_dir
    with open(os.path.join(testdata_dir, "caseconfig.json")) as conf:
        files_config = json.loads(conf.read())
    testcaseList = files_config.get("testcaseList")
    for itemCase in sorted(testcaseList, key=itemgetter('name')):
        name = itemCase["name"]
        score = itemCase["score"]
        input_src = itemCase["input"]
        output_src = itemCase["output"]
        testcases.append(name, score, input_src, output_src)
    # 更新测试用例和配置信息到任务
    job.set_testcases(testcases)
