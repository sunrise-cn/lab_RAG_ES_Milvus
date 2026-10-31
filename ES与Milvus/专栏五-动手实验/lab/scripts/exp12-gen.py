"""实验 12 材料：10 万条带簇结构的 128 维向量 + 100 条 query。

为什么不用纯随机：真实 embedding 是聚团的（语义相近的文本挤在一起），
纯均匀随机数据下 ANN 索引的表现会失真偏乐观。这里造一个"聚团"的世界：
100 个簇心均匀撒在 [-1,1]^128 里，每条向量 = 自己的簇心 + 高斯噪声（sigma=0.35）。
sigma 是挑过的：太小（比如 0.1）簇太干净，IVF nprobe=1 都能接近满分召回，
曲线失去动态范围；太大（0.5 以上）簇糊成一片，退化回均匀云。
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

COLLECTION = "exp12"
DIM = 128
N_CLUSTERS = 100
PER_CLUSTER = 1000          # 100 簇 x 1000 条 = 10 万条
N_QUERIES = 100
NOISE = 0.35
BATCH = 5000


def main():
    DATA.mkdir(exist_ok=True)
    connections.connect(host="localhost", port="19530")

    rng = np.random.default_rng(1212)

    # 100 个簇心，均匀撒在 [-1, 1]^128
    centers = rng.uniform(-1.0, 1.0, size=(N_CLUSTERS, DIM))
    # 每条向量 = 自己的簇心 + 高斯噪声；id 恰好等于 簇号*1000 + 簇内序号
    noise = rng.normal(0.0, NOISE, size=(N_CLUSTERS * PER_CLUSTER, DIM))
    vectors = np.repeat(centers, PER_CLUSTER, axis=0) + noise
    ids = np.arange(N_CLUSTERS * PER_CLUSTER, dtype=np.int64)

    # query 从簇心加噪声采样：和库内向量同分布，但独立加噪
    q_center = rng.integers(0, N_CLUSTERS, size=N_QUERIES)
    queries = centers[q_center] + rng.normal(0.0, NOISE, size=(N_QUERIES, DIM))

    if utility.has_collection(COLLECTION):
        utility.drop_collection(COLLECTION)

    schema = CollectionSchema([
        FieldSchema("id", DataType.INT64, is_primary=True),
        FieldSchema("vector", DataType.FLOAT_VECTOR, dim=DIM),
    ])
    col = Collection(COLLECTION, schema)

    t0 = time.perf_counter()
    for i in range(0, len(ids), BATCH):
        col.insert([ids[i:i + BATCH].tolist(), vectors[i:i + BATCH].tolist()])
        print(f"insert {min(i + BATCH, len(ids))}/{len(ids)}")
    col.flush()
    print(f"insert+flush 耗时 {time.perf_counter() - t0:.1f}s，num_entities={col.num_entities}")

    np.savez(DATA / "exp12.npz", queries=queries)
    print(f"query 已存 {DATA / 'exp12.npz'}")
    print("材料就绪。下一步：python scripts/exp12-run.py")


if __name__ == "__main__":
    main()
