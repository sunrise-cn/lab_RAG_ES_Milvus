# 实验 09「深分页的墙」材料构建
# 建两个索引、各灌 30 万条（no: long + text），用于对比不同分片数下的深翻页代价：
#   exp09_one  —— 1 个主分片
#   exp09_five —— 5 个主分片
# 运行：python scripts/exp09-gen.py（先激活 lab/.venv，ES 在 http://localhost:9200）
# 预计耗时 1~2 分钟（30 万条 × 2 个索引），脚本幂等：重跑先删旧索引

import time

from elasticsearch import Elasticsearch, helpers

ES = Elasticsearch("http://localhost:9200")
TOTAL = 300_000

MAPPINGS = {
    "properties": {
        "no": {"type": "long"},
        "text": {"type": "text"},
    }
}


def gen_actions(index: str):
    # _id 显式给 no：路由公式 hash(_id) % 主分片数 会把 30 万条近似均匀地摊到各分片
    for i in range(TOTAL):
        yield {
            "_index": index,
            "_id": i,
            "_source": {"no": i, "text": f"第{i}号深分页实验记录"},
        }


def build(index: str, shards: int):
    if ES.indices.exists(index=index):
        ES.indices.delete(index=index)
        print(f"已删除旧索引 {index}")
    ES.indices.create(
        index=index,
        mappings=MAPPINGS,
        settings={"number_of_shards": shards, "number_of_replicas": 0},
    )
    print(f"已创建索引 {index}（{shards} 分片），开始写入 {TOTAL} 条")

    t0 = time.perf_counter()
    ok, _ = helpers.bulk(ES, gen_actions(index), chunk_size=2000)
    ES.indices.refresh(index=index)
    count = ES.count(index=index)["count"]
    print(f"bulk 写入 {ok} 条，refresh 后 count = {count}，"
          f"耗时 {time.perf_counter() - t0:.0f}s")


def main():
    build("exp09_one", 1)
    build("exp09_five", 5)
    print("材料构建完成")


if __name__ == "__main__":
    main()
