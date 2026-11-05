"""CLI 入口：``python -m infoflow`` 或装包后的 ``infoflow`` 命令。"""
import argparse
import logging
import sys

from .client import get_client
from .config import load_config
from .pipeline import run

DEFAULT_CFG = "config.yaml"


def main(argv=None):
    ap = argparse.ArgumentParser(prog="infoflow", description="个人信息流")
    ap.add_argument("--config", default=DEFAULT_CFG)
    ap.add_argument("--refresh-profile", action="store_true", help="重建兴趣画像（会带上最新反馈）")
    ap.add_argument("--portrait", action="store_true", help="单独重新生成画像配图")
    ap.add_argument("--feedback", action="store_true", help="只收集反馈并打印汇总，不抓取")
    ap.add_argument("--web", action="store_true", help="启动 Web 界面（浏览器里跑管线、读简报、标反馈）")
    ap.add_argument("--web-host", default="127.0.0.1", help="Web 界面监听地址（默认仅本机）")
    ap.add_argument("--web-port", type=int, default=7781, help="Web 界面端口（默认 7781）")
    ap.add_argument("-v", "--verbose", action="store_true", help="打印更详细的调试日志")
    args = ap.parse_args(argv)

    # 用纯消息格式 + 走 stdout，让日志和 pipeline 的进度行同流、顺序一致；
    # --verbose 时降到 DEBUG。
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(message)s",
        stream=sys.stdout,
    )
    # 第三方库（openai/httpx）的 INFO 噪音（"HTTP Request: POST ..."）压到 WARNING。
    for noisy in ("httpx", "httpcore", "openai", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    cfg = load_config(args.config)

    if args.web:
        from .web import serve
        serve(cfg, host=args.web_host, port=args.web_port)
        return

    client = get_client()

    run(cfg, client,
        refresh_profile=args.refresh_profile,
        portrait=args.portrait,
        feedback_only=args.feedback)


if __name__ == "__main__":
    main()
