# 01 第一次见 ES：REST API 全景

新接手一个用 ES 的项目，你最先撞上的往往不是概念，是一坨 JSON：同事甩给你一条 curl，返回值里 `_shards`、`hits.total`、`_score`、`_version` 挤在一起，哪个是健康、哪个是结果、哪个能不管？这一篇就把这坨 JSON 拆成词典。跑完这一篇，你要拿到两样东西：一张 ES 的 API 地图（哪类活找哪个接口），一本响应字段词典（每个字段什么意思、单节点上它应该是几）。

## 这个实验验证什么

把 ES 的核心 API 家族挨个跑通——集群体检（`_cat`/`_cluster`）、索引管理、文档 CRUD（含 `_mget`/`_bulk`）、查询分析（`_search`/`_count`/`_analyze`/`_explain`）——并搞懂每个响应字段是什么意思。热身实验，不求深，求全。

关联正文：[专栏一·02](../专栏一-ES实战/02-核心概念与上手.md)（REST CRUD 与五个概念）、[专栏一·03](../专栏一-ES实战/03-检索DSL查询写不对一切白搭.md)（match/term/bool）、[专栏一·07](../专栏一-ES实战/07-Java客户端集成.md)（bulk 的 ndjson）、[专栏三·02](../专栏三-运行机制/02-写入路径与近实时.md)（_version 与写入路径）。

## 实验材料构建

前提：环境按 [00-实验环境](00-实验环境.md)起好，并激活 venv（`source .venv/Scripts/activate`）。所有命令在 `lab` 目录下执行，curl 在 Git Bash 里跑（PowerShell 的引号转义是另一个坑，后面坑点里说）。

材料脚本 [lab/scripts/exp01-seed.py](lab/scripts/exp01-seed.py)：显式建 `demo_index`（1 主分片、0 副本、手写 mapping），插入 50 条商品文档，字段有 id、title、content、category、price、created_at：

```python
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
```

跑它：

```bash
python scripts/exp01-seed.py
```

预期你会看到：

```text
demo_index 就绪：写入 50 条，可搜索 50 条
常用演示文档：1001（手机/退款） 1002（耳机/降噪） 1003（手机/维修）
```

一个约定：下面所有"预期你会看到"都是按机制推的**示意**——具体数字（took、分数、uuid）每台机器都不同，对不上别慌，重点是看懂**结构**。

## 实验步骤

### 第一组：集群体检（5 条）

**1. 集群整体健康：**

```bash
curl -s "http://localhost:9200/_cluster/health"
```

预期你会看到（示意，节选）：

```json
{
  "cluster_name" : "es-lab",
  "status" : "green",
  "timed_out" : false,
  "number_of_nodes" : 1,
  "active_primary_shards" : 2,
  "active_shards" : 2,
  "unassigned_shards" : 0,
  "active_shards_percent_as_number" : 100.0
}
```

`active_primary_shards` 是 2 不是 1：demo_index 一个，系统索引（如 `.geoip_databases`）一个，以你的实际输出为准。

**2. 索引列表：**

```bash
curl -s "http://localhost:9200/_cat/indices?v"
```

预期你会看到（示意，节选）：

```text
health status index            uuid                     pri rep docs.count docs.deleted store.size pri.store.size
green  open   .geoip_databases XyZaBcDeFgHiJkLmNoPqRs   1   0         42            0     40.4mb     40.4mb
green  open   demo_index        AbCdEfGhIjKlMnOpQrStUv   1   0         50            0     15.2kb     15.2kb
```

**3. 分片列表：**

```bash
curl -s "http://localhost:9200/_cat/shards?v"
```

预期你会看到（示意，节选）：

```text
index            shard prirep state   docs store   ip        node
.geoip_databases 0     p      STARTED   42  40.4mb 172.18.0.2 es01
demo_index       0     p      STARTED   50  15.2kb 172.18.0.2 es01
```

