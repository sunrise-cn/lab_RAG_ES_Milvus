"""实验 14 主测量：insert 之后立刻查，三种一致性级别各自能看到几条。

核心方法：同一批 100 条用已知 id 插入，insert 返回后"同一口气"里用
query 数这批 id 可见几条。Strong 是保证（每一轮都该是 100），
其他级别是概率（取决于查询节点追日志的时机）——这个实验的现象有时机性，
多跑几轮才作数。
"""
import time
from pathlib import Path

import numpy as np
from pymilvus import Collection, connections

LAB = Path(__file__).resolve().parent.parent
DATA = LAB / "data"

COLLECTION = "exp14"
BATCH = 100
ROUNDS = 10


def visible_count(col, ids):
    """立刻数这批 id 里可见几条，返回 (可见条数, 查询耗时 ms)。"""
    expr = "id in [" + ",".join(str(i) for i in ids) + "]"
    t0 = time.perf_counter()
    rows = col.query(expr=expr, output_fields=["id"])
    return len(rows), (time.perf_counter() - t0) * 1000


def main():
    connections.connect(host="localhost", port="19530")
    data = np.load(DATA / "exp14.npz")
    all_ids, all_vecs = data["ids"], data["vectors"]

    # 同一个 collection 的三个"一致性镜头"
    col_default = Collection(COLLECTION)                              # 服务端默认级别
    col_strong = Collection(COLLECTION, consistency_level="Strong")
    col_eventual = Collection(COLLECTION, consistency_level="Eventually")

    cursor = 0

    def take():
        nonlocal cursor
        ids = all_ids[cursor:cursor + BATCH]
        vecs = all_vecs[cursor:cursor + BATCH]
        cursor += BATCH
        return ids, vecs

    def round_once(col, label, verbose=True):
        ids, vecs = take()
        mr = col_default.insert([ids.tolist(), vecs.tolist()])
        n, ms = visible_count(col, ids)
        if verbose:
            print(f"[{label}] insert_count={mr.insert_count}"
                  f"  立刻可见 {n}/{BATCH}  查询耗时 {ms:.1f}ms")
        return n, ms

    print("== 第 1 步：默认一致性级别（insert 完立刻数）==")
    round_once(col_default, "默认")
    print("（单轮不作数，时机性现象，见文档）")

    print("== 第 2 步：Strong ==")
    round_once(col_strong, "Strong")

    print("== 第 3 步：Eventually ==")
    round_once(col_eventual, "Eventually")

    print("== 第 4 步：三种级别各 10 轮 ==")
    print(f"{'级别':<12}{'全见轮数':>8}{'平均可见':>10}{'平均查询耗时':>14}")
    for col, label in [(col_strong, "Strong"),
                       (col_default, "默认"),
                       (col_eventual, "Eventually")]:
        ns, mss = [], []
        for _ in range(ROUNDS):
            n, ms = round_once(col, label, verbose=False)
            ns.append(n)
            mss.append(ms)
        full = sum(1 for n in ns if n == BATCH)
        print(f"{label:<12}{full:>6}/10{np.mean(ns):>10.1f}{np.mean(mss):>12.1f}ms")

    print("\n下一步：python scripts/exp14-segment-demo.py（去 attu 看 growing segment）")


if __name__ == "__main__":
    main()
