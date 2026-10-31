# 03 第一次见 Milvus：attu 与 SDK 全景

实验 01、02 把 ES 从 API 到磁盘摸了一遍，现在换另一半地基。Milvus 和 ES 最大的不同在你按下回车的第一秒就能感觉到：ES 你 curl 一下就有了响应，Milvus 你 curl 什么都没用——它只说 gRPC，不认 HTTP。所以这一篇的路线是：先靠图形界面 attu 建立画面感，再用 pymilvus SDK 把核心 API 挨个跑通，最后打开 MinIO 控制台，亲眼看看 Milvus 的数据到底存在哪（答案不在 Milvus 容器里）。

## 这个实验验证什么

Milvus 的操作全景：attu 图形界面能看什么、干什么；pymilvus 的核心 API 一条链跑通（连接、建 collection、insert、flush、建索引、load、search、query、get）；insert 和 search 的响应对象怎么读；Milvus 的数据真身躺在对象存储的哪个目录里。

关联正文：[专栏二·02](../专栏二-Milvus实战/02-上手与架构速览.md)（attu、三个容器是架构本身）、[专栏二·07](../专栏二-Milvus实战/07-客户端使用.md)（两代客户端、批量插入、load）、[专栏三·06](../专栏三-运行机制/06-存算分离架构.md)（存算分离，MinIO 是数据的最终归宿）。

## 实验材料构建

前提：环境按 [00-实验环境](00-实验环境.md)起好，venv 激活，当前目录在 `lab`。

材料脚本 [lab/scripts/exp03-seed.py](lab/scripts/exp03-seed.py)：显式 schema 建 collection `exp03_person`（id 主键、embedding 128 维向量、city 标量字段），插入 100 条随机向量，flush、建 HNSW 索引、load，然后 search/query/get 各跑一次。脚本里每个 API 前面有注释标了它对应 MySQL 的什么操作：

```python
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
```

跑它：

```bash
python scripts/exp03-seed.py
```

预期你会看到（示意，节选；distance 数值以你的实际输出为准，量级对了就正常）：

```text
insert: insert_count=100, primary_keys 前 5 个: [0, 1, 2, 3, 4]
flush 完成，num_entities=100
search hit: id=0, distance=0.0000, city=北京
search hit: id=52, distance=4.5091, city=北京
search hit: id=17, distance=4.6138, city=上海
search hit: id=74, distance=4.6657, city=深圳
search hit: id=93, distance=4.7020, city=杭州
query "city == '北京'" 前 5 条: [{'id': 0, 'city': '北京'}, {'id': 4, 'city': '北京'}, ...]
get ids=[1,2,3]: [{'id': 1, 'city': '上海'}, {'id': 2, 'city': '杭州'}, {'id': 3, 'city': '深圳'}]
查询向量（粘到 attu 用）: [0.3047, 0.7281, 0.5683, ...]
```

几个数字先说破，免得你对输出起疑：top1 的 distance 是 0，因为查询向量就是库里第 0 条自己，自己到自己的距离是 0；其余几条的 distance 在几到二十几之间——[0,1) 均匀分布的 128 维随机向量，两两欧氏距离的量级算出来在 4.6 上下（若返回的是距离的平方则是 21 左右，不同版本实现有差异，v2.4.4 以实际输出为准）。反正排序不受影响：小的永远近，量级明显离谱（比如上千）才需要怀疑数据。query/get 的返回是 dict 列表，不同小版本字段组织可能有差异，以实际为准。

## 实验步骤

### 第一步：attu 走查——Milvus 的 Navicat

**1. 浏览器开 http://localhost:3000**（attu 2.4 界面，文案以实际为准）。

**2. Collection 列表**：进来就能看到 `exp03_person`，行数 100，状态是已加载（loaded）。这个列表就是 MySQL 里表清单的位置。

