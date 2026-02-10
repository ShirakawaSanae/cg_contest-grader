"""
    Name: project_utils.py
    Author: Charles Zhang <694556046@qq.com>
    Propose: Initialize a pygrading project
    Coding: UTF-8
"""
import json
import os
import pkgutil
import subprocess
import time
from datetime import datetime

import fire
import pytz

from pygrading.utils import makedirs
from jinja2 import Template
import pygrading as gg
import shutil
import zipapp


def render_file(pkg_path, target_path, name, **kwargs):
    data = pkgutil.get_data(__package__, pkg_path).decode()
    template = Template(data)
    with open(os.path.join(target_path, name), "w", encoding='utf-8') as f:
        f.write(template.render(**kwargs))
    print(f"render {pkg_path} done.")


def copy_file(pkg_path, target_path, name):
    data = pkgutil.get_data(__package__, pkg_path)
    with open(os.path.join(target_path, name), 'wb') as f:
        f.write(data)
    # writefile(os.path.join(target_path, name), data)
    print(f"copy {pkg_path} done.")


def init(name="cg-kernel"):
    path = os.getcwd()
    """ Initialize a pygrading project """

    print("Create project folder", end="")
    new_project_path = os.path.join(path, name)
    if os.path.exists(new_project_path) and len(os.listdir(new_project_path)) > 0:
        raise RuntimeError(f"{new_project_path} is already exists.")
    render_file_list = ['README.md', 'manage.py', 'docker/Dockerfile']
    copy_file_list = pkgutil.get_data(__package__, 'static/copy_files.txt').decode().replace('\r', '').split('\n')
    render_data = {
        'proj_name': name,
        'version': gg.__version__
    }
    for file in copy_file_list:
        if not file:
            continue
        ori_path = os.path.join('static', file)
        folder, file_name = os.path.split(file)
        folder = os.path.join(new_project_path, folder)
        makedirs(folder, exist_ok=True)
        if file in render_file_list:
            render_file(ori_path, folder, file_name, **render_data)
        else:
            copy_file(ori_path, folder, file_name)

    print("Initialization Completed!")


project_name = None
project_version = None


def package(backup=True):
    if os.path.exists("kernel.pyz"):
        os.remove("kernel.pyz")
    zipapp.create_archive(os.path.join(os.getcwd(), "kernel"), "kernel.pyz")
    if backup:
        now = datetime.now(pytz.timezone("Asia/Shanghai")).strftime("%Y-%m-%d-%H-%M")
        os.makedirs("backup-kernels", exist_ok=True)
        shutil.copyfile("kernel.pyz", f"backup-kernels/kernel-{now}.pyz")


def build_docker():
    os.system(f"cd docker && docker build --force-rm -t {project_name}:{project_version} .")


def save_docker():
    for cmd in ["pigz", "zgip"]:
        if shutil.which(cmd):
            tar_name = f"{project_name}_{project_version.replace('.', '-')}.tar.gz"
            run = f"docker save {project_name}:{project_version} | {cmd} > {tar_name}"
            print(run)
            os.system(run)
            return tar_name
    raise RuntimeError("No pigz or zgip")


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def test():
    meta = json.load(open(os.path.join(os.getcwd(), "test.json")))
    testdata_dir = meta["testdata_dir"]
    submit_dir = meta["submit_dir"]
    kernel_dir = meta["kernel_dir"]
    kernel = f"{kernel_dir}/kernel.pyz"
    local_kernel = os.path.join(os.getcwd(), "kernel.pyz")
    entrypoint = meta["entrypoint"]
    testcases = meta["testcases"]
    test_dir = os.path.join(os.getcwd(), "test")
    result_root = os.path.join(os.getcwd(), "test_result")
    shutil.rmtree(result_root, ignore_errors=True)
    all_cnt, pass_cnt = 0, 0
    all_result = {}
    for case in testcases:
        name = case["name"]
        if 'submits' in case:
            submits = case['submits']
            for item in submits:
                item['path'] = os.path.join(test_dir, name, "submits", item['name'])
        else:
            if 'submit' in case:
                submits = [case['submit']]
            else:
                submits = [{k: v for k, v in case.items() if k != 'name'}]
            submits[0]['name'] = 'submit'
            submits[0]['path'] = os.path.join(test_dir, name, 'submit')
        # 开始测试
        local_testdata_dir = os.path.join(test_dir, name, "testdata")
        timeout = case.get("timeout")
        for submit in submits:
            print(f"test:{name} submit:{submit['name']}  ... ", end='')
            local_submit_dir = submit['path']
            if not os.path.exists(local_submit_dir):
                raise RuntimeError(f"no submit dir {local_submit_dir}")
            begin = time.time()
            cmd = ' '.join(["docker", "run", "--rm",
                            "-e PYGRADING_DEBUG=true",
                            "--mount", f'type=bind,source="{local_testdata_dir}",target="{testdata_dir}",readonly',
                            "--mount", f'type=bind,source="{local_submit_dir}",target="{submit_dir}"',
                            "--mount", f'type=bind,source="{local_kernel}",target="{kernel}"',
                            "--entrypoint", entrypoint[0], f"{project_name}:{project_version}",
                            ' '.join(entrypoint[1:])])
            # print(cmd)
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf8")
            out, err = process.communicate(timeout=timeout)
            end = time.time()
            exec_time = int((end - begin) * 1000)
            result_dir = os.path.join(result_root, name, submit['name'])
            shutil.rmtree(result_dir, ignore_errors=True)
            os.makedirs(result_dir)
            write_file(os.path.join(result_dir, "stdout.txt"), out)
            write_file(os.path.join(result_dir, "stderr.txt"), err)
            summary = {"exec_time": exec_time, 'cmd': cmd}
            # print(summary['cmd'])
            try:
                result = json.loads(out)
                assert_result = [
                    {'what': k, 'exp': v, 'act': result.get(k), 'res': v == result.get(k)}
                    for k, v in submit.items() if k not in ('name', 'path')]
                summary['asserts'] = assert_result
                write_file(os.path.join(result_dir, "comment.html"), result['comment'])
                write_file(os.path.join(result_dir, "detail.html"), result.get("detail", "None"))
            except Exception as e:
                summary['error'] = repr(e)
            all_result[name + "--" + submit['name']] = summary
            with open(os.path.join(result_dir, "summary.json"), "w") as f:
                json.dump(summary, f)
            print(f"exec time: {exec_time}, error: {summary.get('error')}")
            final_result = False
            if 'asserts' in summary:
                print("what|expect|actual|result")
                for item in summary['asserts']:
                    print(f"{item['what']}|{item['exp']}|{item['act']}|{item['res']}")
                final_result = all([x['res'] for x in summary['asserts']])
            print(f"========== SUCCESS:{final_result}")
            all_cnt += 1
            if final_result:
                pass_cnt += 1
    with open(os.path.join(result_root, 'summary.json'), 'w', encoding='utf-8') as f:
        json.dump(all_result, f)
    print(f"{pass_cnt}/{all_cnt} TESTS PASSED!")
    return pass_cnt == all_cnt


def main(proj_name, proj_version, require_version=None):
    # assert (require_version == gg.__version__)
    global project_name, project_version
    project_name = proj_name
    project_version = proj_version
    fire.Fire({
        "info": f"{project_name}:{project_version}",
        "package": package,
        "docker-build": build_docker,
        "docker-save": save_docker,
        "test": test
    })
