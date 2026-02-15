#!/bin/bash
echo "=== [Ascend 环境初始化脚本] 开始执行 ==="
export PATH=/usr/local/python3.11.13/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/Ascend/driver/lib64:/usr/local/Ascend/driver/lib64/common:/usr/local/Ascend/driver/lib64/driver:$LD_LIBRARY_PATH

if [ -f /usr/local/Ascend/ascend-toolkit/set_env.sh ]; then
    source /usr/local/Ascend/ascend-toolkit/set_env.sh
    echo "[OK] 已加载 Ascend Toolkit 环境"
else
    echo "[ERROR] 未找到 /usr/local/Ascend/ascend-toolkit/set_env.sh"
    exit 1
fi