**3. 点进 exp03_person，看 Schema 标签页**：三个字段一字排开——id（Int64，主键）、embedding（FloatVector，dim=128）、city（VarChar）。这就是建表语句的可视化，和脚本里的 FieldSchema 一一对应。注意没有隐式字段：Milvus 默认没有 ES 动态映射那套"替你猜"，schema 之外的字段塞不进来（除非显式开 dynamic field）。

**4. Data Preview（数据预览）标签页**：翻 entity，等价于翻表数据。embedding 列太长只显示一截，city 列的"北京/上海/杭州/深圳"轮转肉眼可见。灌完数据先来这确认数据真的进去了，是排查"搜不到"的第一步——先分清是数据没进去，还是查询写错了。

**5. Search（Conduct Vector Search）标签页**：把脚本最后打印的那串"查询向量"（128 个数，一对方括号包着）粘进向量输入框，TopK 填 5，跑一次搜索。结果和脚本第 8 步一致：top1 是 id=0、distance 0。同样的数据、同样的索引，界面和代码拿到的世界是同一个。

### 第二步：pymilvus 全景——对照着读一遍脚本

回到脚本，按执行顺序把 API 过一遍（每行对应 MySQL 的什么，注释里都写了）。这里只补三条注释里放不下的：

- **`connections.connect(alias="default", ...)`**：建立的是全局连接，后面 `Collection("exp03_person")` 靠这个默认连接工作。这是 ORM 风格的写法；[专栏二·07](../专栏二-Milvus实战/07-客户端使用.md)里主推的是不带全局状态的 `MilvusClient`，两套都能用，本实验用 ORM 风格是因为它把"每个 API 是什么"摆得最清楚。
- **insert 之后为什么要有 flush**：insert 返回成功时，数据还在消息队列和内存里的 growing segment 里；flush 才把它封成 sealed segment 写进对象存储。`num_entities` 在 flush 之后是全的 100。
- **create_index 和 load 的顺序**：先建索引（对已 flush 的数据生成 HNSW 图文件，写进对象存储），再 load（把数据和索引文件拉进内存）。顺序反了 load 不到索引，能 load 但搜的姿势不对。

### 第三步：读响应对象——Milvus 的"响应词典"

实验 01 给 ES 建了响应字段词典的习惯，Milvus 这边照做，只是 JSON 换成了对象树。

**insert 的响应**（脚本第 5 步的 `ins`）：

- `ins.insert_count`：写进去的条数，100。ES 的 `_bulk` 响应要逐条翻 items 找 error，Milvus 的 insert 响应只给你一个总条数——错误处理走异常，不藏在响应里。
- `ins.primary_keys`：这批数据的主键列表。我们显式指定了主键，它就是把你给的 id 原样还你；如果 schema 用了 `auto_id=True`，这个列表是 Milvus 生成的 id，**必须接住存到业务库**——那是你以后取回这条数据的唯一凭据（专栏二·07 的"主键映射自己管"）。

**search 的响应**（脚本第 8 步的 `res`）：三层结构，对应"你给了几个查询向量 → 每个向量的命中列表 → 每条命中"：

```text
SearchResult                    # 一次 search 的总响应
 └─ hits（第 1 个查询向量的命中列表）
     ├─ hit.id         ← 命中的主键，对应 ES 的 hits.hits[]._id
     ├─ hit.distance   ← 距离，对应 ES 的 _score——但方向相反，越小越近
     └─ hit.entity     ← 动态字段容器，get("city") 取标量，对应 ES 的 _source
```

和 ES 的对照表收口：

| | ES | Milvus |
|---|---|---|
| 一批命中的总数 | hits.total.value | len(hits)（top-k 之内才有） |
| 排序依据 | _score，越大越靠前 | distance，越小越靠前 |
| 拿原字段 | hit._source | hit.entity.get("字段名") |
| 主键 | hit._id | hit.id |

### 第四步：MinIO 控制台走查——Milvus 的数据存在哪

这一步是本实验的重点。Milvus 号称存算分离、数据在对象存储，眼见为实。

