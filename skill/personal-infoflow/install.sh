#!/usr/bin/env bash
# 把 personal-infoflow skill 装到某个 agent 的 skills 目录。
#
#   用法： ./install.sh [目标skills目录]
#   默认目标：~/.claude/skills   （Claude Code）
#   Hermes 等：./install.sh /path/to/hermes/skills
#
# 它会把 SKILL.md / scripts / references 复制到 <目标>/personal-infoflow/，
# 并写下 scripts/home_path 记录本仓库根路径——这样装到仓库外也能找回仓库。
set -euo pipefail

SKILL_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"          # .../skill/personal-infoflow
REPO_HOME="$(cd "$SKILL_SRC/../.." && pwd)"                         # 仓库根
TARGET_BASE="${1:-$HOME/.claude/skills}"
DEST="$TARGET_BASE/personal-infoflow"

mkdir -p "$DEST/scripts" "$DEST/references"
cp "$SKILL_SRC/SKILL.md" "$DEST/SKILL.md"
cp "$SKILL_SRC/README.md" "$DEST/README.md" 2>/dev/null || true
cp "$SKILL_SRC/scripts/run.sh" "$DEST/scripts/run.sh"
cp "$SKILL_SRC/scripts/run.py" "$DEST/scripts/run.py"
cp "$SKILL_SRC"/references/*.md "$DEST/references/" 2>/dev/null || true
chmod +x "$DEST/scripts/run.sh" "$DEST/scripts/run.py"

# 记录仓库根，供装在仓库外的副本回找。
printf '%s\n' "$REPO_HOME" > "$DEST/scripts/home_path"

echo "已安装 personal-infoflow skill 到：$DEST"
echo "仓库根（home_path）：$REPO_HOME"
echo "自测： $DEST/scripts/run.sh --feedback"