**4. 段列表（现在看不懂没关系，实验 02 的主角）：**

```bash
curl -s "http://localhost:9200/_cat/segments?v"
```

预期你会看到（示意，节选）：

```text
index      shard prirep ip        segment generation docs.count docs.deleted  size size.memory committed searchable version compound
demo_index 0     p      172.18.0.2 _0               0         50            0   15kb    122.0kb true       true       9.8.0  true
```

**5. 节点列表：**

```bash
curl -s "http://localhost:9200/_cat/nodes?v"
```

预期你会看到（示意，节选）：

```text
ip        heap.percent ram.percent cpu load_1m load_5m load_15m node.role master name
172.18.0.2           27          78   3    0.36    0.42     0.55 cdfhilmrstw      *      es01
```

### 第二组：索引管理

demo_index 正在被查询用，这组拿 `demo_index2` 当演习对象，演完删掉。

**1. 先看现成索引的结构（mapping + settings）：**

```bash
curl -s "http://localhost:9200/demo_index"
```

预期你会看到（示意，节选）：

```json
{
  "demo_index" : {
    "aliases" : { },
    "mappings" : {
      "properties" : {
        "category"   : { "type" : "keyword" },
        "content"    : { "type" : "text" },
        "price"      : { "type" : "float" },
        "title"      : { "type" : "text" }
      }
    },
    "settings" : {
      "index" : {
        "provided_name" : "demo_index",
        "number_of_shards" : "1",
        "number_of_replicas" : "0",
        "uuid" : "AbCdEfGhIjKlMnOpQrStUv",
        "creation_date" : "1769500000000"
      }
    }
  }
}
```

**2. 显式建索引（相当于 CREATE TABLE，带 DDL）：**

```bash
curl -s -X PUT "http://localhost:9200/demo_index2" -H "Content-Type: application/json" -d '
{
  "settings": { "number_of_shards": 1, "number_of_replicas": 0 },
  "mappings": {
    "properties": {
      "title":    { "type": "text" },
      "category": { "type": "keyword" }
    }
  }
}'
```

预期你会看到：

```json
{ "acknowledged" : true, "shards_acknowledged" : true, "index" : "demo_index2" }
```

**3. 试试建一个已经存在的索引：**

```bash
curl -s -X PUT "http://localhost:9200/demo_index"
```

预期你会看到（示意，节选）：

```json
{
  "error" : {
    "root_cause" : [
      { "type" : "resource_already_exists_exception",
        "reason" : "index [demo_index/AbCdEfGhIjKlMnOpQrStUv] already exists" }
    ],
    "type" : "resource_already_exists_exception",
    "reason" : "index [demo_index/AbCdEfGhIjKlMnOpQrStUv] already exists"
  },
  "status" : 400
}
```

**4. 探活（HEAD 只要状态码，不要 body）：**

```bash
curl -i -X HEAD "http://localhost:9200/demo_index2"
```

预期你会看到（示意，节选）：

```text
HTTP/1.1 200 OK
content-type: application/json; charset=UTF-8
```

**5. 手动 refresh（后面实验 04 的主角，这里先混个脸熟）：**

```bash
curl -s -X POST "http://localhost:9200/demo_index2/_refresh"
```

预期你会看到：

```json
{ "_shards" : { "total" : 1, "successful" : 1, "failed" : 0 } }
```

**6. 删掉演习对象，再确认删干净了：**

```bash
curl -s -X DELETE "http://localhost:9200/demo_index2"
```

预期你会看到：

```json
{ "acknowledged" : true }
```

```bash
curl -s "http://localhost:9200/demo_index2"
```

预期你会看到（示意，节选）：

```json
{ "error" : { "type" : "index_not_found_exception", "reason" : "no such index [demo_index2]" }, "status" : 404 }
```

### 第三组：文档 CRUD

**1. 指定 id 写入（PUT）：**

