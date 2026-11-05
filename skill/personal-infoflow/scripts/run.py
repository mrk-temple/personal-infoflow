#!/usr/bin/env python3
"""personal-infoflow 的可移植入口（给偏好直接调 Python 脚本的 agent，如 Hermes）。

与 run.sh 等价：自动解析仓库根与解释器，把 CLI 参数透传给 ``python -m infoflow``。

仓库根解析顺序：INFOFLOW_HOME → 脚本在仓库内的相对位置 → install.sh 写的 home_path。
解释器解析顺序：INFOFLOW_PYTHON → <repo>/.venv/bin/python → 当前 sys.executable。
"""
import os
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def resolve_home() -> Path:
    env = os.environ.get("INFOFLOW_HOME")
    if env and (Path(env) / "infoflow").is_dir():
        return Path(env)
    cand = SCRIPT_DIR.parents[2]  # <repo>/skill/personal-infoflow/scripts → <repo>
    if (cand / "infoflow").is_dir():
        return cand
    hp = SCRIPT_DIR / "home_path"
    if hp.is_file():
        p = Path(hp.read_text(encoding="utf-8").strip())
        if (p / "infoflow").is_dir():
            return p
    sys.exit(
        "找不到 personal-infoflow 仓库根。\n"
        "请设 INFOFLOW_HOME 指向仓库根目录，或在仓库里运行 skill/personal-infoflow/install.sh。"
    )


def resolve_python(home: Path) -> str:
    env = os.environ.get("INFOFLOW_PYTHON")
    if env:
        if not Path(env).is_file():
            sys.exit(f"INFOFLOW_PYTHON 指向的解释器不存在：{env}")
        return env
    venv = home / ".venv" / "bin" / "python"
    return str(venv) if venv.is_file() else sys.executable


def main():
    home = resolve_home()
    py = resolve_python(home)
    sys.exit(subprocess.call([py, "-m", "infoflow", *sys.argv[1:]], cwd=home))


if __name__ == "__main__":
    main()
