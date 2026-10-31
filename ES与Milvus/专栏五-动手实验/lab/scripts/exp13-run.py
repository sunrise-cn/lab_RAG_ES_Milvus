"""实验 13 主测量：同一批向量，三把尺子，两两对答案。

所有查询都走 Strong 一致性级别的句柄：把"等水位"这个变量钉死，
只看度量方式的差异（那个变量归实验 14 管）。
"""
from pathlib import Path

import numpy as np
from pymilvus import Collection, connections

LAB = Path(__file__).resolve().parent.parent
DATA = LAB / "data"

TOPK = 10
METRICS = ["L2", "IP", "COSINE"]


def strong(name):
    return Collection(name, consistency_level="Strong")


def search_topk(col, metric, q, k):
    res = col.search(data=[q], anns_field="vector",
                     param={"metric_type": metric, "params": {}}, limit=k)
    hits = res[0]
    return list(hits.ids), list(hits.distances)


def main():
    connections.connect(host="localhost", port="19530")

    # ---- 第 1 步：2 维心算组，query = (1, 0) ----
    print("== 第 1 步：2 维心算组，query = (1, 0)，各搜 top-3 ==")
    for metric in METRICS:
        col = strong(f"exp13_2d_{metric.lower()}")
        ids, dists = search_topk(col, metric, [1.0, 0.0], 3)
        print(f"{metric:>6}: " + ", ".join(f"id={i} d={d:.4f}" for i, d in zip(ids, dists)))

    # ---- 第 2 步：128 维未归一化组 ----
    print("\n== 第 2 步：128 维未归一化组，10 条 query 的 top-10 ==")
    queries = np.load(DATA / "exp13.npz")["queries"]
    tops = {}
    for metric in METRICS:
        col = strong(f"exp13_128_{metric.lower()}")
        tops[metric] = [search_topk(col, metric, q.tolist(), TOPK) for q in queries]

    print("query#0 的三份 top-10：")
    for metric in METRICS:
        ids, dists = tops[metric][0]
        print(f"{metric:>6}  ids: {ids}")
        print(f"{'':>6}  dist: {[round(d, 3) for d in dists]}")
    for a, b in [("L2", "IP"), ("L2", "COSINE"), ("IP", "COSINE")]:
        overlap = np.mean([len(set(tops[a][i][0]) & set(tops[b][i][0]))
                           for i in range(len(queries))])
        print(f"top-10 平均重合：{a} vs {b} = {overlap:.1f} / 10")

    # ---- 第 3 步：归一化后，L2 和 COSINE 是不是同一把尺子 ----
    print("\n== 第 3 步：归一化后，同一 query 在 L2 / COSINE 下的 top-10 ==")
    q = queries[0]
    qn = (q / np.linalg.norm(q)).tolist()
    res = {}
    for metric in ["L2", "COSINE"]:
        col = strong(f"exp13_128n_{metric.lower()}")
        res[metric] = search_topk(col, metric, qn, TOPK)
        print(f"{metric:>6}  ids: {res[metric][0]}")
        print(f"{'':>6}  dist: {[round(d, 3) for d in res[metric][1]]}")
    if res["L2"][0] == res["COSINE"][0]:
        print("逐位对比：完全一致——归一化后 L2 和 COSINE 是同一把尺子")
    else:
        print("逐位对比：存在差异！（理论上不该出现，见文档坑点）")


if __name__ == "__main__":
    main()
