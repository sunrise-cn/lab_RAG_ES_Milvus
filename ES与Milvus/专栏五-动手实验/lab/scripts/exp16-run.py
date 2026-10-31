"""实验 16 主测量：三种索引的 recall@10 + 平均延迟 + collection_id。

FLAT 是 ground truth 尺子，SQ8/PQ 的 recall 拿它对答案。
collection_id 打出来是给 MinIO 那一步用的：去 index_log 目录里对号。

运行方式（先激活 venv）：
  cd lab && source .venv/Scripts/activate
  python scripts/exp16-run.py
"""
import time
from pathlib import Path

import numpy as np
from pymilvus import Collection, connections

LAB = Path(__file__).resolve().parent.parent
DATA = LAB / "data"

TOPK = 10
WARMUP = 3

# nprobe=16 对齐实验 12 的 IVF_FLAT 扫描档：桶裁剪条件一致，recall 的差值才是纯量化失真
PLANS = [
    ("exp16-flat", "FLAT", {"metric_type": "L2", "params": {}}),
    ("exp16-sq8", "IVF_SQ8", {"metric_type": "L2", "params": {"nprobe": 16}}),
    ("exp16-pq", "IVF_PQ", {"metric_type": "L2", "params": {"nprobe": 16}}),
]


def run_batch(col, queries, search_params):
    for q in queries[:WARMUP]:
        col.search(data=[q.tolist()], anns_field="vector",
                   param=search_params, limit=TOPK)
    t0 = time.perf_counter()
    results = [col.search(data=[q.tolist()], anns_field="vector",
                          param=search_params, limit=TOPK) for q in queries]
    total = time.perf_counter() - t0
    return total / len(queries) * 1000, [list(hits.ids) for hits in results]


def recall(id_lists, truth):
    hit = sum(len(set(a) & set(b)) for a, b in zip(id_lists, truth))
    return hit / (len(truth) * TOPK)


def collection_id(col):
    """能拿到就拿（去 MinIO 对目录），拿不到不影响测量。"""
    try:
        return col.describe().get("collection_id", "未知")
    except Exception:
        return "未知（以实际为准）"


def main():
    connections.connect(host="localhost", port="19530")
    queries = np.load(DATA / "exp16.npz")["queries"]

    truth = None
    for name, index_type, search_params in PLANS:
        col = Collection(name)
        avg, id_lists = run_batch(col, queries, search_params)
        if truth is None:
            truth = id_lists
            r = 1.0                      # FLAT 拿自己对自己，定义就是 1
        else:
            r = recall(id_lists, truth)
        print(f"{name:<12} {index_type:<8} recall@10={r:.4f}  "
              f"avg={avg:.2f}ms  collection_id={collection_id(col)}")


if __name__ == "__main__":
    main()
