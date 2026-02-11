import os
import subprocess
import time
import timeit
import traceback
import re
import json5
from os.path import basename, splitext

from exception import Verdict

import pygrading as gg
from pygrading import Job, TestCases, loge
from pygrading.utils import compare_list, get_result_lines, str2list

from prework import Lab4Data


def run(job: Job, case: TestCases.SingleTestCase) -> dict:
    """任务执行函数

    用于执行测试用例

    参数：
        job: 传入的当前任务对象
        case: 单独的测试用例对象

    返回值：
        result: 测试用例执行结果字典，该结果会被汇总到 job 对象的 summary 对象中
    """
    phase = job.get_config()["phase"]
    loge("run...")
    result = eval("run_" + phase + "(job, case)")
    loge("run...done")
    return result

def run_softmax(job: Job, case: TestCases.SingleTestCase) -> dict:
    # 创建一个结果对象
    result = {
        "name": case.name,
        "score": 0,
        "verdict": Verdict.WrongAnswer,
        "detail": case.extension["detail"],
        "exe_result": []
    }
    # 加载测试输入，若没有测试数据可以直接运行
    # 加载测试输出
    loge(f"-> case.output_src: {case.output_src}")
    expected_output = None
    if case.output_src:
        with open(case.output_src) as f:
            expected_output = f.read().strip()
    loge(f"-> set up env and execute python ")
    # 运行提交的程序
    submit_dir = case.extension["submit_dir"]
    try:  
        # run_operation = f"cd {case.extension["submit_dir"]} && rm -rf kernel_meta && python softmax.py"
        # exec_result = gg.exec(run_operation, time_out=None)
        run_operation = (
            f"cd {submit_dir} && "
            f"source ./setup_env.sh && "
            f"rm -rf kernel_meta && "
            f"python softmax.py"
        )
        exec_result = gg.exec(run_operation)
        #gg.exec("sleep 5s")
        loge(f"-> executed python and get result {exec_result}")
        # 加载学生的输出
        actual_path = os.path.join(submit_dir, "softmax.out")
        loge(f"-> actual_result_path: {actual_path}")
        with open(actual_path) as f:
            actual_output = f.read().strip()
        # actual_output.append(str(exec_result.returncode))
        # expected_output = str2list(expected_output)
        loge(f"-> expected output: {expected_output}")
        loge(f"-> actual output: {actual_output}")
        if expected_output is not None: 
            try:
                exp = float(expected_output)
                act = float(actual_output)
                ok = (abs(exp - act) <= 1e-8)
            except ValueError:
                ok = (expected_output == actual_output)
        else:
            ok = False
        if ok:
            result["verdict"] = Verdict.Accept
            result["score"] = case.score
            result["exe_result"] =  actual_output
            loge("--- Accept! ---")
        else:
            result["verdict"] = Verdict.WrongAnswer
            loge("--- Wrong Answer! ---")
            return result
    except subprocess.TimeoutExpired:
        loge("TimeoutExpired!")
        result["verdict"] = Verdict.TimeLimitError
        result["detail"] = "The executable file has been running for too long"
        return result
    except Exception as e:
        loge("Exception " + str(e))
        result["verdict"] = Verdict.RuntimeError
        result["detail"] = {"exception": e, "detail": traceback.format_exc()}
        return result
    return result


def run_lab2_warmup(job: Job, case: TestCases.SingleTestCase) -> dict:
    # 创建一个结果对象
    result = {
        "name": case.name,
        "score": 0,
        "verdict": Verdict.WrongAnswer,
        "detail": case.extension["detail"],
        "exe_result": 0,
        "expected_result": case.extension["answer"],
    }
    # lab2 测试数据加载
    run_file = job.get_config()["run_file"]
    input_src = case.input_src
    answer = result["expected_result"]
    # try:
    #     with open(input_src) as f:
    #         print(f.read())
    # except Exception as e:
    #     print(e)
    #     print(input_src)
    # print(answer)
    # exec_result = gg.exec("mkdir /root/submit_answer")
    # print(gg.exec("ls /root/build/ -al").stdout)
    # exec_result=gg.exec("lli /root/build/"+name+"_ll")
    try:
        gg.exec("clang --version")
        exec_result = gg.exec(run_file + input_src)
    except OSError:
        job.verdict(Verdict.RuntimeError)
        job.comment("Error: Cannot find lli")
        job.is_terminate = True
        return

    print(exec_result.stderr)
    result["exe_result"] = exec_result.returncode
    # 结果符合预期且执行时无错误，文件路径存在且编译无错误
    if (
        exec_result.returncode == answer
        and len(exec_result.stderr) == 0
        and len(result["detail"]) == 0
    ):
        result["verdict"] = Verdict.Accept
        result["score"] = case.score
    # 文件路径不存在或编译错误
    elif len(result["detail"]) != 0:
        result["verdict"] = Verdict.RuntimeError
        result["score"] = 0
    # 执行出错返回 RuntimeError
    elif len(exec_result.stderr) != 0:
        result["verdict"] = Verdict.RuntimeError
        result["detail"] = exec_result.stderr
        result["score"] = 0
    # wrong answer
    else:
        result["verdict"] = Verdict.WrongAnswer
        result["detail"] = exec_result.returncode
        result["score"] = 0
        result["expected"] = answer
    return result


