"""实验 16 材料：三个 collection 灌同一份带簇结构的向量，建三种索引。

exp16-flat: FLAT（暴力，ground truth 尺子）
exp16-sq8 : IVF_SQ8（nlist=100）
exp16-pq  : IVF_PQ（nlist=100, m=16, nbits=8）

数据和实验 12 是同一份（种子 1212、100 簇 x 1000 条、sigma 0.35），
所以实验 12 里 IVF_FLAT 的测量可以直接拿来当"无量化基线"。

注意：2.4 里量化不是独立索引类型，是 IVF 家族的变体（IVF_SQ8 / IVF_PQ）。

运行方式（先激活 venv）：
  cd lab && source .venv/Scripts/activate
  python scripts/exp16-gen.py
"""
import time
from pathlib import Path

import numpy as np
from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    connections,
    utility,
)

LAB = Path(__file__).resolve().parent.parent
DATA = LAB / "data"

DIM = 128
N_CLUSTERS = 100
PER_CLUSTER = 1000          # 100 簇 x 1000 条 = 10 万条
N_QUERIES = 100
NOISE = 0.35
BATCH = 5000

INDEXES = {
    "exp16-flat": {"index_type": "FLAT", "metric_type": "L2", "params": {}},
    "exp16-sq8": {"index_type": "IVF_SQ8", "metric_type": "L2",
                  "params": {"nlist": 100}},
    # IVF_PQ 参数名（m/nbits）以 pymilvus 2.4.4 实际为准——待验证
    "exp16-pq": {"index_type": "IVF_PQ", "metric_type": "L2",
                 "params": {"nlist": 100, "m": 16, "nbits": 8}},
}


def main():
    DATA.mkdir(exist_ok=True)
    connections.connect(host="localhost", port="19530")

    # ---- 以下生成逻辑与 exp12-gen.py 逐行相同（含种子），产出同一份数据 ----
    rng = np.random.default_rng(1212)
    centers = rng.uniform(-1.0, 1.0, size=(N_CLUSTERS, DIM))
    noise = rng.normal(0.0, NOISE, size=(N_CLUSTERS * PER_CLUSTER, DIM))
    vectors = np.repeat(centers, PER_CLUSTER, axis=0) + noise
    ids = np.arange(N_CLUSTERS * PER_CLUSTER, dtype=np.int64)
    q_center = rng.integers(0, N_CLUSTERS, size=N_QUERIES)
    queries = centers[q_center] + rng.normal(0.0, NOISE, size=(N_QUERIES, DIM))

    for name, index_params in INDEXES.items():
        if utility.has_collection(name):
            utility.drop_collection(name)
        schema = CollectionSchema([
            FieldSchema("id", DataType.INT64, is_primary=True),
            FieldSchema("vector", DataType.FLOAT_VECTOR, dim=DIM),
        ])
        col = Collection(name, schema)
        t0 = time.perf_counter()
        for i in range(0, len(ids), BATCH):
            col.insert([ids[i:i + BATCH].tolist(),
                        vectors[i:i + BATCH].tolist()])
            print(f"  {name} insert {min(i + BATCH, len(ids))}/{len(ids)}")
        col.flush()
        col.create_index(field_name="vector", index_params=index_params)
        col.load()
        print(f"{name}: {col.num_entities} 行，{index_params['index_type']} 索引，"
              f"已 load（灌数据+建索引 {time.perf_counter() - t0:.0f}s）")

    np.savez(DATA / "exp16.npz", queries=queries)
    print(f"query 已存 {DATA / 'exp16.npz'}")
    print("材料就绪。下一步：python scripts/exp16-run.py")


if __name__ == "__main__":
    main()
