'''
    Name: setup.py
    Author: Charles Zhang <694556046@qq.com>
    Propose: Setup script for pygrading!
    Coding: UTF-8
'''

# python setup.py sdist bdist_wheel
# python -m twine upload dist/*

import setuptools

from pygrading import __version__

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()


import os
file_list = ([os.path.join(path, file) for file in file_list] for path, dir_list, file_list in os.walk("pygrading/static"))
file_list = [x.replace("pygrading/", "").replace('\\', '/') for x in sum(file_list, [])]
with open("pygrading/static/copy_files.txt", "w", encoding="utf-8") as f:
    f.write('\n'.join(x[len("static/"):] for x in file_list))
file_list.append("copy_files.txt")

setuptools.setup(
    name='pygrading',
    version=__version__,
    author='Charles Zhang',
    author_email='694556046@qq.com',
    description='A Python ToolBox for CourseGrading platform.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://gitlab.educg.net/zhangmingyuan/PyGrading',
    packages=['pygrading', 'cg_learning'],
    package_data={
        'pygrading': file_list
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.5',
    install_requires=[
        'Jinja2>=2.11.2',
        'fire>=0.3.1',
        'PyJWT>=2.0.1',
        'requests>=2.21.0',
        'pytz',
        'Cython'
    ],
)
