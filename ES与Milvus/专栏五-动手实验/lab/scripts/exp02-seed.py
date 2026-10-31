# exp02-seed.py —— 实验 02 材料：建 exp02_index，bulk 写 1000 条小文档，force merge 成 1 个段
# 用法：在 lab 目录的 venv 激活后运行 python scripts/exp02-seed.py
# 为什么 force merge：一次 bulk 写完会产生多个小段，合并成 1 个段后，
# 磁盘分片目录里的段文件最干净，逐个数文件最方便

import random

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

ES_URL = "http://localhost:9200"
INDEX = "exp02_index"
N = 1000


def main():
    es = Elasticsearch(ES_URL)
    if not es.ping():
        raise SystemExit("连不上 ES，先确认环境起来了：docker compose ps（在 lab 目录下执行）")

    es.indices.delete(index=INDEX, ignore=[400, 404])
    es.indices.create(
        index=INDEX,
        mappings={
            "properties": {
                "no":       {"type": "integer"},
                "title":    {"type": "text"},
                "category": {"type": "keyword"},
                "price":    {"type": "float"},
            }
        },
        settings={"number_of_shards": 1, "number_of_replicas": 0},
    )

    rng = random.Random(7)
    names = ["手机", "耳机", "电脑", "家电", "配件", "穿戴"]
    actions = [
        {
            "_index": INDEX,
            "_id": i,
            "_source": {
                "no": i,
                "title": f"商品编号{i:04d}",
                "category": names[i % len(names)],
                "price": round(rng.uniform(10, 2000), 2),
            },
        }
        for i in range(1, N + 1)
    ]
    success, errors = bulk(es, actions)
    es.indices.refresh(index=INDEX)

    # force merge：把所有段合并成 1 个（1000 条小文档，很快）
    es.indices.forcemerge(index=INDEX, max_num_segments=1)

    count = es.count(index=INDEX)["count"]
    print(f"exp02_index 就绪：写入 {success} 条，可搜索 {count} 条")
    print("下一步：GET /_cat/segments/exp02_index?v 验证只剩 1 个段，再去磁盘看文件")


if __name__ == "__main__":
    main()
