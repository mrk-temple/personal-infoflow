# 获取层入口：实际抓取逻辑都在 sources.py 的各适配器里。
from .sources import gather


def fetch_items(cfg):
    return gather(cfg)
