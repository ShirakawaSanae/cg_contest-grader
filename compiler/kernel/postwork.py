import math
import os
import re

from exception import Verdict

import pygrading as gg
from pygrading import Job, loge


def postwork(job: Job) -> dict:
    phase = job.get_config()["phase"]
    loge("postwork...")
    eval("postwork_" + phase + "(job)")
    loge("postwork...done")

def postwork_softmax(job: Job) -> dict:
    # 创建一个总结对象
    summary = job.get_summary()
    # 设置需要显示的参数
    all_tests = 0
    passed_tests = 0
    score = 0
    show_summary = []
    err_type = Verdict.Accept
    # 遍历每个测试点
    for result in summary:
        show_item = {}
        show_item['name'] = os.path.basename(result['name'])
        show_item['verdict'] = result['verdict']
        show_item['score'] = result['score']
        print(result)
        if result['verdict'] == Verdict.Accept:
            passed_tests += 1
        else:
            show_item['detail'] = result['detail']
            err_type = result['verdict']
        show_summary.append(show_item)
        all_tests += 1
        score += result['score']
    # 每个测试点所要展示的结果对象
    info = {
        "all": all_tests,
        "passed": passed_tests,
        "score": score,
        "err_type": err_type
    }
    # 更新结果输出字段
    job.verdict("Accepted" if all_tests == passed_tests else "Wrong Answer")
    job.score(score)
    # 渲染 HTML 模板页面（可选）
    # 被渲染的页面应位于 kernel/templates/html 目录下
    # job.detail(gg.render_template("index.html", author="Charles Zhang", summary=summary))
    comment = gg.render_template(
        "index.html", author="", summary=show_summary, info=info)
    job.comment(comment)

def postwork_lab2_warmup(job: Job) -> dict:
    summary = job.get_summary()

    all_tests = 0
    passed_tests = 0
    score = 0
    show_summary = []
    err_type = Verdict.Accept

    for result in summary:
        show_item = {}
        show_item['name'] = os.path.basename(result['name'])
        show_item['verdict'] = result['verdict']
        show_item['score'] = result['score']
        # print(result)
        if result['verdict'] == Verdict.Accept:
            passed_tests += 1
        else:
            show_item['detail'] = result['detail']
            err_type = result['verdict']
        if result['verdict'] == Verdict.WrongAnswer:
            show_item['expected'] = result['expected']
        show_summary.append(show_item)
        all_tests += 1
        score += result['score']

    info = {
        "all": all_tests,
        "passed": passed_tests,
        "score": score,
        "err_type": err_type
    }

    # 更新结果输出字段
    job.verdict("Accepted" if all_tests == passed_tests else "Wrong Answer")
    job.score(score)
    # 渲染 HTML 模板页面（可选）
    # 被渲染的页面应位于 kernel/templates/html 目录下
    # job.detail(gg.render_template("index.html", author="Charles Zhang", summary=summary))
    comment = gg.render_template(
        "index.html", author="Charles Zhang", summary=show_summary, info=info)
    job.comment(comment)


def format_float_from_int(num_int: int) -> str:
    integer_part = num_int // 100
    decimal_part = num_int % 100
    if decimal_part != 0:
        return f"{integer_part}.{decimal_part:02d}".rstrip('0')
    return f"{integer_part}"

