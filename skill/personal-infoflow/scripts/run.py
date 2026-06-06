#!/usr/bin/env python3
"""Hermes skill 的薄入口：在 personal-infoflow 仓库里用配好的 venv 跑核心管线。

需要两个环境变量：
    INFOFLOW_HOME    指向 personal-infoflow 仓库根目录
    INFOFLOW_PYTHON  指向已装好依赖的虚拟环境的 python（如 ~/infoflow-venv/bin/python）
"""
import os
import sys
import subprocess

home = os.environ.get("INFOFLOW_HOME")
if not home or not os.path.isdir(home):
    sys.exit("INFOFLOW_HOME 未设置或无效。请指向 personal-infoflow 仓库根目录。")

py = os.environ.get("INFOFLOW_PYTHON")
if not py:
    sys.exit("INFOFLOW_PYTHON 未设置。请指向已装好依赖的虚拟环境的 python"
             "（如 ~/infoflow-venv/bin/python）。不要用系统 python，也不要在仓库里新建环境。")
if not os.path.isfile(py):
    sys.exit(f"INFOFLOW_PYTHON 指向的解释器不存在：{py}")

cmd = [py, "-m", "infoflow.main", *sys.argv[1:]]
sys.exit(subprocess.call(cmd, cwd=home))