**1. 浏览器开 http://localhost:9001**，账号密码都是 `minioadmin`（00-实验环境里钉死的）。

**2. 进 Object Browser**，左侧 bucket 列表里应该有一个 **a-bucket**——这是 Milvus 2.4 默认的 bucket 名（不同部署方式可能不同，以实际为准；如果你看到的不是这个名字，点开那个非空的就对了）。

**3. 点开 a-bucket，进 `files/` 目录**：里面能看到几类目录，常见的有 `insert_log/`（数据）、`index_files/`（索引）、`stats_log/`（统计信息），如果做过删除还有 `delta_log/`（删除标记——和实验 02 里 ES 的 .liv 一个思路）。

**4. 逐层点进 `files/insert_log/`**：先是几个纯数字命名的目录，再点一层还是数字，最后能看到一排 `.binlog` 文件。这些数字是 Milvus 内部的 collection/partition/segment ID（层级顺序以实际为准）——你不用翻译它们，只需要知道：**exp03_person 的每一行数据，就躺在这里面的 binlog 文件里**。

**5. 退回去点 `files/index_files/`**：HNSW 索引文件在这里。你刚才建的图结构，本体在对象存储里。

**6. 对比看一眼 Milvus 自己的容器**：它也挂了 milvusdata 卷，但那里面主要是消息队列和工作文件。数据真身不在 Milvus 节点本地，在 MinIO。

### 第五步：对比收口

三个实验走完，ES 和 Milvus 的第一印象可以并排放着看了：

| | ES | Milvus |
|---|---|---|
| 协议 | REST over HTTP + JSON | gRPC + SDK（attu 也是包了 gRPC 的客户端） |
| curl 能直接玩吗 | 能 | 不能，必须 SDK 或 attu |
| 建表 | PUT 索引（mapping，默认还能动态猜） | Collection（显式 schema，没有动态映射） |
| 响应形态 | JSON 词典（took/_shards/hits...） | 对象树（SearchResult → hits → hit） |
| 写入后可搜 | 近实时，默认 1 秒 refresh | 默认 Bounded 一致性（有短暂滞后，实验 14 展开） |
| 搜索的前提 | 无感 | 显式 load |
| 数据在哪 | 节点本地磁盘（实验 02 那些目录） | 对象存储 MinIO（这一篇的 bucket） |

最大的分野在最后一行，也是下一篇的引子：数据的家安在哪，决定了后面所有机制长相。

## 现象解释

**load 这一步为什么 ES 没有。** HNSW 是纯内存结构，搜索全靠图在内存里；Milvus 又是存算分离架构，query node 本地无数据，load 就是"把段数据和索引文件从对象存储拉进内存"的显式动作。ES 呢？mmap + page cache 把这件事做没了：段文件天然映射进内存，冷了操作系统自己淘汰、热了自己加载，用户全程无感。两个系统都逃不开"搜索要在内存里做"，一个把它藏进操作系统，一个把它显式化成 API——显式化的代价是多一步操作，换来的是对内存的精确控制（什么进内存、什么时候释放，都是你说）。

**distance 为什么是"越小越好"。** ES 的 _score 是相关性得分（BM25，越大越相关），Milvus 的 distance 是距离度量（L2，越小越近）。方向相反，读代码时这是真实的坑：按 distance 降序排个序，结果最不相关的排最前面。另外 distance 的"单位"跟 metric_type 走——L2 和 COSINE、IP 的数值不可比，实验 13 拿这个专门做文章。

**insert 成功 ≠ 数据落了对象存储。** insert 返回时数据在消息队列 + growing segment 里（所以 Milvus 写入后立刻就能搜——growing segment 直接可查）；flush 才封口成 sealed segment 写进 MinIO。这一篇你在 MinIO 里看到的 binlog，是 flush 之后的产物。写入路径的完整机制在[专栏三·06](../专栏三-运行机制/06-存算分离架构.md)。