def postwork_lab4_mem2reg(job: Job) -> dict:
    total_score: int = 0
    max_score: int = 0
    count: int = 0
    for i in job.get_summary():
        if type(i) == dict and "score" in i:
            total_score += i["score"]
            i["scshow"] = format_float_from_int(i["score"]) + "/" + str(object=i["scmax"])
            max_score += i["scmax"]
            count += 1
    # 更新结果输出字段
    job_verdict = Verdict.Accept if sum(result['verdict'] == Verdict.Accept for result in job.get_summary()) == count else Verdict.WrongAnswer
    job.verdict(job_verdict)
    job.score((total_score + 99) // 100)

    # 渲染信息
    info = {
        "all": len(job.get_testcases()),
        "passed": sum(result['verdict'] == Verdict.Accept for result in job.get_summary()),
        "score": format_float_from_int(total_score),
        "scmax": max_score,
        "half_pass": (total_score != max_score * 100),
        "err_type": job_verdict
    }

    # 自定义排序
    def custom_sort_key(d: dict):
        s = d['name']
        match = re.search(r'(\d+)_.*\.cminus', s)
        if match:
            return 400 + int(match.group(1))
        return 0

    # 渲染 HTML 模板页面（可选）
    # 被渲染的页面应位于 kernel/templates/html 目录下
    job.comment(gg.render_template(
        "index.html", summary=sorted(job.get_summary(), key=custom_sort_key), info=info
    ))
    job.set_config({
        'PATH': os.environ["PATH"],
        'list /usr/local/bin': os.listdir("/usr/local/bin"),
        'list /coursegrader': os.listdir("//coursegrader"),
    })
    job.secret(job.get_config())

def postwork_lab4_licm(job: Job) -> dict:
    total_score: int = 0
    max_score: int = 0
    count: int = 0
    for i in job.get_summary():
        if type(i) == dict and "score" in i:
            total_score += i["score"]
            i["scshow"] = format_float_from_int(i["score"]) + "/" + str(object=i["scmax"])
            max_score += i["scmax"]
            count += 1
    # 更新结果输出字段
    job_verdict = Verdict.Accept if sum(result['verdict'] == Verdict.Accept for result in job.get_summary()) == count else Verdict.WrongAnswer
    job.verdict(job_verdict)
    job.score((total_score + 99) // 100)

    # 渲染信息
    info = {
        "all": len(job.get_testcases()),
        "passed": sum(result['verdict'] == Verdict.Accept for result in job.get_summary()),
        "score": format_float_from_int(total_score),
        "scmax": max_score,
        "half_pass": (total_score != max_score * 100),
        "err_type": job_verdict
    }

    # 自定义排序
    def custom_sort_key(d: dict):
        s = d['name']
        match = re.search(r'(\d+)_.*\.cminus', s)
        if match:
            return 400 + int(match.group(1))
        return 0

    # 渲染 HTML 模板页面（可选）
    # 被渲染的页面应位于 kernel/templates/html 目录下
    job.comment(gg.render_template(
        "index.html", summary=sorted(job.get_summary(), key=custom_sort_key), info=info
    ))
    job.set_config({
        'PATH': os.environ["PATH"],
        'list /usr/local/bin': os.listdir("/usr/local/bin"),
        'list /coursegrader': os.listdir("//coursegrader"),
    })
    job.secret(job.get_config())


def postwork_lab5(job: Job) -> dict:
    summary = job.get_summary()
    all_tests = 0
    passed_tests = 0
    score = 0
    show_summary = []
    err_type = Verdict.Accept

    for result in summary:
        show_item = {}
        # show_item['name'] = os.path.basename(result['name'])
        show_item["name"] = result["name"]
        show_item["verdict"] = result["verdict"]
        show_item["score"] = result["score"]
        # print(show_item['score'])
        extension = result["extension"]

        if result["verdict"] == Verdict.Accept:
            passed_tests += 1
        else:
            show_item["detail"] = extension["detail"]
            err_type = result["verdict"]
        if result["verdict"] == Verdict.WrongAnswer:
            show_item["expected"] = extension["expected"]

        # show_summary.append(show_item)
        if extension["hide"] == False:
            show_summary.append(show_item)
        all_tests += 1
        score += result["score"]

        # extension = result['extension']
        # if result['verdict'] == Verdict.Accept:
        #     passed_tests += 1
        # all_tests += 1
        # score += result['score']

    # for result in summary:
    #     extension = result['extension']
    #     # if (extension['hide'] == False):
    #     show_summary.append(result)

    info = {
        "all": all_tests,
        "passed": passed_tests,
        "score": score,
        "err_type": err_type,
    }

    # 更新结果输出字段
    job.verdict("Accepted" if all_tests == passed_tests else "Wrong Answer")
    job.score(int(score))
    # summary = job.get_summary()
    # 渲染 HTML 模板页面（可选）
    # 被渲染的页面应位于 kernel/templates/html 目录下
    # job.detail(gg.render_template("index.html", author="Charles Zhang", summary=summary))
    comment = gg.render_template(
        "index.html", author="Charles Zhang", summary=show_summary, info=info
    )
    job.comment(comment)


def postwork_lab5_const_prop(job: Job) -> dict:
    return postwork_lab5(job)


def postwork_lab5_loop_inv(job: Job) -> dict:
    return postwork_lab5(job)

def postwork_lab5_gvn(job: Job) -> dict:
    summary = job.get_summary()
    all_tests = 0
    passed_tests = 0
    score = 0
    show_summary = []
    err_type = Verdict.Accept

    for result in summary:
        show_item = {}
        # show_item['name'] = os.path.basename(result['name'])
        show_item["name"] = result["name"]
        show_item["verdict"] = result["verdict"]
        show_item["score"] = result["score"]
        # print(show_item['score'])
        extension = result["extension"]

        if result["verdict"] == Verdict.Accept:
            passed_tests += 1
        else:
            show_item["detail"] = extension["detail"]
            err_type = result["verdict"]
        # if result["verdict"] == Verdict.WrongAnswer:
        #     show_item["expected"] = extension["expected"]

        # show_summary.append(show_item)
        if extension["hide"] == False:
            show_summary.append(show_item)
        all_tests += 1
        score += result["score"]

        # extension = result['extension']
        # if result['verdict'] == Verdict.Accept:
        #     passed_tests += 1
        # all_tests += 1
        # score += result['score']

    # for result in summary:
    #     extension = result['extension']
    #     # if (extension['hide'] == False):
    #     show_summary.append(result)

    info = {
        "all": all_tests,
        "passed": passed_tests,
        "score": score,
        "err_type": err_type,
    }

    # 更新结果输出字段
    job.verdict("Accepted" if all_tests == passed_tests else "Wrong Answer")
    job.score(int(score))
    # summary = job.get_summary()
    # 渲染 HTML 模板页面（可选）
    # 被渲染的页面应位于 kernel/templates/html 目录下
    # job.detail(gg.render_template("index.html", author="Charles Zhang", summary=summary))
    comment = gg.render_template(
        "index.html", author="Charles Zhang", summary=show_summary, info=info
    )
    job.comment(comment)


def postwork_lab6(job: Job) -> dict:
    total_score = job.get_total_score()

    # 更新结果输出字段
    job_verdict = Verdict.Accept if total_score == 70 else Verdict.WrongAnswer
    job.verdict(job_verdict)
    job.score(total_score)
    # job.comment("Mission Complete")

    # 渲染信息
    info = {
        "all": len(job.get_testcases()),
        "passed": sum(result['verdict'] == Verdict.Accept for result in job.get_summary()),
        "score": total_score,
        "err_type": job_verdict
    }

    # 自定义排序
    def custom_sort_key(d: dict):
        s = d['name']
        match = re.search(r'(codegen|general)-(\d+)-.*.cminus', s)
        return (0 if match.group(1) == 'codegen' else 100) + int(match.group(2))

    # 渲染 HTML 模板页面（可选）
    # 被渲染的页面应位于 kernel/templates/html 目录下
    job.comment(gg.render_template(
        "index.html", summary=sorted(job.get_summary(), key=custom_sort_key), info=info
    ))
    job.set_config({
        'PATH': os.environ["PATH"],
        'list /usr/local/bin': os.listdir("/usr/local/bin"),
        'list /coursegrader': os.listdir("//coursegrader"),
    })
    job.secret(job.get_config())

