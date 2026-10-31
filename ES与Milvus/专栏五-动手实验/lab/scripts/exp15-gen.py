"""实验 15 材料：同一份数据、两种 schema 的两个 collection。

exp15-pk   : category 建为 partition key（is_partition_key=True）
exp15-plain: category 是普通标量字段
两份数据逐行相同（同一个 rng 生成、同一批 insert），schema 里唯一差别是
is_partition_key 一个参数——步骤 3 的延迟对比里只有"分区裁剪"这一个变量。

数据：20 万条 128 维随机向量，10 个 category——cat_0~cat_8 各 22200 条，
cat_rare 200 条（选择率 0.1%，步骤 2 的靶子）。
向量用均匀随机：本实验量的是过滤行为不是 ANN 召回，分布不影响结论。

运行方式（先激活 venv）：
  cd lab && source .venv/Scripts/activate
  python scripts/exp15-gen.py
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
N_ROWS = 200_000
COMMON_EACH = 22_200          # 9 个常见值 x 22200 + cat_rare 200 = 200000
RARE = "cat_rare"
N_QUERIES = 50
BATCH = 5000
HNSW = {"index_type": "HNSW", "metric_type": "L2",
        "params": {"M": 16, "efConstruction": 200}}


def main():
    DATA.mkdir(exist_ok=True)
    connections.connect(host="localhost", port="19530")

    rng = np.random.default_rng(1515)
    vectors = rng.uniform(-1.0, 1.0, size=(N_ROWS, DIM))
    ids = np.arange(N_ROWS, dtype=np.int64)
    categories = np.array(
        [f"cat_{i}" for i in range(9) for _ in range(COMMON_EACH)] + [RARE] * 200)
    perm = rng.permutation(N_ROWS)          # 打乱：让 10 个值交错分布
    vectors, ids, categories = vectors[perm], ids[perm], categories[perm]

    for name, is_pk in [("exp15-pk", True), ("exp15-plain", False)]:
        if utility.has_collection(name):
            utility.drop_collection(name)
        schema = CollectionSchema([
            FieldSchema("id", DataType.INT64, is_primary=True),
            FieldSchema("vector", DataType.FLOAT_VECTOR, dim=DIM),
            # partition key：写入按 hash(category) 自动路由分区，等值过滤自动裁剪。
            # 分区数用服务端默认（2.4 的默认值待验证），不显式指定。
            FieldSchema("category", DataType.VARCHAR, max_length=32,
                        is_partition_key=is_pk),
        ])
        col = Collection(name, schema)
        t0 = time.perf_counter()
        for i in range(0, N_ROWS, BATCH):
            col.insert([ids[i:i + BATCH].tolist(),
                        vectors[i:i + BATCH].tolist(),
                        categories[i:i + BATCH].tolist()])
            if (i // BATCH) % 4 == 0:
                print(f"  {name} insert {min(i + BATCH, N_ROWS)}/{N_ROWS}")
        col.flush()
        col.create_index(field_name="vector", index_params=HNSW)
        col.load()
        print(f"{name}: {col.num_entities} 行，HNSW 索引，已 load"
              f"（灌数据 {time.perf_counter() - t0:.0f}s）")
        if is_pk:
            for p in col.partitions:
                print(f"  partition {p.name}: {p.num_entities} 行")

    queries = rng.uniform(-1.0, 1.0, size=(N_QUERIES, DIM))
    np.savez(DATA / "exp15.npz", queries=queries)
    print(f"query 已存 {DATA / 'exp15.npz'}")
    print("材料就绪。下一步：python scripts/exp15-run.py")


if __name__ == "__main__":
    main()
