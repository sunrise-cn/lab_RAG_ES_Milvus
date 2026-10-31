"""实验 15 主测量：filter 的执行时机 + partition key 裁剪。

A. 无 filter 搜索：top-5 每次都满额（基准线）
B. 低选择率 filter（cat_rare，约 0.1%）：query() 拿得到全部 200 条，
   search() 却返回不满 5 条、跨 query 条数不稳定——"filter 织进 ANN 遍历"的现场
C. partition key 裁剪：cat_3（约 11%）等值过滤，plain vs pk 各 50 轮取均值

运行方式（先激活 venv）：
  cd lab && source .venv/Scripts/activate
  python scripts/exp15-run.py
"""
import time
from pathlib import Path

import numpy as np
from pymilvus import Collection, connections

LAB = Path(__file__).resolve().parent.parent
DATA = LAB / "data"

PLAIN = "exp15-plain"
PK = "exp15-pk"
RARE = "cat_rare"
COMMON = "cat_3"
TOPK = 5
N_B = 10          # B：10 个不同 query 各搜一次
N_C = 50          # C：正式测量轮数
WARMUP = 5

# ef 不显式传，用默认（默认值多大待验证——B 段的"预算"就是它）
PARAM = {"metric_type": "L2", "params": {}}


def search(col, vec, expr):
    return col.search(data=[vec.tolist()], anns_field="vector",
                      param=PARAM, limit=TOPK, expr=expr)


def main():
    connections.connect(host="localhost", port="19530")
    queries = np.load(DATA / "exp15.npz")["queries"]
    plain, pk = Collection(PLAIN), Collection(PK)

    # ---- A. 基准：无 filter，top-5 满额 ----
    counts = [len(search(plain, q, "")) for q in queries]
    print(f"[A] 无 filter 搜 {len(queries)} 次，"
          f"返回条数 min={min(counts)} max={max(counts)}")

    # ---- B. 低选择率 filter：数据在库里，search 给不满 ----
    rare_expr = f'category == "{RARE}"'
    rows = plain.query(expr=rare_expr, output_fields=["id"])
    print(f"[B] 库内满足 {rare_expr} 的行数：{len(rows)}"
          f"（选择率 {len(rows) / plain.num_entities:.2%}）")
    per_query = [len(search(plain, q, rare_expr)) for q in queries[:N_B]]
    same_q = [len(search(plain, queries[0], rare_expr)) for _ in range(3)]
    print(f"[B] {N_B} 个不同 query 各搜一次，返回条数：{per_query}")
    print(f"[B] 同一个 query 连搜 3 次，返回条数：{same_q}")

    # ---- C. partition key 裁剪：同过滤，plain vs pk，多轮取均值 ----
    common_expr = f'category == "{COMMON}"'
    vec = queries[0]
    for name, col in [(PLAIN, plain), (PK, pk)]:
        for _ in range(WARMUP):
            search(col, vec, common_expr)
        ts = []
        for _ in range(N_C):
            t0 = time.perf_counter()
            hits = search(col, vec, common_expr)
            ts.append((time.perf_counter() - t0) * 1000)
        ts.sort()
        mean = sum(ts) / len(ts)
        print(f"[C] {name:<12} {common_expr}：均值 {mean:.2f}ms  "
              f"最小 {ts[0]:.2f}ms  中位 {ts[len(ts) // 2]:.2f}ms  "
              f"返回 {len(hits)} 条")


if __name__ == "__main__":
    main()