**MinIO 里的目录为什么长成数字的样子。** 集群里 collection 名字是给人看的，存储层只认 ID（数字），和实验 02"ES 磁盘只认 uuid、不认索引名"是同一个设计——名字是逻辑层的皮，存储层要的是稳定的标识。两个系统殊途同归。

## 常见坑点

**1. collection 必须 load 才能搜。** 不 load 就 search，报 collection not loaded 之类的错。新手在 attu 里建完表插完数据直接搜，报错就是这个。ES 没这步，从 MySQL/ES 过来的最容易漏。drop 掉重建、重新 insert 之后，load 状态也会回退，要再 load。

**2. attu 里改了东西，SDK 侧要刷新。** `Collection` 对象会缓存 schema、行数这些信息；你在 attu 里重建了 collection 或改了结构，SDK 这边老对象继续用就是脏的——重新 `Collection("exp03_person")` 拿新对象。反过来也一样，SDK 建的东西 attu 侧记得刷新页面。

**3. MinIO 里的文件绝对不能手改、手删。** 和实验 02 的 ES 磁盘目录同理，还更严格：ES 的段目录好歹在一个节点上，Milvus 的 binlog、索引文件之外还有 etcd 里的元数据和你看到的文件互相引用——手动删文件，元数据和存储对不上，collection 可能就废了。清理数据走 `drop_collection`。

**4. bucket 名、目录层级以实际为准。** a-bucket 是 2.4 这套 compose 的默认值，别的部署（helm、Milvus Operator）默认名不同；insert_log 下的数字层级也别硬记顺序——记"bucket → files → 数据/索引分目录"这个骨架就够用。

**5. schema 错误是硬报错，不是静默猜。** 维度不是 128 直接拒收；VARCHAR 不给 max_length 建表就报错。ES 的动态映射替你猜类型（实验 06 专门拆那个坑），Milvus 反过来把话说在前面——两种设计你都会打交道，报错早的那个其实更好排查。

## 进一步实验

- **attu 搜索页换参数**：topK 从 5 改成 10，或把向量换一段（手改几个数字再搜），看命中列表怎么变——界面调参数比改代码重跑快得多，这是 attu 的正确用法：attu 里调通，参数再搬进代码。
- **drop 之后看 MinIO**：跑 `utility.drop_collection("exp03_person")`（或在 attu 里删），回 MinIO 刷新——目录不会立刻消失，异步 GC 有延迟。存算分离架构里"删除"是元数据标记 + 后台回收，和实验 02 的删除标记、实验 07 的 merge 回收是一个家族的思想。
- **换一致性级别**：脚本 search 里加 `consistency_level="Strong"`，insert 后立刻 search 对比默认 Bounded 的结果差异——实验 14 的前菜。
- **用 MilvusClient 重写**：拿[专栏二·07](../专栏二-Milvus实战/07-客户端使用.md)的 MilvusClient 写法把这个脚本重写一遍（create_collection schema 写法、client.search），跑通同样流程。两代 API 都摸过，以后看谁的教程都不迷糊。

## 最后，总结

这一篇给 Milvus 建了三样东西：**操作地图**（attu 看状态和 schema、Data Preview 验数据、搜索页调参数；SDK 干所有活），**响应词典**（insert 看 insert_count/primary_keys，search 是 SearchResult → hits → hit 的三层树，distance 越小越近），**数据观**（Milvus 自己不存数据，真身在 MinIO 的 bucket 里——insert_log 是数据、index_files 是索引，你在控制台里亲手点开过它们，存算分离眼见为实）。和 ES 对照着记：REST+JSON 对 gRPC+SDK，_score 对 distance，磁盘 uuid 目录对 MinIO bucket，近实时对一致性级别。地基的两半都摸过了，接下来回到 ES，撞上第一个反直觉现象：写入成功了，搜索却查不到——那是 refresh 与近实时的主场。