```bash
curl -s -X PUT "http://localhost:9200/demo_index/_doc/2001" -H "Content-Type: application/json" -d '
{
  "id": 2001,
  "title": "曲面显示器",
  "content": "曲面显示器，亮三个以内坏点符合出厂标准，超出可换货。",
  "category": "家电",
  "price": 1999.0,
  "created_at": "2026-10-28"
}'
```

预期你会看到（示意，节选）：

```json
{
  "_index" : "demo_index",
  "_id" : "2001",
  "_version" : 1,
  "result" : "created",
  "_shards" : { "total" : 1, "successful" : 1, "failed" : 0 },
  "_seq_no" : 50,
  "_primary_term" : 1
}
```

**2. 同一个 id 再写一次（不是报错，是整篇覆盖）：**

```bash
curl -s -X PUT "http://localhost:9200/demo_index/_doc/2001" -H "Content-Type: application/json" -d '
{
  "id": 2001,
  "title": "曲面显示器（升级款）",
  "content": "曲面显示器升级款，支持换货，运费险生效。",
  "category": "家电",
  "price": 2199.0,
  "created_at": "2026-10-28"
}'
```

预期你会看到（示意，节选）：

```json
{ "_id" : "2001", "_version" : 2, "result" : "updated", "_seq_no" : 51, "_primary_term" : 1 }
```

**3. 不指定 id 写入（POST，ES 自动生成）：**

```bash
curl -s -X POST "http://localhost:9200/demo_index/_doc" -H "Content-Type: application/json" -d '
{ "id": 2002, "title": "机械键盘", "content": "机械键盘，键帽打油可申请更换。", "category": "配件", "price": 399.0, "created_at": "2026-10-28" }'
```

预期你会看到（示意，节选）：

```json
{ "_id" : "YjQ0NGM3YmE1Nj", "_version" : 1, "result" : "created" }
```

**4. 按 id 取：**

```bash
curl -s "http://localhost:9200/demo_index/_doc/2001"
```

预期你会看到（示意，节选）：

```json
{
  "_index" : "demo_index",
  "_id" : "2001",
  "_version" : 2,
  "_seq_no" : 51,
  "_primary_term" : 1,
  "found" : true,
  "_source" : {
    "title" : "曲面显示器（升级款）",
    "price" : 2199.0
  }
}
```

```bash
curl -s "http://localhost:9200/demo_index/_doc/9999"
```

预期你会看到：

```json
{ "_index" : "demo_index", "_id" : "9999", "found" : false }
```

**5. 局部更新（_update 是取出-合并-写回，不是原地改字段）：**

```bash
curl -s -X POST "http://localhost:9200/demo_index/_update/2001" -H "Content-Type: application/json" -d '
{ "doc": { "price": 1899.0 } }'
```

预期你会看到（示意，节选）：

```json
{ "_id" : "2001", "_version" : 3, "result" : "updated" }
```

给不存在的 id 做 _update 试试（会 404）：

```bash
curl -s -X POST "http://localhost:9200/demo_index/_update/9999" -H "Content-Type: application/json" -d '
{ "doc": { "price": 1.0 } }'
```

预期你会看到（示意，节选）：

```json
{ "error" : { "type" : "document_missing_exception", "reason" : "[9999]: document missing" }, "status" : 404 }
```

**6. 删除：**

```bash
curl -s -X DELETE "http://localhost:9200/demo_index/_doc/2001"
```

预期你会看到（示意，节选）：

```json
{ "_id" : "2001", "_version" : 4, "result" : "deleted" }
```

再删一次同一条：

```bash
curl -s -X DELETE "http://localhost:9200/demo_index/_doc/2001"
```

预期你会看到（示意，节选）：

```json
{ "_id" : "2001", "_version" : 1, "result" : "not_found" }
```

**7. _mget：一次取多条（省网络往返）：**

```bash
curl -s -X POST "http://localhost:9200/demo_index/_mget" -H "Content-Type: application/json" -d '
{ "ids": ["1001", "1002", "9999"] }'
```

