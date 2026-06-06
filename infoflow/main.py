import pathlib
import argparse

import yaml

from .client import get_client
from .pipeline import run

DEFAULT_CFG = "config.yaml"


def main():
    ap = argparse.ArgumentParser(description="个人信息流")
    ap.add_argument("--config", default=DEFAULT_CFG)
    ap.add_argument("--refresh-profile", action="store_true", help="重建兴趣画像（会带上最新反馈）")
    ap.add_argument("--portrait", action="store_true", help="单独重新生成画像配图")
    ap.add_argument("--feedback", action="store_true", help="只收集反馈并打印汇总，不抓取")
    args = ap.parse_args()

    cfg_path = pathlib.Path(args.config)
    if not cfg_path.exists():
        raise SystemExit(
            f"没找到配置文件 {cfg_path}。\n"
            f"先复制模板：cp config.example.yaml config.yaml，再编辑里面的路径和源。"
        )
    cfg = yaml.safe_load(open(cfg_path, encoding="utf-8"))
    client = get_client()

    run(cfg, client,
        refresh_profile=args.refresh_profile,
        portrait=args.portrait,
        feedback_only=args.feedback)


if __name__ == "__main__":
    main()
