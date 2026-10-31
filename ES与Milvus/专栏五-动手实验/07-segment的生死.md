# 07 segment 的生死

## 这个实验验证什么

一句话：**segment 不可变，所以删除和更新都只是打标记——删掉一半数据，磁盘占用一个字节不会少；真正物理回收发生在 merge。**

机制依据是 [专栏三·02 写入路径与近实时](../专栏三-运行机制/02-写入路径与近实时.md) 第四节"segment 不可变的连锁反应"，磁盘结构层面呼应实验 02 亲眼见过的 segment 文件（包括那个 `.liv` 位图文件）。正文里那段是推理，这一篇我们拿数字当面验。

## 实验材料构建

```bash
cd lab
source .venv/Scripts/activate
python scripts/exp07-gen.py
```

脚本建索引 `exp07_docs`（`id` 是 integer，`content` 是 text），分 20 批 bulk，每批 500 条（共 10000 条，id 1~10000），每批之间 flush 一次——flush 把内存里的东西固化成磁盘上的 segment，20 批写入就该留下 20 个上下的段。预期输出（示意，节选）：

```text
已创建索引 exp07_docs，开始 20 批写入（每批 500 条，批间 flush）
  批 01/20：写入 500 条，flush 完成
  批 02/20：写入 500 条，flush 完成
  ...
  批 20/20：写入 500 条，flush 完成
count = 10000
材料构建完成
```

## 实验步骤

### 第 1 步：看看这一万条数据留下的段

```bash
curl -s "http://localhost:9200/_cat/segments/exp07_docs?v&h=index,segment,shard,docs.count,docs.deleted,size"
```

预期你会看到一长串段（示意，节选）：

```text
index      segment   shard docs.count docs.deleted  size
exp07_docs _2          0        500            0 14.3kb
exp07_docs _4          0       1000            0 27.1kb
exp07_docs _6          0        500            0 14.3kb
exp07_docs _a          0        500            0 14.3kb
```

具体段数取决于写入速度和后台 merge 的竞争（默认 1 秒一次 refresh 还会额外造段，merge 又在后台吞并小段），二十几个、三十几个都正常。对照实验 02：你在磁盘上亲眼看过这些段对应的文件（`_2.cfe`、`_2.si`……），segment 名就是文件名前缀，两个视图一一对应。

### 第 2 步：基线数字

```bash
curl -s "http://localhost:9200/exp07_docs/_stats?filter_path=indices.exp07_docs.primaries.docs,indices.exp07_docs.primaries.store" | python -m json.tool
```

预期你会看到（示意，节选）：

```json
{
  "indices": {
    "exp07_docs": {
      "primaries": {
        "docs": { "count": 10000, "deleted": 0 },
        "store": { "size_in_bytes": 234567 }
      }
    }
  }
}
```

记住这组数字：count 10000、deleted 0、store.size 约几百 KB。接下来全部的戏都对着它演。

### 第 3 步：删掉一半，磁盘没动

```bash
curl -s -X POST "http://localhost:9200/exp07_docs/_delete_by_query?refresh=true" -H "Content-Type: application/json" -d '{"query": {"range": {"id": {"lte": 5000}}}}' | python -m json.tool
```

预期返回里 `"total": 10000`（delete_by_query 扫过的文档）、`"deleted": 5000`（真正删掉的）。再看 stats：

```bash
curl -s "http://localhost:9200/_cat/segments/exp07_docs?v&h=index,segment,docs.count,docs.deleted,size" 
```

```bash
curl -s "http://localhost:9200/exp07_docs/_stats?filter_path=indices.exp07_docs.primaries.docs,indices.exp07_docs.primaries.store" | python -m json.tool
```

预期：`docs.count` 变成 5000；`docs.deleted` 变成约 5000；**store.size 几乎没变**——注意，不是变小了，是基本没动。删掉了一半数据，磁盘占用一个字节没省。

### 第 4 步：段视图里的删除标记

再回看第 1 步那条 `_cat/segments`：段的 `size` 一列没有降，但 `docs.deleted` 列起来了——原来全是 0，现在大部分段的 docs.deleted 占了半壁甚至更多（示意，节选）：

```text
index      segment   shard docs.count docs.deleted  size
exp07_docs _2          0            0          500 14.3kb
exp07_docs _4          0          300          700 27.1kb
```

一个段里 docs.count 和 docs.deleted 此消彼长，size 纹丝不动。删除去了哪里？去位图里了。

### 第 5 步：update 的真相

改 1 号文档的一个字段：

```bash
curl -s -X POST "http://localhost:9200/exp07_docs/_update/1" -H "Content-Type: application/json" -d '{"doc": {"content": "文档1的正文已被改写"}}' | python -m json.tool
```

