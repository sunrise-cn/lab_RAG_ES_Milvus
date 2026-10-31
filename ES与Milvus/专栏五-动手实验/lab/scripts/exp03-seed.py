# exp03-seed.py —— 实验 03 材料：显式 schema 建 collection，插 100 条随机向量，
# 建 HNSW 索引，load，然后跑一遍 search / query / get
# 用法：在 lab 目录的 venv 激活后运行 python scripts/exp03-seed.py
# 前提：Milvus 已按 00-实验环境 起好（http://localhost:19530）
#
# 逐 API 对照（详情见实验文档 03）：
#   connections.connect          连服务（对应 JDBC 建连）
#   utility.has_collection       collection 是否存在（对应 SHOW TABLES 判断）
#   utility.drop_collection      删 collection（幂等重跑用）
#   FieldSchema/CollectionSchema/Collection  显式建表（对应 DDL）
#   insert                       写入（对应 INSERT）
#   flush                        把内存中攒的数据封成 segment 落到对象存储
#   create_index                 建 ANN 索引
#   load                         把数据加载进内存（不 load 不能搜）
#   search                       向量检索
#   query                        标量过滤查询（不碰向量，对应 WHERE）
#   get                          按主键取（对应 SELECT ... WHERE id IN）
#   num_entities                 行数（对应 COUNT(*)）

import numpy as np
from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    connections,
    utility,
)

COLLECTION = "exp03_person"
DIM = 128
CITIES = ["北京", "上海", "杭州", "深圳"]


def main():
    # 1. 连接：alias="default" 是这条全局连接的名字
    connections.connect(alias="default", host="localhost", port="19530")

    # 2. 幂等：同名 collection 先删，保证脚本可重复跑
    if utility.has_collection(COLLECTION):
        utility.drop_collection(COLLECTION)

    # 3. 显式 schema：id 主键 + embedding 向量 + city 标量字段
    schema = CollectionSchema(
        fields=[
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=DIM),
            FieldSchema(name="city", dtype=DataType.VARCHAR, max_length=64),
        ],
        description="实验03 演示 collection",
    )
    col = Collection(name=COLLECTION, schema=schema)

    # 4. 造 100 条随机向量（固定种子，可复现；[0,1) 均匀分布）
    rng = np.random.default_rng(42)
    vectors = rng.random((100, DIM)).astype(np.float32)

    # 5. 插入：行式写法，一行一条记录，像 INSERT VALUES
    rows = [
        {"id": i, "embedding": vectors[i].tolist(), "city": CITIES[i % len(CITIES)]}
        for i in range(100)
    ]
    ins = col.insert(rows)
    print(f"insert: insert_count={ins.insert_count}, "
          f"primary_keys 前 5 个: {list(ins.primary_keys[:5])}")

    # 6. flush：把攒在内存里的数据封成 segment 写到对象存储
    col.flush()
    print(f"flush 完成，num_entities={col.num_entities}")

    # 7. 建 HNSW 索引（L2 度量），建完 load 进内存——不 load 搜不了
    col.create_index(
        field_name="embedding",
        index_params={
            "index_type": "HNSW",
            "metric_type": "L2",
            "params": {"M": 16, "efConstruction": 200},
        },
    )
    col.load()

    # 8. 向量搜索：拿第 0 条向量搜它自己，top1 的 distance 应该是 0
    res = col.search(
        data=[vectors[0].tolist()],
        anns_field="embedding",
        param={"metric_type": "L2", "params": {"ef": 64}},
        limit=5,
        output_fields=["city"],
    )
    for hits in res:
        for hit in hits:
            print(f"search hit: id={hit.id}, distance={hit.distance:.4f}, "
                  f"city={hit.entity.get('city')}")

    # 9. 标量查询：不用向量，按字段过滤（city == '北京'）
    q = col.query(expr="city == '北京'", output_fields=["id", "city"], limit=5)
    print(f"query \"city == '北京'\" 前 5 条: {q}")

    # 10. 按主键取（等价于 WHERE id IN (1,2,3)）
    g = col.get(ids=[1, 2, 3], output_fields=["city"])
    print(f"get ids=[1,2,3]: {g}")

    # 11. 把查询向量打出来，复制到 attu 的 Vector Search 页面里用
    print(f"查询向量（粘到 attu 用）: {vectors[0].tolist()}")


if __name__ == "__main__":
    main()
