# exp01-seed.py —— 实验 01 材料：建 demo_index，插入 50 条商品文档
# 用法：在 lab 目录的 venv 激活后运行 python scripts/exp01-seed.py
# 前提：ES 已按 00-实验环境 起好（http://localhost:9200，单节点，认证关闭）
# 脚本幂等：重复跑会先删掉旧 demo_index 再重建

import random

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

ES_URL = "http://localhost:9200"
INDEX = "demo_index"

MAPPINGS = {
    "properties": {
        "id":         {"type": "long"},
        "title":      {"type": "text"},
        "content":    {"type": "text"},
        "category":   {"type": "keyword"},
        "price":      {"type": "float"},
        "created_at": {"type": "date", "format": "yyyy-MM-dd"},
    }
}
SETTINGS = {"number_of_shards": 1, "number_of_replicas": 0}

# 手写的 12 条：给 GET / _mget / _explain 演示用，内容固定、有辨识度
HAND_MADE = [
    (1001, "旗舰智能手机 Pro Max",
     "旗舰手机，支持快充与无线充电。用户咨询充电发烫是否正常，能否申请退款。",
     "手机", 6999.00, "2026-10-20"),
    (1002, "主动降噪蓝牙耳机",
     "无线蓝牙耳机，主动降噪，续航 30 小时。降噪开启后有轻微底噪属正常现象。",
     "耳机", 1299.00, "2026-10-21"),
    (1003, "折叠屏手机",
     "折叠屏手机，铰链保修三年。屏幕出现亮线可申请维修换屏。",
     "手机", 8999.00, "2026-10-21"),
    (1004, "高透钢化膜",
     "钢化膜，贴膜失败支持补发。不支持退款，仅支持换货。",
     "配件", 19.90, "2026-10-22"),
    (1005, "轻薄笔记本",
     "14 英寸轻薄笔记本，续航 12 小时。预装系统不支持退货，硬件故障保修两年。",
     "电脑", 5499.00, "2026-10-22"),
    (1006, "变频空调",
     "一级能效变频空调，整机保修六年。安装后不支持七天无理由退款。",
     "家电", 3299.00, "2026-10-23"),
    (1007, "运动智能手表",
     "运动智能手表，防水 50 米。表带过敏可申请退款。",
     "穿戴", 1599.00, "2026-10-23"),
    (1008, "有线入耳式耳机",
     "监听级有线耳机，3.5mm 接口。线材断裂一年内免费维修。",
     "耳机", 399.00, "2026-10-24"),
    (1009, "游戏笔记本",
     "高性能游戏笔记本，显卡满载时风扇噪音较大属正常。",
     "电脑", 9999.00, "2026-10-24"),
    (1010, "激光导航扫地机器人",
     "扫地机器人，主机保修两年，耗材配件需另行购买。",
     "家电", 2199.00, "2026-10-25"),
    (1011, "磨砂手机保护壳",
     "手机保护壳，摔损不在保修范围，可申请折价换新。",
     "配件", 49.00, "2026-10-25"),
    (1012, "平板电脑",
     "11 英寸平板，支持手写笔。屏幕坏点三个以内符合出厂标准，超出可退换。",
     "电脑", 3999.00, "2026-10-26"),
]


def build_docs():
    docs = []
    for doc_id, title, content, category, price, created in HAND_MADE:
        docs.append({"id": doc_id, "title": title, "content": content,
                     "category": category, "price": price, "created_at": created})
    # 再程序生成 38 条，凑满 50 条（固定种子，可复现）
    rng = random.Random(42)
    names = ["手机", "耳机", "电脑", "家电", "配件", "穿戴"]
    for i in range(38):
        doc_id = 1013 + i
        name = names[i % len(names)]
        docs.append({
            "id": doc_id,
            "title": f"{name}产品 {doc_id} 型",
            "content": f"{name}类目的常规商品 {doc_id}，支持七天无理由退款，一年保修。",
            "category": name,
            "price": round(rng.uniform(20, 3000), 2),
            "created_at": f"2026-10-{27 + (i % 3):02d}",
        })
    return docs


def main():
    es = Elasticsearch(ES_URL)
    if not es.ping():
        raise SystemExit("连不上 ES，先确认环境起来了：docker compose ps（在 lab 目录下执行）")

    es.indices.delete(index=INDEX, ignore=[400, 404])
    es.indices.create(index=INDEX, mappings=MAPPINGS, settings=SETTINGS)

    actions = ({"_index": INDEX, "_id": str(d["id"]), "_source": d} for d in build_docs())
    success, errors = bulk(es, actions)
    es.indices.refresh(index=INDEX)

    count = es.count(index=INDEX)["count"]
    print(f"demo_index 就绪：写入 {success} 条，可搜索 {count} 条")
    print("常用演示文档：1001（手机/退款） 1002（耳机/降噪） 1003（手机/维修）")


if __name__ == "__main__":
    main()