# 实验四：4-ir-opt
def run_lab4_mem2reg(job: Job, case: TestCases.SingleTestCase) -> dict:
    l4d: Lab4Data = case.extension
    # 创建一个结果对象
    result = {
        "name": basename(case.name),
        "score": 0,
        "scmax": case.score,
        "verdict": Verdict.CompileError,
        "detail": "",
    }
    loge("Running " + result["name"])
    os.chdir("/root/build")
    case_base_name = splitext(basename(case.name))[0]
    asm_file = f"{case_base_name}.s"
    exec_binary = f"./{case_base_name}"
    ir_file = f"{case_base_name}.ll"
    loge(f"-> cminusfc -mem2reg -S {case.name} -o {asm_file}")
    try:
        compile_result = gg.exec(
            cmd=f"cminusfc -mem2reg -S {case.name} -o {asm_file}",
            time_out=None,
            queit=False,
        )
    except subprocess.TimeoutExpired:
        loge("TimeoutExpired!")
        result["verdict"] = Verdict.TimeLimitError
        result["detail"] = "cminusfc generate ir for too long"
        return result
    except Exception as e:
        loge("Exception " + str(e))
        err_info = {"exception": str(e)}
        result["detail"] = err_info
        return result
    
    loge(f"-> gcc {asm_file} -L . -lcminus_io -o {exec_binary}")
    try:
        # cminusfc编译
        # 在本地x86机器可以选择gcc生成汇编，测试测评的其他部分：
        # compile_result = gg.exec(cmd=f"gcc -include /coursegrader/submit/src/io/io.h -x c -S {case.name} -o {asm_file}", time_out=5, queit=False,)
        # gcc编译
        compile_result = gg.exec(
            cmd=f"gcc {asm_file} -L . -lcminus_io -o {exec_binary}",
            time_out=None,
            queit=False,
        )
    except subprocess.TimeoutExpired:
        loge("TimeoutExpired!")
        result["verdict"] = Verdict.TimeLimitError
        result["detail"] = "cminusfc has been running for too long"
        return result
    except Exception as e:
        loge("Exception " + str(e))
        err_info = {"exception": str(e)}
        result["detail"] = err_info
        return result

    # 输入输出
    input_content = expected_output = ""
    if case.input_src:
        with open(case.input_src) as f:
            input_content = f.read()
    if case.output_src:
        with open(case.output_src) as f:
            expected_output = f.read()

    loge(f"-> {exec_binary}")
    try:  # 运行生成的程序
        exec_result = gg.exec(cmd=f"{exec_binary}", input_str=input_content, time_out=None)
        actual_output = str2list(exec_result.stdout) if exec_result.stdout else []
        actual_output.append(str(exec_result.returncode))
        expected_output = str2list(expected_output)
        if compare_list(actual_output, expected_output):
            if l4d.base_val == l4d.max_val or l4d.base_score >= case.score * 100: 
                result["verdict"] = Verdict.Accept
                result["score"] = case.score * 100
            else:
                idx = l4d.idx
                base = l4d.base_score
                errs = str2list(exec_result.stderr)
                if len(errs) <= idx:
                    result["verdict"] = Verdict.Accept
                    result["score"] = base
                    result["detail"] = "Invalid stderr Output"
                else:
                    val = int(errs[-(1 + idx)])
                    k = case.score * 100 - l4d.base_score
                    t = l4d.max_val - l4d.base_val
                    u = k * (val - l4d.base_val)
                    if(t < 0):
                        t = -t
                        u = -u
                    sc = ((u + t - 1) // t) + l4d.base_score
                    if sc < l4d.base_score:
                        sc = l4d.base_score
                    elif sc > case.score * 100:
                        sc = case.score * 100
                    result["verdict"] = Verdict.Accept
                    result["score"] = sc
        else:
            result["verdict"] = Verdict.WrongAnswer
            result["actual"] = actual_output
            result["expected"] = expected_output
            return result
    except subprocess.TimeoutExpired:
        loge("TimeoutExpired!")
        result["verdict"] = Verdict.TimeLimitError
        result["detail"] = "The executable file has been running for too long"
        return result
    except Exception as e:
        loge("Exception " + str(e))
        result["verdict"] = Verdict.RuntimeError
        result["detail"] = {"exception": e, "detail": traceback.format_exc()}
        return result
    return result

def run_lab4_licm(job: Job, case: TestCases.SingleTestCase) -> dict:
    l4d: Lab4Data = case.extension
    # 创建一个结果对象
    result = {
        "name": basename(case.name),
        "score": 0,
        "scmax": case.score,
        "verdict": Verdict.CompileError,
        "detail": "",
    }
    loge("Running " + result["name"])
    os.chdir("/root/build")
    case_base_name = splitext(basename(case.name))[0]
    asm_file = f"{case_base_name}.s"
    exec_binary = f"./{case_base_name}"
    ir_file = f"{case_base_name}.ll"
    loge(f"-> cminusfc -mem2reg -licm -S {case.name} -o {asm_file}")
    try:
        compile_result = gg.exec(
            cmd=f"cminusfc -mem2reg -licm -S {case.name} -o {asm_file}",
            time_out=None,
            queit=False,
        )
    except subprocess.TimeoutExpired:
        loge("TimeoutExpired!")
        result["verdict"] = Verdict.TimeLimitError
        result["detail"] = "cminusfc generate ir for too long"
        return result
    except Exception as e:
        loge("Exception " + str(e))
        err_info = {"exception": str(e)}
        result["detail"] = err_info
        return result
    
    loge(f"-> gcc {asm_file} -L . -lcminus_io -o {exec_binary}")
    try:
        # cminusfc编译
        # 在本地x86机器可以选择gcc生成汇编，测试测评的其他部分：
        # compile_result = gg.exec(cmd=f"gcc -include /coursegrader/submit/src/io/io.h -x c -S {case.name} -o {asm_file}", time_out=5, queit=False,)
        # gcc编译
        compile_result = gg.exec(
            cmd=f"gcc {asm_file} -L . -lcminus_io -o {exec_binary}",
            time_out=None,
            queit=False,
        )
    except subprocess.TimeoutExpired:
        loge("TimeoutExpired!")
        result["verdict"] = Verdict.TimeLimitError
        result["detail"] = "cminusfc has been running for too long"
        return result
    except Exception as e:
        loge("Exception " + str(e))
        err_info = {"exception": str(e)}
        result["detail"] = err_info
        return result

    # 输入输出
    input_content = expected_output = ""
    if case.input_src:
        with open(case.input_src) as f:
            input_content = f.read()
    if case.output_src:
        with open(case.output_src) as f:
            expected_output = f.read()

    loge(f"-> {exec_binary}")
    try:  # 运行生成的程序
        exec_result = gg.exec(cmd=f"{exec_binary}", input_str=input_content, time_out=None)
        actual_output = str2list(exec_result.stdout) if exec_result.stdout else []
        actual_output.append(str(exec_result.returncode))
        expected_output = str2list(expected_output)
        if compare_list(actual_output, expected_output):
            if l4d.base_val == l4d.max_val or l4d.base_score >= case.score * 100: 
                result["verdict"] = Verdict.Accept
                result["score"] = case.score * 100
            else:
                idx = l4d.idx
                base = l4d.base_score
                errs = str2list(exec_result.stderr)
                if len(errs) <= idx:
                    result["verdict"] = Verdict.Accept
                    result["score"] = base
                    result["detail"] = "Invalid stderr Output"
                else:
                    val = int(errs[-(1 + idx)])
                    k = case.score * 100 - l4d.base_score
                    t = l4d.max_val - l4d.base_val
                    u = k * (val - l4d.base_val)
                    if(t < 0):
                        t = -t
                        u = -u
                    sc = ((u + t - 1) // t) + l4d.base_score
                    if sc < l4d.base_score:
                        sc = l4d.base_score
                    elif sc > case.score * 100:
                        sc = case.score * 100
                    result["verdict"] = Verdict.Accept
                    result["score"] = sc
        else:
            result["verdict"] = Verdict.WrongAnswer
            result["actual"] = actual_output
            result["expected"] = expected_output
            return result
    except subprocess.TimeoutExpired:
        loge("TimeoutExpired!")
        result["verdict"] = Verdict.TimeLimitError
        result["detail"] = "The executable file has been running for too long"
        return result
    except Exception as e:
        loge("Exception " + str(e))
        result["verdict"] = Verdict.RuntimeError
        result["detail"] = {"exception": e, "detail": traceback.format_exc()}
        return result
    return result


def run_lab5_const_prop(job: Job, case: TestCases.SingleTestCase) -> dict:
    result = {
        "name": case.name,
        "score": 0,
        "verdict": Verdict.WrongAnswer,
        "extension": case.extension,
    }
    run_file = job.get_config()["run_file"]
    input_src = case.input_src
    output = case.output_src
    input = case.extension["input"]
    extension = result["extension"]

    # print("===============  run_lab2 is executed, %s  ===============" % (input_src))

    # testcase_dir = job.get_config().testcase_dir
    # # 拼接获取 tescase_input 文件夹路径
    # testcase_input_dir = os.path.join(testcase_dir, f"testcase_input")

    compile_result = gg.exec(
        f"cd /root/build && ./cminusfc -emit-llvm -mem2reg -const-prop {input_src} -o ./{case.name}.ll && clang -O0 -w -no-pie ./{case.name}.ll -o ./{case.name} -L . -lcminus_io"
    )
    if compile_result.returncode != 0:
        # print("run 52 RuntimeError111")
        result["verdict"] = Verdict.CompileError
        result["score"] = 0
        extension["detail"] = compile_result.stderr
        result["extension"] = extension
        job.verdict(Verdict.CompileError)
        job.comment("Error: Cannot compile %s" % (input_src.split("/")[-1]))
        job.is_terminate = True
        return result

    # 获得生成的可执行二进制文件路径
    exec_binary = "/root/build/" + case.name
    screen_input = None
    if input:
        with open(input, "rb") as fin:
            screen_input = fin.read()

    try:
        t1 = time.time()
        exec_result = subprocess.run(
            exec_binary,
            input=screen_input,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=1,
        )
        t2 = time.time()
        # print(exec_result.returncode, exec_result.stdout, exec_result.stderr)
        with open(output, "rb") as output_str:
            # 再为将文件关闭之前，此处不能多次调用 output_str.read()
            actual_output = exec_result.stdout
            expected_output = output_str.read()
            if gg.utils.compare_str(actual_output, expected_output):
                result["verdict"] = Verdict.Accept
                result["score"] = case.extension["score"]
                ratio = extension["time"] * 1.3 / (t2 - t1)
                ratio = min(ratio, 1)
                result["score"] = result["score"] * ratio
                # print(result["score"], result["verdict"], " >>>>>>结果执行正确!!!!!!!!!!!!!!!!!!!!!\n")
            else:
                result["verdict"] = Verdict.WrongAnswer
                result["score"] = 0
                extension["detail"] = actual_output
                extension["expected"] = expected_output

    except OSError:
        # print("run 81 RuntimeError222")
        # if len(exec_result.stderr) != 0:
        result["verdict"] = Verdict.RuntimeError
        result["score"] = 0
        extension["detail"] = "OSError"
        result["extension"] = extension
        job.verdict(Verdict.RuntimeError)
        job.comment("Error: Cannot find %s" % (exec_binary))
        job.is_terminate = True
        return result

    except subprocess.TimeoutExpired:
        result["verdict"] = Verdict.RuntimeError
        result["score"] = 0
        extension["detail"] = "TimeoutExpired"
        result["extension"] = extension
        job.verdict(Verdict.RuntimeError)
        job.comment("Timeout while running testcases")
        job.is_terminate = True
        return result
    # print("run is over----------------------------------------------------------\n")
    return result


def run_lab5_loop_inv(job: Job, case: TestCases.SingleTestCase) -> dict:
    result = {
        "name": case.name,
        "score": 0,
        "verdict": Verdict.WrongAnswer,
        "extension": case.extension,
    }
    run_file = job.get_config()["run_file"]
    input_src = case.input_src
    output = case.output_src
    input = case.extension["input"]
    extension = result["extension"]

    # print("===============  run_lab2 is executed, %s  ===============" % (input_src))

    # testcase_dir = job.get_config().testcase_dir
    # # 拼接获取 tescase_input 文件夹路径
    # testcase_input_dir = os.path.join(testcase_dir, f"testcase_input")

    compile_result = gg.exec(
        f"cd /root/build && ./cminusfc -emit-llvm -mem2reg -loop-inv-hoist {input_src} -o ./{case.name}.ll && clang -O0 -w -no-pie ./{case.name}.ll -o ./{case.name} -L . -lcminus_io"
    )
    if compile_result.returncode != 0:
        # print("run 52 RuntimeError111")
        result["verdict"] = Verdict.CompileError
        result["score"] = 0
        extension["detail"] = compile_result.stderr
        result["extension"] = extension
        job.verdict(Verdict.CompileError)
        job.comment("Error: Cannot compile %s" % (input_src.split("/")[-1]))
        job.is_terminate = True
        return result

    # 获得生成的可执行二进制文件路径
    exec_binary = "/root/build/" + case.name
    screen_input = None
    if input:
        with open(input, "rb") as fin:
            screen_input = fin.read()

    try:
        t1 = time.time()
        exec_result = subprocess.run(
            exec_binary,
            input=screen_input,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=1,
        )
        t2 = time.time()
        # print(exec_result.returncode, exec_result.stdout, exec_result.stderr)
        with open(output, "rb") as output_str:
            # 再为将文件关闭之前，此处不能多次调用 output_str.read()
            actual_output = exec_result.stdout
            expected_output = output_str.read()
            if gg.utils.compare_str(actual_output, expected_output):
                result["verdict"] = Verdict.Accept
                result["score"] = case.extension["score"]
                ratio = extension["time"] * 1.3 / (t2 - t1)
                ratio = min(ratio, 1)
                result["score"] = result["score"] * ratio
                # print(result["score"], result["verdict"], " >>>>>>结果执行正确!!!!!!!!!!!!!!!!!!!!!\n")
            else:
                result["verdict"] = Verdict.WrongAnswer
                result["score"] = 0
                extension["detail"] = actual_output
                extension["expected"] = expected_output

    except OSError:
        # print("run 81 RuntimeError222")
        # if len(exec_result.stderr) != 0:
        result["verdict"] = Verdict.RuntimeError
        result["score"] = 0
        extension["detail"] = "OSError"
        result["extension"] = extension
        job.verdict(Verdict.RuntimeError)
        job.comment("Error: Cannot find %s" % (exec_binary))
        job.is_terminate = True
        return result

    except subprocess.TimeoutExpired:
        result["verdict"] = Verdict.RuntimeError
        result["score"] = 0
        extension["detail"] = "TimeoutExpired"
        result["extension"] = extension
        job.verdict(Verdict.RuntimeError)
        job.comment("Timeout while running testcases")
        job.is_terminate = True
        return result
    # print("run is over----------------------------------------------------------\n")
    return result

def calculate_gvn_bb_score(input_partition, answer_partition):
    # score of every bb is either 0 or 1
    if len(input_partition) != len(answer_partition):
        return 0
    score_cnt = 0
    for in_cc in input_partition:
        for ans_cc in answer_partition:
            if set(in_cc) == set(ans_cc):
                score_cnt += 1
                break
    if score_cnt == len(answer_partition):
        return 1
    return 0

def calculate_gvn_score(input_functions, answer_functions):
    # input & answer is dict from json
    # calculate score use sum(score of every bb)/total_bb
    # score of every bb is either 1 or 0
    # total_bb is count of pout

    total_bb = 0
    for ans_func in answer_functions:
        total_bb += len(ans_func["pout"])
    cal_score = 0
    for ans_func in answer_functions:
        for in_func in input_functions:
            if ans_func["function"] == in_func["function"]:
                for ans_bb, ans_partition in ans_func["pout"].items():
                    for in_bb, in_partition in in_func["pout"].items():
                        if ans_bb == in_bb:
                            cal_score += calculate_gvn_bb_score(
                                in_partition, ans_partition
                            )
                        else:
                            continue
            else:
                continue
    return cal_score / total_bb

def run_lab5_gvn(job: Job, case: TestCases.SingleTestCase) -> dict:
    result = {
        "name": case.name,
        "score": 0,
        "verdict": Verdict.WrongAnswer,
        "extension": case.extension,
    }
    input_src = case.input_src
    output = case.output_src
    extension = result["extension"]
    compile_result = gg.exec(
        f"cd /root/build && ./cminusfc -emit-llvm -mem2reg -gvn -dump-json {input_src} -o ./{case.name}.ll"
    )
    if compile_result.returncode != 0:
        # print("run 52 RuntimeError111")
        result["verdict"] = Verdict.CompileError
        result["score"] = 0
        extension["detail"] = compile_result.stderr
        result["extension"] = extension
        job.verdict(Verdict.CompileError)
        job.comment("Error: Cannot compile %s" % (input_src.split("/")[-1]))
        job.is_terminate = True
        return result

    try:
        extension["detail"] = "create gvn json Error "
        with open("/root/build/gvn.json", "r") as load_input:
            extension["detail"] = "create testcase json Error "
            with open(output, "r") as load_answer:
                extension["detail"] = "json load Error"
                input_functions = json5.load(load_input)
                answer_functions = json5.load(load_answer)
                extension["detail"] = "calculate_gvn_score Error"
                rate = calculate_gvn_score(input_functions, answer_functions)
                if rate == 1:
                    result["verdict"] = Verdict.Accept
                    result["score"] = case.score
                    # print(result["score"], result["verdict"], " >>>>>>结果执行正确!!!!!!!!!!!!!!!!!!!!!\n")
                else:
                    result["verdict"] = Verdict.WrongAnswer
                    result["score"] = rate*case.score

    except OSError:
        # print("run 81 RuntimeError222")
        # if len(exec_result.stderr) != 0:
        result["verdict"] = Verdict.RuntimeError
        result["score"] = 0
        extension["detail"] += "OSError"
        result["extension"] = extension
        job.verdict(Verdict.RuntimeError)
        job.comment("Error: Cannot find ")
        job.is_terminate = True
        return result

    except subprocess.TimeoutExpired:
        result["verdict"] = Verdict.RuntimeError
        result["score"] = 0
        extension["detail"] = "TimeoutExpired"
        result["extension"] = extension
        job.verdict(Verdict.RuntimeError)
        job.comment("Timeout while running testcases")
        job.is_terminate = True
        return result
    # print("run is over----------------------------------------------------------\n")
    return result

#lab6 
def run_lab6(job: Job, case: TestCases.SingleTestCase) -> dict:
    # 创建一个结果对象
    result = {
        "name": basename(case.name),
        "score": 0,
        "verdict": Verdict.CompileError,
        "detail": "",
    }
    os.chdir("/root/build")
    case_base_name = splitext(basename(case.name))[0]
    asm_file = f"{case_base_name}.s"
    exec_binary = f"./{case_base_name}"
    # testdata_dir = job.get_config().testcase_dir
    # testcase_dir = os.path.join(testdata_dir, f"testcase")
    # io_dir = os.path.join(testcase_dir,"io.c")
    try:
        # cminusfc编译
        # 在本地x86机器可以选择gcc生成汇编，测试测评的其他部分：
        # compile_result = gg.exec(cmd=f"gcc -include /coursegrader/submit/src/io/io.h -x c -S {case.name} -o {asm_file}", time_out=5, queit=False,)
        compile_result = gg.exec(
            cmd=f"cminusfc -S -mem2reg -register-allocate {case.name} -o {asm_file}",
            time_out=5,
            queit=False,
        )
        # gcc编译
        compile_result = gg.exec(
            cmd=f"gcc {asm_file} -L . -lcminus_io -o {exec_binary}",
            time_out=5,
            queit=False,
        )
    except subprocess.TimeoutExpired:
        result["verdict"] = Verdict.TimeLimitError
        result["detail"] = "cminusfc has been running for too long"
        return result
    except Exception as e:
        err_info = {"exception": str(e)}
        result["detail"] = err_info
        return result

    # 输入输出
    input_content = expected_output = ""
    if case.input_src:
        with open(case.input_src) as f:
            input_content = f.read()
    if case.output_src:
        with open(case.output_src) as f:
            expected_output = f.read()

    try:  # 运行生成的程序
        exec_result = gg.exec(cmd=f"{exec_binary}", input_str=input_content, time_out=5)
        actual_output = str2list(exec_result.stdout) if exec_result.stdout else []
        actual_output.append(str(exec_result.returncode))
        expected_output = str2list(expected_output)
        if compare_list(actual_output, expected_output):
            result["verdict"] = Verdict.Accept
            result["score"] = case.score
        else:
            result["verdict"] = Verdict.WrongAnswer
            result["actual"] = actual_output
            result["expected"] = expected_output
            return result
    except subprocess.TimeoutExpired:
        result["verdict"] = Verdict.TimeLimitError
        result["detail"] = "The executable file has been running for too long"
        return result
    except Exception as e:
        result["verdict"] = Verdict.RuntimeError
        result["detail"] = {"exception": e, "detail": traceback.format_exc()}
        return result

    return result
