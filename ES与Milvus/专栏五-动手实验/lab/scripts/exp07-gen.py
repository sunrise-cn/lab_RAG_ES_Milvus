# 实验 07「segment 的生死」材料构建
# 建索引 exp07_docs（id: integer, content: text），
# 分 20 批 bulk，每批 500 条，每批之间 flush 一次，逼出 20+ 个 segment
# 运行：python exp07-gen.py

from elasticsearch import Elasticsearch, helpers

ES = Elasticsearch("http://localhost:9200")
INDEX = "exp07_docs"

BATCHES = 20
BATCH_SIZE = 500

# 进一步实验用：改成 "30s" 再跑一遍，对比段数（段数变少、单段更大）
REFRESH_INTERVAL = "1s"


def gen_batch(batch_no):
    start = batch_no * BATCH_SIZE + 1
    for i in range(start, start + BATCH_SIZE):
        yield {
            "_index": INDEX,
            "_id": i,
            "_source": {
                "id": i,
                "content": f"文档{i}的正文，包含关键词keyword{i % 10}",
            },
        }


def main():
    if ES.indices.exists(index=INDEX):
        ES.indices.delete(index=INDEX)
        print(f"已删除旧索引 {INDEX}")

    ES.indices.create(
        index=INDEX,
        settings={"index": {"refresh_interval": REFRESH_INTERVAL}},
        mappings={
            "properties": {
                "id": {"type": "integer"},
                "content": {"type": "text"},
            }
        },
    )
    print(f"已创建索引 {INDEX}，开始 {BATCHES} 批写入（每批 {BATCH_SIZE} 条，批间 flush）")

    for batch_no in range(BATCHES):
        ok, _ = helpers.bulk(ES, gen_batch(batch_no))
        # 每批 flush 一次，把这批的数据固化成磁盘上的 segment
        ES.indices.flush(index=INDEX)
        print(f"  批 {batch_no + 1:02d}/{BATCHES}：写入 {ok} 条，flush 完成")

    ES.indices.refresh(index=INDEX)
    stats = ES.indices.stats(index=INDEX)
    primaries = stats["_all"]["primaries"]
    print(f"count = {primaries['docs']['count']}")
    print("材料构建完成")


if __name__ == "__main__":
    main()