预期你会看到（示意，节选）：

```json
{
  "docs" : [
    { "_index" : "demo_index", "_id" : "1001", "_version" : 1, "found" : true,
      "_source" : { "title" : "旗舰智能手机 Pro Max", "category" : "手机" } },
    { "_index" : "demo_index", "_id" : "1002", "_version" : 1, "found" : true,
      "_source" : { "title" : "主动降噪蓝牙耳机", "category" : "耳机" } },
    { "_index" : "demo_index", "_id" : "9999", "found" : false }
  ]
}
```

**8. _bulk：一次请求打包多种操作。** 重点在请求体格式——**ndjson**：一行 action、一行数据，交替排列；每行都是独立完整的 JSON，行尾没有逗号，整个请求体最后以换行符结尾；Content-Type 是 `application/x-ndjson`：

```bash
curl -s -X POST "http://localhost:9200/_bulk" -H "Content-Type: application/x-ndjson" --data-binary $'{"index":{"_index":"demo_index","_id":"3001"}}\n{"id":3001,"title":"曲面显示器","content":"曲面显示器，支持换货，运费险生效。","category":"家电","price":1999.0,"created_at":"2026-10-28"}\n{"delete":{"_index":"demo_index","_id":"3001"}}\n'
```

预期你会看到（示意，节选）：

```json
{
  "took" : 12,
  "errors" : false,
  "items" : [
    { "index" : { "_index" : "demo_index", "_id" : "3001", "_version" : 1,
                  "result" : "created", "status" : 201 } },
    { "delete" : { "_index" : "demo_index", "_id" : "3001", "_version" : 2,
                   "result" : "deleted", "status" : 200 } }
  ]
}
```

注意 delete 的 action 行后面没有数据行——它不需要。

**9. 再看一次"部分成功"——bulk 里塞一条写不进去的**（price 是 float，这里给字符串）：

```bash
curl -s -X POST "http://localhost:9200/_bulk" -H "Content-Type: application/x-ndjson" --data-binary $'{"index":{"_index":"demo_index","_id":"3002"}}\n{"id":3002,"title":"坏数据","content":"这条的 price 类型不对","category":"配件","price":"不是数字","created_at":"2026-10-28"}\n'
```

预期你会看到（示意，节选；错误类型措辞以 8.11.4 实际输出为准）：

```json
{
  "took" : 8,
  "errors" : true,
  "items" : [
    { "index" : { "_index" : "demo_index", "_id" : "3002", "status" : 400,
      "error" : { "type" : "document_failure_exception",
                  "caused_by" : { "type" : "mapper_parsing_exception",
                                  "reason" : "failed to parse field [price] of type [float] in document with id '3002'" } } } }
  ]
}
```

注意两层：整批响应的 HTTP 状态码还是 200（请求本身没挂），坏消息只藏在 items 里；顶层 `errors` 是 true，但具体哪条坏、为什么坏，得逐条翻 items 找 error 字段。这就是为什么所有 bulk 调用方都必须写逐条检查的代码——[专栏一·07](../专栏一-ES实战/07-Java客户端集成.md)里 Java 客户端那段循环就是干这个的。

### 第四组：查询分析

**1. match 全文检索（会分词）：**

```bash
curl -s -X POST "http://localhost:9200/demo_index/_search" -H "Content-Type: application/json" -d '
{ "query": { "match": { "title": "蓝牙耳机" } } }'
```

预期你会看到（示意，节选）：

```json
{
  "took" : 5,
  "timed_out" : false,
  "_shards" : { "total" : 1, "successful" : 1, "skipped" : 0, "failed" : 0 },
  "hits" : {
    "total" : { "value" : 20, "relation" : "eq" },
    "max_score" : 6.93,
    "hits" : [
      {
        "_index" : "demo_index",
        "_id" : "1002",
        "_score" : 6.93,
        "_source" : { "title" : "主动降噪蓝牙耳机", "category" : "耳机" }
      },
      { "_id" : "1003", "_score" : 3.52, "_source" : { "title" : "折叠屏手机" } }
    ]
  }
}
```

