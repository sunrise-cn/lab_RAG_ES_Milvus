"""实验 14 材料：collection exp14 + 3500 条已知 id 的 128 维向量。

注意顺序：先建索引并 load，再让 run 去 insert。查询节点只对"已 load 的
collection"订阅增量流（growing segment），顺序反了看到的世界就不一样了。
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

COLLECTION = "exp14"
DIM = 128
N_ROWS = 3500      # 主实验用 3400（34 批 x 100），留 100 给 attu 环节


def main():
    DATA.mkdir(exist_ok=True)
    connections.connect(host="localhost", port="19530")

    rng = np.random.default_rng(1414)
    ids = np.arange(N_ROWS, dtype=np.int64)
    vectors = rng.normal(0.0, 1.0, size=(N_ROWS, DIM))

    if utility.has_collection(COLLECTION):
        utility.drop_collection(COLLECTION)
    schema = CollectionSchema([
        FieldSchema("id", DataType.INT64, is_primary=True),
        FieldSchema("vector", DataType.FLOAT_VECTOR, dim=DIM),
    ])
    col = Collection(COLLECTION, schema)
    col.create_index(field_name="vector", index_params={
        "index_type": "FLAT", "metric_type": "L2", "params": {}})
    col.load()

    np.savez(DATA / "exp14.npz", ids=ids, vectors=vectors)
    print(f"collection {COLLECTION} 已建好（FLAT 索引，已 load）")
    print(f"3500 条备弹已存 {DATA / 'exp14.npz'}")
    print("下一步：python scripts/exp14-run.py")


if __name__ == "__main__":
    main()
