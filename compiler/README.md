# 评测脚本编写与内核制作

## 一、文件结构

```
cg_contest-grader (省略号表示不用在意，只需要关注列出来的文件)
  |...
  |--compiler (主要修改部分)
     |--backup-kernels (每次导出内核会在这里备份)
     |--coursegrader   (笔者本地测试时的尝试，可以忽略)
     |--docker         (构建镜像时会调用其中的Dockerfile)
     	|--Dockerfile  (根据需要修改)
     	|--pygrading-1.1.8.dev0-py3-none-any.whl (希冀官方提供的包，需要手动传入镜像)
     |--kernel         (主要修改部分)
     	|...
     	|--exception.py(应对测评异常的脚本)
     	|--prework.py  (测评预处理脚本，兼加载测试数据)
     	|--run.py      (测评运行脚本，兼分数计算)
     	|--postwork.py (测评收尾脚本，兼生成学生可看到的测评结果)
     |--test           (测试数据存放在这里)
     |--README.md      (本文)
     |--kernel.pyz     (每次导出内核会在这里留下最新版本)
     |--manage.py      (希冀制作镜像和评测内核的主要程序)
     |--make.sh        (便捷制作镜像)
     |--test.json      (本地测试时需要修改此配置)
     
  |...
  |--README.md (希冀官方的README，包含脚本和内核的介绍)
  |--pygrading-1.1.8.dev0-py3-none-any.whl (希冀官方提供的包，需要手动传入镜像)
```



## 二、我们需要做什么 - 流程

**TLDR:** 我们需要（1）修改 `prework.py` `run.py` `postwork.py` 和 `test.json`，来执行正确的测评逻辑；（2）向 `test` 文件夹中添加测试数据和提交文件，以适配不同的题目；（3）修改 `Dockerfile` 以正确生成评测所需的环境镜像；（4）进行本地测试并导出 `kernel.pyz` ；（5）在通过本地测试之后，将内核文件 `kernel.pyz` 和对应的 `Dockerfile` 放到希冀平台的通用评测工作台中的镜像（Docker）里，再把测试数据也传到希冀上，使同学们能在希冀上测评。本文后续将分别介绍（1）~（5）部分。

**评测原理是什么？**在希冀平台上，当学生点击提交时，希冀系统会自动使用指定的 Docker 镜像运行本评测核心，并将题目数据、学生提交内容及其他相关信息通过目录挂载或环境变量方式传入 Docker 容器中。评测机需要以恰当的方式运行学生所提交的程序，并根据其输出结果与标准答案进行比对，给出得分。

为保证学生使用的流畅性，我们需要先进行本地测试，实际上就是在本地模拟评测机行为。下面是希冀官方给出的一段描述：

> <font face="楷体">对于测试数据的管理，可以先在本地测试，随后将文件提交到线上服务器。</font>
>
> <font face="楷体">在本地测试中，所有题目的测试数据位于\compiler\test 目录下，其对应的测试结果输出到\compiler\test_result 目录下。</font>
>
> <font face="楷体">项目中test目录应该包含所有的测试题目，每个题目一个子目录，目录名无限制。**每个题目应包含testdata和submits两个子目录，testdata目录中应包含测试输入和标准输出，与希冀系统中“测试数据编辑器”中“work”目录内容保持一致。submits目录中可有多个子目录，子目录名不限。每个子目录表示一个不同的提交，**由于学生提交程序不仅仅有正确执行一种情况，还可能出现WA、CE、RE、TLE等多种情况，可以在此准备多个提交程序，以测试评测机应对不同情况的能力。</font>
>
> **<font face="楷体">项目中\compiler\test.json用于声明内核执行方式和需要进行测试的样例。其中submit_dir、testdata_dir、kernel_dir、entrypoint与希冀系统中的“提交文件挂载路径”、“测试数据挂载路径”、“内核扩展挂载路径”和“启动参数”保持一致。</font>**
>
> <font face="楷体">test.json中的testcases字段用于声明需要进行测试的样例，为列表类型，其中每个元素为一个测试题目。每个题目对象必须拥有一个name字段，为题目名称，与test目录中的每个子目录一致。题目对象中的submits字段表示此题目的提交数据，为列表类型。其元素中name字段与此题目中submits中的子目录名一致，verdict，score等其他字段为此题目在此提交下的期望输出，若此题目仅有一个提交，也可以将submits简写成submit，甚至可以省略submits。</font>
>
> <font face="楷体">执行python manage.py test即可自动使用本机Docker程序运行所有的测试点，测试结果存放在test_result目录中。</font>
>
> <font face="楷体">在线上测试中，单个题目的测试数据可以通过**题目-编辑-测试数据编辑器**进行修改，**其work目录下的内容应该与相对应的testdata目录下的内容保持一致。**</font>
>
> <font face="楷体">**PyGrading推荐将评测过程分为prework，run和postwork三个阶段**。</font>
>
> <font face="楷体">prework为评测前准备，主要完成评测环境的初始化，对学生提交的程序进行编译，准备测试数据等工作。prework阶段必须使用pygrading.create_testcase(100)创建测试样例集，并将本次评测所使用的测试数据使用append函数添加到样例集中，最后使用job.set_testcase函数设置测试数据。</font>
>
> <font face="楷体">对于每一个testcase都会执行一次run函数。在run函数中需要正式运行学生程序，并将其结果与标准答案进行比对，以Json格式返回此测试点的评分。PyGrading会将多次运行run函数的结果组织成一个列表，列表的长度与测试样例集的长度相同。</font>
>
> <font face="楷体">在postwork中，可以使用job.get_summary()获得执行run函数的结果列表。postwork需要通过对象中的score、verdict、comment、detail、secret、rank等函数设置评测结果。为了获得更好的显示结果，comment、detail、secret三个字段中可以包含HTML标签。PyGrading中内置了jinja2实现HTML模板渲染。</font>



## 更多内容见 README.pdf



