<h1>
    Pygrading
</h1>

往年脚本都放在Compiler目录下
CourseGrading(希冀)信息类专业教学与科研一体化平台开发用Python工具包

<p>
	<a href="http://www.educg.net/">
		<img src="https://img.shields.io/badge/site-CG-red" alt="Official Site">
	</a>
    <!--
	<a href="https://pypi.org/project/pygrading/">
		<img src="https://img.shields.io/badge/pypi-v1.1.7-orange" alt="Pypi package">
	</a>
	<a href='https://pygrading.readthedocs.io/en/latest/?badge=latest'>
		<img src='https://readthedocs.org/projects/pygrading/badge/?version=latest' alt='Documentation Status' />
	</a>
	-->
	<a href="https://github.com/PhenomingZ/PyGrading/blob/master/LICENSE">
		<img src="https://img.shields.io/github/license/PhenomingZ/PyGrading" alt="GitHub license">
	</a>
</p>
<p>
	<a href="#what-is-it">What is it</a> •
	<a href="#install">Install</a> •
	<a href="#quick-start">Quick Start</a> •
	<a href="#change-log">Change Log</a> •
	<a href="#faq">FAQ</a> •
	<a href="http://www.educg.net/" target="_blank">CG Site</a>
</p>
## What is it

**希冀平台** 全面支撑计算机、大数据、人工智能、集成电路、信息安全、机器人、金融科技、区块链等专业建设。 基于平台建成了涵盖实验、质量指标及过程控制的完整在线实验体系，实现了“任何人、任何时间、任何地点均能开展实验学习”的目标。

**通用评测** 是一个通用的自动评测框架，基于该框架可以定制开发任何自己需要的自动评测内核。

**PyGrading工具包** 目前该工具包包含以下功能：

1. 支持CourseGrading平台通用评测内核快速构建；
2. 支持适用于通用评测题、云桌面环境和Jupyter实验环境的评测结果JSON串的快速生成；
2. 支持HTML标签文本内容的快速生成，绝对好用的HTML生成工具；

希望使用本工具能够提高大家的工作效率，祝各位开发顺利！

## Install

~~使用pip可以轻松安装PyGrading：~~
可能要安装Cython
请在[Release](https://gitlab.educg.net/wangmingjian/pygrading/-/releases)中下载最新的whl文件进行安装。

```bash
pip install pygrading-xxx-py3-none-any.whl
```

PyGrading的运行环境要求 **Python >= 3.5**，不支持Python2。

## Quick Start

使用以下命令可以快速生成PyGrading开发模板。

```bash
python -m pygrading init [项目名]
```

PyGrading会自动在当前目录下创建*项目名*目录，其中包含一个简单的C语言评测核心，您可以在此基础上进行修改以满足具体评测需求。若未指定*项目名*，则默认名称为cg-kernel。

PyGrading项目文件如下：

``` 
cg-kernel
  | docker  包含用于构建Docker镜像的Dockerfile和其他必要文件。
  | test    包含进行本地测试所需样例文件。
  | kernel  PyGrading评测机主体。
  | manage.py  项目管理辅助工具。
  + test.json  声明进行本地测试所需的样例极其期望测试结果。
```

**注意：目前您必须手动将pygrading-xxx-py3-none-any.whl复制到docker目录中，才可以进行后续操作。**

### 构建Docker镜像

使用以下命令可使用docker目录的Dockerfile文件在本机构建docker镜像。

```shell
python manage.py docker-build
```

### 导出Docker镜像

使用以下命令会将本机docker镜像导出为tar.gz格式，可作为评测镜像上传到希冀系统中。

```shell
python manage.py docker-save
```

### 打包内核

使用以下命令可以将编写好的评测内核打包成pyz文件，可作为内核扩展上传到希冀系统中。

```shell
python manage.py package
```

### 测试

使用以下命令可以在本机运行测试样例，以确保评测机可以正常运行。具体请参阅<a href="#test">Test</a>节。

```shell
python manage.py test
```

## PyGrading评测原理

当学生点击提交时，希冀系统会自动使用指定的Docker镜像运行本评测核心，并将题目数据、学生提交内容及其他相关信息通过目录挂载或环境变量方式传入Docker容器中。评测机需要以恰当的方式运行学生所提交的程序，并根据其输出结果与标准答案进行比对，给出得分。数据挂载和结果输出的具体格式请参阅[通用评测开发指南](https://test.educg.net/admin/help/projJudge.jsp#dockerDev)。

PyGrading推荐将评测过程分为prework，run和postwork三个阶段。

prework为评测前准备，主要完成评测环境的初始化，对学生提交的程序进行编译，准备测试数据等工作。prework阶段必须使用pygrading.create_testcase(100)创建测试样例集，并将本次评测所使用的测试数据使用append函数添加到样例集中，最后使用job.set_testcase函数设置测试数据。

对于每一个testcase都会执行一次run函数。在run函数中需要正式运行学生程序，并将其结果与标准答案进行比对，以Json格式返回此测试点的评分。PyGrading会将多次运行run函数的结果组织成一个列表，列表的长度与测试样例集的长度相同。

在postwork中，可以使用job.get_summary()获得执行run函数的结果列表。postwork需要通过对象中的score、verdict、comment、detail、secret、rank等函数设置评测结果。为了获得更好的显示结果，comment、detail、secret三个字段中可以包含HTML标签。PyGrading中内置了jinja2实现HTML模板渲染。

## Test

为了避免开发时频分地上传评测镜像和内核扩展，PyGrading提供了本地测试功能，可以在本地运行预设的测试样例，及时发现评测镜像中的问题。

项目中test目录应该包含所有的测试题目，每个题目一个子目录，目录名无限制。每个题目应包含testdata和submits两个子目录，testdata目录中应包含测试输入和标准输出，与希冀系统中“测试样编辑器”中“work”目录内容保持一致。submits目录中可有多个子目录，子目录名不限。每个子目录表示一个不同的提交，由于学生提交程序不仅仅有正确执行一种情况，还可能出现WA、CE、RE、TLE等多种情况，可以在此准备多个提交程序，以测试评测机应对不同情况的能力。若仅有一个提交，则submits可以简写成submit，submit中无需准备子目录（参见/test/a+b）。

项目中test.json用于声明内核执行方式和需要进行测试的样例。其中submit_dir、testdata_dir、kernel_dir、entrypoint与希冀系统中的“提交文件挂载路径”、“测试数据挂载路径”、“内核扩展挂载路径”和“启动参数”保持一致。

test.json中的testcases字段用于声明需要进行测试的样例，为列表类型，其中每个元素为一个测试题目。每个题目对象必须拥有一个name字段，为题目名称，与test目录中的每个子目录一致。题目对象中的submits字段表示此题目的提交数据，为列表类型。其元素中name字段与此题目中submits中的子目录名一致，verdict，score等其他字段为此题目在此提交下的期望输出，若此题目仅有一个提交，也可以将submits简写成submit，甚至可以省略submits。

执行python manage.py test即可自动使用本机Docker程序运行所有的测试点，测试结果存放在test_result目录中。

