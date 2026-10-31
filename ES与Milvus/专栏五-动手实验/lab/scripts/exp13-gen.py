"""实验 13 材料：三把尺子（L2 / IP / COSINE）量同一批向量。

三组数据：
  1) 手造 2 维向量 5 条，可以心算，建 L2/IP/COSINE 三个 collection；
  2) 128 维随机向量 1000 条 + 10 条 query，模长特意拉开到 0.5~2.0——
     如果用纯高斯向量，128 维下模长全挤在 11.3 附近（卡方分布集中），
     三种度量的排序几乎重合，看不出差异；
  3) 第 2 组归一化后的版本，只建 L2/COSINE 两个 collection。
"""
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
N = 1000
NQ = 10

VECS_2D = [[1.0, 0.0], [2.0, 0.0], [3.0, 0.0], [0.0, 1.0], [1.0, 1.0]]   # id 1~5


def make_collection(name, dim, metric):
    if utility.has_collection(name):
        utility.drop_collection(name)
    schema = CollectionSchema([
        FieldSchema("id", DataType.INT64, is_primary=True),
        FieldSchema("vector", DataType.FLOAT_VECTOR, dim=dim),
    ])
    col = Collection(name, schema)
    col.create_index(field_name="vector", index_params={
        "index_type": "FLAT", "metric_type": metric, "params": {}})
    col.load()
    return col


def main():
    DATA.mkdir(exist_ok=True)
    connections.connect(host="localhost", port="19530")

    # ---- 第 1 组：2 维心算组 ----
    for metric in ["L2", "IP", "COSINE"]:
        col = make_collection(f"exp13_2d_{metric.lower()}", 2, metric)
        col.insert([list(range(1, 6)), VECS_2D])
        col.flush()
    print("2 维心算组就绪：exp13_2d_l2 / exp13_2d_ip / exp13_2d_cos")

    # ---- 第 2 组：128 维，模长特意拉开 ----
    rng = np.random.default_rng(1313)
    direction = rng.normal(size=(N, DIM))
    direction /= np.linalg.norm(direction, axis=1, keepdims=True)
    length = rng.uniform(0.5, 2.0, size=(N, 1))
    vectors = direction * length

    q_dir = rng.normal(size=(NQ, DIM))
    q_dir /= np.linalg.norm(q_dir, axis=1, keepdims=True)
    q_len = rng.uniform(0.5, 2.0, size=(NQ, 1))
    queries = q_dir * q_len

    for metric in ["L2", "IP", "COSINE"]:
        col = make_collection(f"exp13_128_{metric.lower()}", DIM, metric)
        col.insert([list(range(N)), vectors.tolist()])
        col.flush()
    print("128 维组就绪：exp13_128_l2 / exp13_128_ip / exp13_128_cos（未归一化）")

    # ---- 第 3 组：归一化后的同一批向量（模长全 1）----
    for metric in ["L2", "COSINE"]:
        col = make_collection(f"exp13_128n_{metric.lower()}", DIM, metric)
        col.insert([list(range(N)), direction.tolist()])
        col.flush()
    print("归一化组就绪：exp13_128n_l2 / exp13_128n_cos")

    np.savez(DATA / "exp13.npz", queries=queries)
    print(f"query 已存 {DATA / 'exp13.npz'}，下一步：python scripts/exp13-run.py")


if __name__ == "__main__":
    main()
