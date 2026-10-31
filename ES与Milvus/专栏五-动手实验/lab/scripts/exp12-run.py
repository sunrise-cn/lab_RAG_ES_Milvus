"""实验 12 主测量：FLAT 标尺 -> HNSW 扫 ef -> IVF_FLAT 扫 nprobe。

产物：lab/data/exp12-results.json（给 exp12-plot.py 画图）。
注意：这个脚本会把 exp12 的索引反复拆掉重建；重跑前建议先重跑 exp12-gen.py。
"""
import json
import time
from pathlib import Path

import numpy as np
from pymilvus import Collection, connections

LAB = Path(__file__).resolve().parent.parent
DATA = LAB / "data"

COLLECTION = "exp12"
TOPK = 10
WARMUP = 3

FLAT = {"index_type": "FLAT", "metric_type": "L2", "params": {}}
HNSW = {"index_type": "HNSW", "metric_type": "L2",
        "params": {"M": 16, "efConstruction": 200}}
IVF = {"index_type": "IVF_FLAT", "metric_type": "L2", "params": {"nlist": 100}}


def rebuild(col, index_params):
    """幂等地把索引换成 index_params，返回建索引耗时（秒）。"""
    try:
        col.release()          # 没 load 过就 release 会报错，吞掉
    except Exception:
        pass
    if col.has_index:
        col.drop_index()
    t0 = time.perf_counter()
    col.create_index(field_name="vector", index_params=index_params)
    build = time.perf_counter() - t0
    col.load()
    return build


def run_batch(col, queries, search_params):
    """逐条搜完全部 query，返回 (总耗时s, 平均单查ms, 每条命中的 id 列表)。"""
    for q in queries[:WARMUP]:                     # 热身 3 条，不计入
        col.search(data=[q.tolist()], anns_field="vector",
                   param=search_params, limit=TOPK)
    t0 = time.perf_counter()
    results = [col.search(data=[q.tolist()], anns_field="vector",
                          param=search_params, limit=TOPK) for q in queries]
    total = time.perf_counter() - t0
    id_lists = [list(hits.ids) for hits in results]
    return total, total / len(queries) * 1000, id_lists


def recall(id_lists, truth):
    hit = sum(len(set(a) & set(b)) for a, b in zip(id_lists, truth))
    return hit / (len(truth) * TOPK)


def main():
    connections.connect(host="localhost", port="19530")
    queries = np.load(DATA / "exp12.npz")["queries"]
    col = Collection(COLLECTION)
    results = {}

    # ---- 阶段 A：FLAT，暴力标尺，顺便产出 ground truth ----
    build = rebuild(col, FLAT)
    print(f"[A] FLAT 索引就绪（build {build:.1f}s）")
    total, avg, truth = run_batch(col, queries, {"metric_type": "L2", "params": {}})
    qps = len(queries) / total
    print(f"[A] 100 条 query：总耗时 {total:.2f}s，平均 {avg:.1f}ms/条，QPS {qps:.0f}")
    print(f"[A] recall@10 = {recall(truth, truth):.4f}（拿 FLAT 对 FLAT，定义就是 1）")
    results["flat"] = {"recall": 1.0, "qps": qps, "avg_ms": avg}

    # ---- 阶段 B：HNSW，扫 ef ----
    build = rebuild(col, HNSW)
    print(f"[B] HNSW 索引就绪（build {build:.1f}s，比 FLAT 慢一个量级）")
    results["hnsw"] = {}
    for ef in [8, 16, 32, 64, 128]:
        total, avg, id_lists = run_batch(
            col, queries, {"metric_type": "L2", "params": {"ef": ef}})
        r = recall(id_lists, truth)
        results["hnsw"][ef] = {"recall": r, "qps": len(queries) / total, "avg_ms": avg}
        print(f"[B] ef={ef:<3} recall@10={r:.4f}  avg={avg:.2f}ms  QPS={len(queries) / total:.0f}")

    # ---- 阶段 C：IVF_FLAT，扫 nprobe ----
    build = rebuild(col, IVF)
    print(f"[C] IVF_FLAT 索引就绪（build {build:.1f}s，含 k-means 训练；nlist=100 对应 100 个簇）")
    results["ivf"] = {}
    for nprobe in [1, 4, 16, 64]:
        total, avg, id_lists = run_batch(
            col, queries, {"metric_type": "L2", "params": {"nprobe": nprobe}})
        r = recall(id_lists, truth)
        results["ivf"][nprobe] = {"recall": r, "qps": len(queries) / total, "avg_ms": avg}
        print(f"[C] nprobe={nprobe:<2} recall@10={r:.4f}  avg={avg:.2f}ms  QPS={len(queries) / total:.0f}")

    with open(DATA / "exp12-results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"结果已存 {DATA / 'exp12-results.json'}，下一步：python scripts/exp12-plot.py")


if __name__ == "__main__":
    main()
