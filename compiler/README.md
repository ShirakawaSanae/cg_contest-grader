# compiler
version: 0.1

```
docker run --rm -e PYGRADING_DEBUG=true 
--mount type=bind,
source="/home/yang/2023_compiler_xiji/compiler/test/4-opt-phase1/testdata",
target="/coursegrader/testdata",
readonly --mount type=bind,
source="/home/yang/2023_compiler_xiji/compiler/test/4-opt-phase1/submits/ta",
target="/coursegrader/submit" 
--mount type=bind,
source="/home/yang/2023_compiler_xiji/compiler/kernel.pyz",
target="/coursegrader/dockerext/kernel.pyz" 
--entrypoint python3 lxq2lxq/compiler-env:latest /coursegrader/dockerext/kernel.pyz
```

## 安装
(该安装步骤在Ubuntu20.04,docker20.10.16环境下测试有效) 

如果安装过程较慢，可以换成国内源
可能需要安装Cython

```
pip install Cython
```

安装docker
```
sudo apt-get update
sudo apt-get install -y docker-ce
```

安装pygrading(安装包已置于compiler/docker/目录下)

```
cd compiler/docker/
pip install pygrading-1.1.8.dev0-py3-none-any.whl 
```

PyGrading的运行环境要求 **Python >= 3.5**，不支持Python2。


## 构建Docker镜像
```shell
python3 manage.py docker-build
```

## 导出Docker镜像
```shell
python3 manage.py docker-save
```

## 打包内核

```shell
python3 manage.py package
```

## 测试

```shell
python3 manage.py test
```

## 测试数据

对于测试数据的管理，可以先在本地测试，随后将文件提交到线上服务器。

在本地测试中，所有题目的测试数据位于\compiler\test 目录下，其对应的测试结果输出到\compiler\test_result 目录下。

项目中test目录应该包含所有的测试题目，每个题目一个子目录，目录名无限制。每个题目应包含testdata和submits两个子目录，testdata目录中应包含测试输入和标准输出，与希冀系统中“测试样编辑器”中“work”目录内容保持一致。submits目录中可有多个子目录，子目录名不限。每个子目录表示一个不同的提交，由于学生提交程序不仅仅有正确执行一种情况，还可能出现WA、CE、RE、TLE等多种情况，可以在此准备多个提交程序，以测试评测机应对不同情况的能力。若仅有一个提交，则submits可以简写成submit，submit中无需准备子目录（参见/test/a+b）。

项目中\compiler\test.json用于声明内核执行方式和需要进行测试的样例。其中submit_dir、testdata_dir、kernel_dir、entrypoint与希冀系统中的“提交文件挂载路径”、“测试数据挂载路径”、“内核扩展挂载路径”和“启动参数”保持一致。

test.json中的testcases字段用于声明需要进行测试的样例，为列表类型，其中每个元素为一个测试题目。每个题目对象必须拥有一个name字段，为题目名称，与test目录中的每个子目录一致。题目对象中的submits字段表示此题目的提交数据，为列表类型。其元素中name字段与此题目中submits中的子目录名一致，verdict，score等其他字段为此题目在此提交下的期望输出，若此题目仅有一个提交，也可以将submits简写成submit，甚至可以省略submits。

执行python manage.py test即可自动使用本机Docker程序运行所有的测试点，测试结果存放在test_result目录中。

在线上测试中，单个题目的测试数据可以通过**题目-编辑-测试数据编辑器**进行修改，其work目录下的内容应该于相对应的testdata目录下的内容保持一致。

由于本实验的各次作业公用同一个评测机，因此可以在测试数据中上传一份json配置文件，在kernel的py文件中对配置文件进行读取，根据不同的配置文件进行不同的测试

## 评测原理

对作业的评测过程主要通过 \kernel\prework.py,\kernel\run.py,\kernel\postwork.py 三个文件完成。

完成不同的作业评测，主要需要修改以上三个文件，以及在线评测的测试数据。

当学生点击提交时，希冀系统会自动使用指定的Docker镜像运行本评测核心，并将题目数据、学生提交内容及其他相关信息通过目录挂载或环境变量方式传入Docker容器中。评测机需要以恰当的方式运行学生所提交的程序，并根据其输出结果与标准答案进行比对，给出得分。数据挂载和结果输出的具体格式请参阅[通用评测开发指南](https://test.educg.net/admin/help/projJudge.jsp#dockerDev)。

PyGrading推荐将评测过程分为prework，run和postwork三个阶段。

prework为评测前准备，主要完成评测环境的初始化，对学生提交的程序进行编译，准备测试数据等工作。prework阶段必须使用pygrading.create_testcase(100)创建测试样例集，并将本次评测所使用的测试数据使用append函数添加到样例集中，最后使用job.set_testcase函数设置测试数据。

对于每一个testcase都会执行一次run函数。在run函数中需要正式运行学生程序，并将其结果与标准答案进行比对，以Json格式返回此测试点的评分。PyGrading会将多次运行run函数的结果组织成一个列表，列表的长度与测试样例集的长度相同。

在postwork中，可以使用job.get_summary()获得执行run函数的结果列表。postwork需要通过对象中的score、verdict、comment、detail、secret、rank等函数设置评测结果。为了获得更好的显示结果，comment、detail、secret三个字段中可以包含HTML标签。PyGrading中内置了jinja2实现HTML模板渲染。

## 关于开发
project_utils.py 执行test在对比输出结果能够被Json读取时 会正确打印test_result 并将comment detail 以html格式写入相应的html文件
而stdout则会被读取走 加载到平台的控制台上
若cg.is_terminate == true 则会终止run 和 postwork 

## 尚存bug
有些题目会故意将错误的文件作为输入，导致运行时报错，但这种报错是合理的，不应该被识别为Runtime Error。目前处理逻辑有点问题
错误原因： 正确的submits 和 某些testcase 会产生空的stdout 和 stderr(error at line 1 column 2 .....)
          错误的submits 和 某些testcase 会产生空的stdout 和 stderr(error : segmentation fault ....)
          没有想到好的区分办法
make -j 现在加上 -j会报错