为什么 20 条这么多？standard 分词器把"蓝牙耳机"拆成"蓝/牙/耳/机"四个单字，match 默认 OR，标题里带"机"字的商品全中招——这是[专栏一·03](../专栏一-ES实战/03-检索DSL查询写不对一切白搭.md)埋的坑，实验 05 专门拆。

**2. term 精确匹配（不分词）：**

```bash
curl -s -X POST "http://localhost:9200/demo_index/_search" -H "Content-Type: application/json" -d '
{ "query": { "term": { "category": "手机" } } }'
```

预期你会看到（示意，节选）：

```json
{
  "hits" : {
    "total" : { "value" : 9, "relation" : "eq" },
    "max_score" : 2.77,
    "hits" : [
      { "_id" : "1001", "_score" : 2.77,
        "_source" : { "title" : "旗舰智能手机 Pro Max", "category" : "手机" } }
    ]
  }
}
```

category 是 keyword 类型，"手机"原样进词典，term 原样去查，精确命中 9 条——term 和 match 的分野见[专栏一·03](../专栏一-ES实战/03-检索DSL查询写不对一切白搭.md)。

**3. bool 组合（must 算分，filter 不算分）：**

```bash
curl -s -X POST "http://localhost:9200/demo_index/_search" -H "Content-Type: application/json" -d '
{
  "query": {
    "bool": {
      "must":   [ { "match": { "content": "退款" } } ],
      "filter": [
        { "term":  { "category": "手机" } },
        { "range": { "price": { "gte": 5000 } } }
      ]
    }
  }
}'
```

预期你会看到（示意，节选）：

```json
{
  "hits" : {
    "total" : { "value" : 1, "relation" : "eq" },
    "max_score" : 3.45,
    "hits" : [
      { "_id" : "1001", "_score" : 3.45,
        "_source" : { "title" : "旗舰智能手机 Pro Max", "price" : 6999.0 } }
    ]
  }
}
```

只有 1001 一条命中：content 里有"退款"、category 是手机、价格过 5000。生成的那批"手机"随机价 20~3000，被 range 挡在门外；filter 里的条件不算分，所以 `max_score` 只来自 must 里那个 match。

**4. 排序、分页、_source 过滤：**

```bash
curl -s -X POST "http://localhost:9200/demo_index/_search" -H "Content-Type: application/json" -d '
{
  "query": { "match_all": {} },
  "from": 0, "size": 3,
  "sort": [ { "price": "asc" } ],
  "_source": [ "title", "price" ]
}'
```

预期你会看到（示意，节选）：

```json
{
  "hits" : {
    "total" : { "value" : 51, "relation" : "eq" },
    "max_score" : null,
    "hits" : [
      { "_id" : "1004", "_score" : null, "_source" : { "title" : "高透钢化膜", "price" : 19.9 } },
      { "_id" : "1032", "_score" : null, "_source" : { "title" : "耳机产品 1032 型", "price" : 39.37 } },
      { "_id" : "1011", "_score" : null, "_source" : { "title" : "磨砂手机保护壳", "price" : 49.0 } }
    ]
  }
}
```

用 sort 之后 `_score` 和 `max_score` 都成了 null（没算分）；`_source` 过滤只把要的字段还给你，省流量也省眼球。from+size 翻页翻得浅没问题，翻到 `from + size > 10000` ES 会直接拒绝你——这堵墙怎么来的、绕过去用什么，实验 09 专门讲。

**5. 只数数：**

```bash
curl -s "http://localhost:9200/demo_index/_count"
```

预期你会看到：

```json
{ "count" : 51, "_shards" : { "total" : 1, "successful" : 1, "skipped" : 0 } }
```

