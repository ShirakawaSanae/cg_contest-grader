FROM ubuntu:20.04
LABEL maintainer="your-name <your-email>"
USER root

RUN sed -i s@/archive.ubuntu.com/@/mirrors.tuna.tsinghua.edu.cn/@g /etc/apt/sources.list && apt update
RUN apt install -y --no-install-recommends python3 python3-pip gcc libc-dev
RUN pip3 config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
RUN rm -rf /var/lib/apt/lists/*

{% if "dev" in version %}
COPY pygrading-{{version}}-py3-none-any.whl /pygrading-{{version}}-py3-none-any.whl
RUN pip3 install /pygrading-{{version}}-py3-none-any.whl
{% else %}
RUN pip3 install pygrading=={{version}}
{% endif %}


RUN groupadd -r cguser && useradd --no-log-init -m -r -g cguser cguser
USER cguser
ENV PATH=$PATH:/usr/bin
ENTRYPOINT ["python3", "/coursegrader/dockerext/kernel.pyz"]