#### this is for x86 machine, lxq2lxq/compiler-env pre-installs cross compiling tools and project build tools
FROM lxq2lxq/compiler-env
USER root
RUN sed -i s@/security.ubuntu.com/@/mirrors.ustc.edu.cn/@g /etc/apt/sources.list && apt update
RUN apt install -y --no-install-recommends python3-pip
RUN pip3 config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
RUN rm -rf /var/lib/apt/lists/*
install essential prerequisites for 2023-jianmu building
RUN export DEBIAN_FRONTEND=noninteractive && \
    apt update && \
    apt dist-upgrade -y && \
    apt install --no-install-recommends -y \
            llvm-dev build-essential \
            python3 python3-pip\
            libglib2.0-0 libgmp-dev \
            zlib1g zlib1g-dev \
            && \
    apt-get autoremove -y && \
    apt-get autoclean -y
COPY pygrading-1.1.8.dev0-py3-none-any.whl /pygrading-1.1.8.dev0-py3-none-any.whl
RUN pip3 install /pygrading-1.1.8.dev0-py3-none-any.whl
RUN pip3 install json5
ENTRYPOINT ["python3", "/coursegrader/dockerext/kernel.pyz"]

#### this is for loongson machine, configure tools necessary for builing project and course grading 
# FROM loongsongd/debian:v10.3-mini

# # install essential prerequisites for 2023-jianmu building
# RUN export DEBIAN_FRONTEND=noninteractive && \
#     apt update && \
#     apt dist-upgrade -y && \
#     apt install --no-install-recommends -y \
#             llvm-dev git build-essential cmake flex bison \
#             python3 python3-pip\
#             libglib2.0-0 libgmp-dev \
#             zlib1g zlib1g-dev \
#             && \
#     apt-get autoremove -y && \
#     apt-get autoclean -y

# # pygrading requirements
# RUN pip3 install json5 setuptools wheel
# COPY pygrading-1.1.8.dev0-py3-none-any.whl /pygrading-1.1.8.dev0-py3-none-any.whl
# RUN pip3 install /pygrading-1.1.8.dev0-py3-none-any.whl

# USER root
# ENTRYPOINT ["python3", "/coursegrader/dockerext/kernel.pyz"]