（51 = 50 条种子 + 1 条步骤 3 里 POST 自动 id 的机械键盘，3001 已被 bulk 里的 delete 删了。）

**6. _analyze：看分词器对一个词做了什么：**

```bash
curl -s -X POST "http://localhost:9200/_analyze" -H "Content-Type: application/json" -d '
{ "analyzer": "standard", "text": "蓝牙降噪耳机" }'
```

预期你会看到（示意，节选）：

```json
{
  "tokens" : [
    { "token" : "蓝", "start_offset" : 0, "end_offset" : 1, "type" : "<IDEOGRAPHIC>", "position" : 0 },
    { "token" : "牙", "start_offset" : 1, "end_offset" : 2, "type" : "<IDEOGRAPHIC>", "position" : 1 },
    { "token" : "降", "start_offset" : 2, "end_offset" : 3, "type" : "<IDEOGRAPHIC>", "position" : 2 },
    { "token" : "噪", "start_offset" : 3, "end_offset" : 4, "type" : "<IDEOGRAPHIC>", "position" : 3 }
  ]
}
```

（"耳""机"两个 token 同理，节选没列。）单字切分，眼见为实。

**7. _explain：拆开看一篇文档为什么得这个分：**

```bash
curl -s -X POST "http://localhost:9200/demo_index/_explain/1002" -H "Content-Type: application/json" -d '
{ "query": { "match": { "content": "降噪" } } }'
```

预期你会看到（示意，节选，实际 details 树更深）：

```json
{
  "matched" : true,
  "explanation" : {
    "value" : 2.92,
    "description" : "sum of:",
    "details" : [
      { "value" : 1.45,
        "description" : "weight(content:降 in 1) [PerFieldSimilarity], result of:",
        "details" : [ ] },
      { "value" : 1.47,
        "description" : "weight(content:噪 in 1) [PerFieldSimilarity], result of:",
        "details" : [ ] }
    ]
  }
}
```

description 里的 `in 1` 是 Lucene 内部文档编号，不是你的 _id，不用对。

### 第五组：Kibana Dev Tools 走查

curl 够用但手疼，日常操作的正主是 Kibana 的 Dev Tools。

**1. 浏览器开 http://localhost:5601**，左侧菜单 → Management → Dev Tools。

**2. 左边编辑器里敲一条：**

```text
GET demo_index/_count
```

光标放这行，按 Ctrl+Enter（Mac 是 Cmd+Enter），右侧出结果。和 curl 拿到的是同一个 JSON。

**3. 再敲一条查询，感受补全**：输入 `GET demo_index/_search`，回车换行，敲 `{`，Dev Tools 会自动补全结构、提示字段名；把第四组里的 bool 查询粘进来跑一遍。请求历史在左侧 History 面板里，翻得回来。左边工具条还有个小扳手图标——**Wrench 菜单**——里面有两个你会反复用的功能：Copy as cURL（把当前请求翻译成 curl 命令，发给同事）、Open documentation（跳官方文档）。

以后实验里的 curl 命令都可以直接搬进 Dev Tools：方法大写、URL 去掉 `http://localhost:9200` 前缀即可，其他一模一样。反过来，Dev Tools 里的请求随时可以 Copy as cURL 拿到命令行去跑——两边是同一个协议的两张皮。

## 现象解释

ES 的响应 JSON 看着字段多，其实就查询、写入两本词典。先给一张速查表（单节点、1 主分片、0 副本的期望值），再逐条解释：

