# 实验 04「写入后为什么查不到」材料构建
# 建索引 exp04_orders（order_no: keyword, content: text），bulk 灌 1000 条订单
# 运行：python exp04-gen.py（先激活 lab/.venv，ES 在 http://localhost:9200）

import random

from elasticsearch import Elasticsearch, helpers

ES = Elasticsearch("http://localhost:9200")
INDEX = "exp04_orders"

# 三类正文，其中一类含"退款"，保证后面 match 查询有区分度
TEMPLATES = [
    "订单已支付，商品打包完毕，等待发货",
    "客户咨询物流进度，客服已回复",
    "客户申请退款，理由是商品与描述不符",
    "订单已签收，交易完成",
]


def gen_actions():
    for i in range(1, 1001):
        yield {
            "_index": INDEX,
            "_id": i,
            "_source": {
                "order_no": f"SO2026{i:06d}",
                "content": random.Random(i).choice(TEMPLATES),
            },
        }


def main():
    if ES.indices.exists(index=INDEX):
        ES.indices.delete(index=INDEX)
        print(f"已删除旧索引 {INDEX}")

    ES.indices.create(
        index=INDEX,
        mappings={
            "properties": {
                "order_no": {"type": "keyword"},
                "content": {"type": "text"},
            }
        },
    )
    print(f"已创建索引 {INDEX}")

    ok, _ = helpers.bulk(ES, gen_actions())
    print(f"bulk 写入 {ok} 条")

    ES.indices.refresh(index=INDEX)
    count = ES.count(index=INDEX)["count"]
    print(f"refresh 后 count = {count}")
    print("材料构建完成")


if __name__ == "__main__":
    main()
