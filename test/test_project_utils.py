import json
import time
import unittest
import shutil
import os


class ProjectTest(unittest.TestCase):
    def test_all(self):
        # 构建
        project_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
        shutil.rmtree(os.path.join(project_path, "build"), ignore_errors=True)
        shutil.rmtree(os.path.join(project_path, "dist"), ignore_errors=True)
        shutil.rmtree(os.path.join(project_path, "pygrading.egg-info"), ignore_errors=True)
        self.assertEqual(os.path.exists(os.path.join(project_path, "build")), False)
        self.assertEqual(os.path.exists(os.path.join(project_path, "dist")), False)
        self.assertEqual(os.path.exists(os.path.join(project_path, "pygrading.egg-info")), False)
        os.system(f"cd {project_path} && python setup.py sdist bdist_wheel")
        whls = [x for x in os.listdir(os.path.join(project_path, "dist")) if x[-4:] == ".whl"]
        self.assertEqual(len(whls), 1)
        whl_path = os.path.join(os.getcwd(), os.path.join(project_path, "dist"), whls[0])
        # 创建虚拟环境
        os.system("python -m venv --clear env")
        python = os.path.join("env", "Scripts", "python")
        os.system(f"{python} -m pip install {whl_path}")
        # 开始测试
        shutil.rmtree("cg-kernel", ignore_errors=True)
        os.system(f"{python} -m pygrading init")
        shutil.copyfile(whl_path, f"cg-kernel/docker/{whls[0]}")
        os.system(f"{python} cg-kernel/manage.py package")
        os.system(f"{python} cg-kernel/manage.py docker-build")
        os.system(f"{python} cg-kernel/manage.py test")

        self.assertEqual(os.path.exists("cg-kernel/test_result/summary.json"), True)
        summary = json.load(open("cg-kernel/test_result/summary.json", encoding='utf-8'))
        summary = [v["asserts"] for k, v in summary.items()]
        summary = all(x['res'] for x in sum(summary, []))
        self.assertEqual(summary, True)
        # os.makedirs("docker", exist_ok=True)
        # shutil.copyfile(self.whl_path, "docker/pygrading-1.1.8.dev0-py3-none-any.whl")
        # os.system("cd docker && docker build --rm -t test_pygrading .")
        # time.sleep(1)
        # os.system("docker run -it --rm --privileged -v //var/run/docker.sock:/var/run/docker.sock test_pygrading")


if __name__ == '__main__':
    unittest.main()

"""
docker run --rm -v "/cg-kernel/test/a+b/testdata:/coursegrader/testdata" -v "/cg-kernel/test/a+b/submit:/coursegrader/submit" -v "/cg-kernel/kernel.pyz:/coursegrader/dockerext/kernel.pyz" --entrypoint python3 cg-kernel:0.1 /coursegrader/dockerext/kernel.pyz
"""