| 字段 | 出现在 | 什么意思 | 单节点 1 分片 0 副本时的期望值 |
|------|--------|----------|-------------------------------|
| took | 查询响应 | 耗时，毫秒 | 个位数 |
| timed_out | 查询响应 | 是否超时被掐断 | false（超时也可能带结果回来） |
| _shards.total | 两者都有 | 查询要访问/写入要确认的分片数 | 1 |
| _shards.successful | 两者都有 | 成功的分片数 | 1（没有副本可挂） |
| hits.total.value | 查询响应 | 命中文档数 | 50 条数据就是 50 |
| hits.total.relation | 查询响应 | 这个总数的可信度 | eq（超过 1 万条变 gte） |
| max_score / _score | 查询响应 | 相关性得分 | 有算分是正数，sort/filter 时是 null |
| _source | 查询响应 | 你写入的原文 | 原样返回 |
| acknowledged | 写响应 | 集群收下了请求 | true |
| result | 写响应 | created/updated/deleted/not_found | 跟着你刚做的操作变 |
| _version | 写响应 | 这篇文档被写的第几版 | 新建 1，每次写 +1 |
| _seq_no / _primary_term | 写响应 | 分片级操作序号/主分片任期 | 单调递增 / 1 |

### 查询响应（_search 的返回）

- **took**：这次查询花了多少毫秒。本地 50 条数据，个位数是正常水位；这个数字生产上是你监控面板的第一公民。
- **timed_out**：查询有没有超时被掐断。注意超时的查询**还是会返回结果**，只是结果可能不全——所以不能拿它当错误处理。
- **_shards.total / successful / skipped**：这次查询去了几个分片、成了几个、跳了几个。我们是单节点、demo_index 是 1 主分片 0 副本，所以 total 是 1——查询只需要问一个主分片要数据。skipped 是带 sort 的查询提前终止时跳过的分片（有排序保证时不用全查完），这里 0。坑点里展开"为什么不是 2"。
- **hits.total.value + relation**：命中总数和这个总数的"可信度"。relation=eq 是精确数（数到头了）；relation=gte 是"至少这么多"——数据量超过 1 万条（`track_total_hits` 默认 10000）时，ES 数到 1 万就停手不数了，因为你翻不了那么深（实验 09 讲这堵墙），它就不替你白数。50 条的 demo_index 永远是 eq。
- **max_score**：本次查询所有命中文档里的最高分。它的用途是归一化和健康观测，业务上少碰。
- **hits.hits 里的四件套**：`_index`（来自哪个索引）、`_id`（文档主键）、`_score`（这篇文档的相关性得分，BM25，实验 08 专门拆）、`_source`（你写进去的原文，ES 原封还你）。一旦你用 sort 排序，`_score` 和 `max_score` 都是 null——没算分，就没有分。

### 写响应（增删改的返回）

- **acknowledged**：集群"收到并处理"了这个请求。索引级别的操作（PUT/DELETE 索引）只有它。
- **result**：这次对文档干了什么——`created`（新建）、`updated`（覆盖或更新）、`deleted`（删掉了）、`not_found`（要删的本来就不在）。它是写操作成功与否的第一落点。
- **_version**：这篇文档被写过的次数。创建是 1，每次覆盖/更新 +1，删除也占一个版本号。步骤 6 里你可能注意到一个怪现象：删一篇不存在的文档，返回 `_version: 1`——"删除标记"（tombstone）本身也是一个版本为 1 的存在，ES 记这笔账是为了并发场景下删了又写、写了又删的先后顺序可判定。它不是给你看的流水账，是乐观并发控制的弹药，马上说。
- **_seq_no + _primary_term**：分片级别单调递增的操作序号 + 主分片任期。`_version` 管"这篇文档的第几版"，`_seq_no` 管"这个分片上的第几号操作"。并发控制的实战用法：写请求带上 `?if_seq_no=51&if_primary_term=1`，版本对不上直接 409——和 MySQL 乐观锁的 CAS 一个意思。前面步骤里你看到的两次 PUT 同 id 静默覆盖，就是没人做版本检查的结果。
- **_shards.total**：这次写要等几个分片确认。1 主分片 0 副本 → 1（只要主分片确认就算成）。为什么单节点上看到的一定是 1，坑点第一条展开。

### _cat 家族

