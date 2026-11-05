#!/usr/bin/env bash
# personal-infoflow 的可移植入口：任何 agent（Claude Code / Hermes / 其它）都能调。
# 所有 CLI 参数原样透传给 `python -m infoflow`（如 --refresh-profile / --feedback / -v）。
#
# 仓库根（INFOFLOW_HOME）解析顺序：
#   1) 环境变量 INFOFLOW_HOME
#   2) 脚本在仓库内时，按脚本位置推导（<repo>/skill/personal-infoflow/scripts/）
#   3) install.sh 写下的 scripts/home_path 文件（脚本被装到仓库外时用）
# Python 解析顺序：INFOFLOW_PYTHON → <repo>/.venv/bin/python → python3
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

HOME_DIR="${INFOFLOW_HOME:-}"
if [[ -z "$HOME_DIR" ]]; then
  cand="$(cd "$SCRIPT_DIR/../../.." 2>/dev/null && pwd || true)"
  if [[ -n "$cand" && -d "$cand/infoflow" ]]; then
    HOME_DIR="$cand"
  elif [[ -f "$SCRIPT_DIR/home_path" ]]; then
    HOME_DIR="$(cat "$SCRIPT_DIR/home_path")"
  fi
fi
if [[ -z "$HOME_DIR" || ! -d "$HOME_DIR/infoflow" ]]; then
  echo "找不到 personal-infoflow 仓库根。" >&2
  echo "请设 INFOFLOW_HOME 指向仓库根目录，或在仓库里运行 skill/personal-infoflow/install.sh。" >&2
  exit 1
fi

PY="${INFOFLOW_PYTHON:-}"
if [[ -z "$PY" ]]; then
  if [[ -x "$HOME_DIR/.venv/bin/python" ]]; then
    PY="$HOME_DIR/.venv/bin/python"
  else
    PY="python3"
  fi
fi

# cwd 必须是仓库根：client.py 用 find_dotenv(usecwd=True) 读 .env，main 默认读 ./config.yaml。
cd "$HOME_DIR"
exec "$PY" -m infoflow "$@"