```bash
curl -s -X POST "http://localhost:9200/exp07_docs/_refresh" > /dev/null
curl -s "http://localhost:9200/exp07_docs/_stats?filter_path=indices.exp07_docs.primaries.docs" | python -m json.tool
```

预期：`docs.count` 还是 5000，**`docs.deleted` 比第 3 步又多了 1**。这一条 update 没有原地改任何东西——它是"新写一条 + 给旧的那条打删除标记"。ES 的世界里没有原地更新。

### 第 6 步：forcemerge，物理回收

```bash
curl -s -X POST "http://localhost:9200/exp07_docs/_forcemerge?max_num_segments=1"
```

等它跑完（一万条数据，很快），把三个视图都再看一遍：

```bash
curl -s "http://localhost:9200/_cat/segments/exp07_docs?v&h=index,segment,shard,docs.count,docs.deleted,size"
```

```bash
curl -s "http://localhost:9200/exp07_docs/_stats?filter_path=indices.exp07_docs.primaries.docs,indices.exp07_docs.primaries.store" | python -m json.tool
```

预期：段只剩 1 个；`docs.deleted` 归零；`docs.count` 5000；store.size 明显下降（大约砍半）。merge 把所有段重写成一个新段，重写时打了删除标记的文档不带进去，5000 条被标记的数据这才真正从磁盘上消失。

## 现象解释

把六步串成一句话：**删除和更新都不碰 segment，只碰标记；merge 是唯一的物理回收时刻。**

为什么删除不能原地做？回想实验 02 的磁盘结构和[专栏三·02](../专栏三-运行机制/02-写入路径与近实时.md)：posting list 是 delta 编码加位打包的紧凑结构，从里面"抠掉"一个 doc id 等于整个重写。ES 的办法是给每个 segment 配一个 `.liv`（live docs）位图文件——第 i 位是 0 表示第 i 篇文档已死。删除就是改位图：term 照样查到这篇文档，返回前被位图过滤掉。update 更彻底：新文档进 buffer 走完整写入链路，旧文档进位图。

merge 时刻才是清算时刻：旧段重写成新段，翻位图，是 0 的文档不搬。位图本身也被扔掉，换个新的全 1 的。这就是第 3 步到第 6 步之间所有魔法的谜底。

日常这套清算不用你操心，后台 merge 会按 tiered 策略持续吞并小段。forcemerge 是"手动要求清算到只剩 1 个段"，一把梭。

## 常见坑点

- **高频 update 的场景磁盘持续膨胀。**每次 update 净增一条删除标记，merge 跟不上时 deleted 越攒越多——`docs.deleted / docs.count` 比值持续走高，就是空间在漏。监控里盯 store size 和 docs.deleted 的趋势（`_cat/indices` 或 `_stats` 都能看到）。
- **forcemerge 生产慎用。**两个代价：merge 是重写，期间磁盘 IO 翻倍（读旧段 + 写新段同时进行）；合并完之后继续写入，又会从头攒新段，白合一次。它的正确场景是**不再写入的索引**：日志类按天滚动、老索引封版之后 forcemerge 一次，收益最大化。
- **close 掉的索引不参与 merge。**关闭的索引省了内存和句柄，但段保持原样，攒下的 deleted 标记一直躺在那。要清理得先 reopen，让 merge 接手。
- **把 `docs.count` 当业务计数要小心。**它是 Lucene 的活文档数（不计删除标记），和你写入的"总条数"是两个概念——第 3 步之后它就是 5000 不是 10000。

## 进一步实验

refresh_interval 调大后，同样的写入会少生成多少段？脚本里把这个常量留好了：

```python
REFRESH_INTERVAL = "1s"
```

把它改成 `"30s"`，INDEX 换个名字（比如 `exp07_docs_slow`，免得把主实验的索引覆盖了），再跑一遍 exp07-gen.py，对比两边的 `_cat/segments` 段数。预期：默认 1 秒造一个段，30 秒一造，段数明显变少、单段更大。这也正是实验 11（进阶）要展开的主题——refresh 间隔是写入吞吐和搜索成本之间的第一根滑杆。

## 最后，总结

- segment 不可变：删除打 `.liv` 位图标记，更新是新写一条加旧条标记，都不碰磁盘上的旧段。
- `docs.deleted` 是删除标记的账面数字，delete_by_query 之后 store.size 不动是设计使然，不是 bug。
- 物理回收只发生在 merge：重写旧段、跳过死文档。forcemerge 是手动触发清算，适合封版索引，不适合还在写的索引。
- 监控两件事：docs.deleted 与 docs.count 的比值（空间泄漏），段数（查询成本）。

下一篇讲打分：BM25 的词频饱和和长度归一，用 `_explain` 把打分的每一分钱拆开看。