`?v` 是显示表头。_cat 输出是文本表格，给人看的；同一信息要进程序，用 `?format=json` 拿 JSON。`_cat/indices` 是索引台账（含系统索引），`_cat/shards` 把主副分片摊开，`_cat/segments` 是最细一层的段台账——这三个视图在实验 02 里会和磁盘目录一一对上。

## 常见坑点

**1. 单节点 _shards.successful 为什么不是 2？** 不是坏了，是根本没有副本。7.x 起新建索引默认 0 副本，查询响应的 `_shards.total` 数的是"这次查询访问了几个分片"，1 主分片就是 1；写响应的 `_shards.total` 数的是"这次写要等几个分片确认"，0 副本就是 1。哪天你在单节点上配了 `number_of_replicas: 1`，会看到 yellow：副本无家可归，一直 unassigned——这是实验 10 的剧本。

**2. _version 的乐观并发。** 两个客户端同时 PUT 同一个 _id，后到的覆盖先到的，ES 不会拦你——默认行为就是"整篇覆盖"。要防丢写，写请求带 `if_seq_no` + `if_primary_term`（版本不对返回 409），或者写入时加 `?op_type=create`（_id 已存在直接 409）。

**3. bulk 的 ndjson 格式错行，是新手第一大翻车点。** 四个高频死法：①每行行尾带逗号（ndjson 每行都是独立完整的 JSON，行与行之间不能有逗号）；②action 行后面忘了跟数据行，或删错了行数错位；③整个请求体结尾没有换行符，报 `The bulk request must be terminated by a newline`；④ Content-Type 传成了 `application/json`。bulk 是部分成功协议：HTTP 200 不代表全成，必须逐条看 items 里有没有 error 字段（专栏一·07 的 Java 代码里专门写了这一步）。

**4. 系统索引别动。** `_cat/indices` 里那些 `.` 开头的（`.geoip_databases` 等）是 ES 自己的，删了它重建就是。

**5. Windows 的 curl 引号。** PowerShell 里单引号双引号转义规则和 bash 不同，多行 JSON 十有八九翻车。统一在 Git Bash 里跑，或者干脆用 Kibana Dev Tools，别跟引号搏斗。

## 进一步实验

- **让集群变黄**：`PUT demo_index/_settings {"index":{"number_of_replicas":1}}`，再看 `_cluster/health`——status 变 yellow、unassigned_shards 出现 1。看完改回 0。
- **突破 1 万总数**：往 demo_index 用 bulk 灌 1 万多条（把 exp01-seed.py 的 50 改成 10500 重跑），再 _search，看 `hits.total` 变成 `{"value": 10000, "relation": "gte"}`；带 `"track_total_hits": true` 再查，relation 变回 eq。
- **自选列**：`curl -s "http://localhost:9200/_cat/indices?h=index,pri,rep,docs.count,store.size"`，只看你要的列，写监控脚本用这招。
- **查询为什么慢**：任意 _search 里加 `"profile": true`，响应里多出 profile 段，把每个阶段的耗时摊开——排查慢查询的第一步。

## 最后，总结

这一篇跑了二十多条命令，要带走的是三样东西：**API 地图**（集群体检看 `_cat`/`_cluster`，索引管理 PUT/GET/HEAD/DELETE/`_refresh`，文档 CRUD `_doc`/`_update`/`_mget`/`_bulk`，查询 `_search`/`_count`/`_analyze`/`_explain`）；**响应词典**（查询看 took/`_shards`/`hits.total`/`_score`，写操作看 result/`_version`/`_seq_no`，速查表在上面）；**手感**（curl 和 Dev Tools 都玩过一轮，bulk 的 ndjson 手写对过一次，部分成功的响应亲手见过一次）。以后接手任何 ES 集群，第一眼看 `_shards`——分片数和副本数就写在那里，这是这本词典最实用的一条。

下一篇把这些 JSON 变成看得见的东西：进容器，亲眼看这 50 条数据在磁盘上长什么样——[02-磁盘上的ES](02-磁盘上的ES-亲眼看数据长什么样.md)。
