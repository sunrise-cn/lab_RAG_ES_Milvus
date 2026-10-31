# 实验 01：第一次见 ES——REST API 全景

> 对应专栏五文档：`专栏五-动手实验/01-第一次见ES-REST-API全景.md`
> 执行日期：2026-10-31 ｜ 环境：ES 8.11.4 单节点（docker compose 项目 lab_rag_es_milvus）

## 做了什么

按文档五组步骤全部跑通：材料构建（`exp01-seed.py`，demo_index 50 条）→ 集群体检（`_cluster/health` + `_cat` 家族）→ 索引管理（demo_index2 的建/探活/refresh/删）→ 文档 CRUD（PUT/POST/GET/_update/DELETE/_mget/_bulk）→ 查询分析（match/term/bool/sort 分页/_count/_analyze/_explain）。逐条原始输出存档在 `outputs/01~06_*.txt`。

第五组 Kibana Dev Tools 是图形界面走查（http://localhost:5601 → Management → Dev Tools），环境已验证可用；建议亲手在 Dev Tools 里敲一遍 `GET demo_index/_count` 和 bool 查询，体验补全和 Copy as cURL。

## 实际输出与文档"预期示意"的差异

文档声明预期输出是推理示意，本次实录差异如下（均不影响结论）：

1. **`active_primary_shards` 是 28 不是 2**：文档假设只有 demo_index + `.geoip_databases`，但本环境开着 Kibana，它建了 26 个 `.kibana*`/`.internal*` 系统索引，每个 1 个主分片。
2. **`_cat/indices?v` 只列出 demo_index**：8.x 里系统索引是 hidden，`_cat/indices` 默认不显示；`_cat/shards` 会把它们全摊出来。看全貌用 `_cat/indices?v&expand_wildcards=all`。
3. **节点名是容器 hostname**（如 `1447d734368d`）而不是 `es01`：compose 没设 `node.name`，ES 默认取主机名。
4. **删不存在的文档返回 `_version: 5`（文档示意是 1）**：8.11.4 里 tombstone 也占用递增的版本号——先删过 2001（版本 4），再删一次 not_found 返回版本 5。
5. **bulk 类型错误的报错是 `document_parsing_exception`**（caused_by `number_format_exception`），文档示意猜的是 `document_failure_exception`/`mapper_parsing_exception`——文档自己也标了"措辞以 8.11.4 实际输出为准"。
6. **match "蓝牙耳机" 命中 21 条**（示意 20 条）：种子数据 50 条固定，但 standard 拆单字后带"机/耳"的标题数量文档数错了，以实录为准。
7. **demo_index 的 segment `committed=false`**：refresh 生成的段还没经历 flush/fsync，和文档示意 `committed=true` 不同，正好印证了"refresh ≠ 落盘"。

## 结论与实践经验

**API 地图**（哪类活找哪个接口）：
- 集群体检：`_cluster/health`、`_cat/indices|shards|segments|nodes`（`?v` 带表头，`?format=json` 给程序用）
- 索引管理：`PUT/GET/HEAD/DELETE <index>`、`_refresh`
- 文档 CRUD：`_doc`（PUT 指定 id / POST 自动 id）、`_update`、`_mget`、`_bulk`
- 查询分析：`_search`、`_count`、`_analyze`、`_explain`

**响应词典**（单节点 1 分片 0 副本的期望值）：
- 查询响应：`took`（毫秒）、`timed_out`（超时也会带结果回来）、`_shards.total=1`、`hits.total.relation=eq`（≤1 万条精确数）、sort 后 `_score`/`max_score` 为 null（没算分就没有分）
- 写响应：`result`（created/updated/deleted/not_found）、`_version` 单调递增（含删除占位）、`_seq_no`+`_primary_term` 是乐观并发控制的弹药（`if_seq_no`+`if_primary_term` 对不上返回 409）

**手感经验**：
1. 接手任何 ES 集群，第一眼看 `_shards`——分片和副本配置都写在那里。
2. bulk 是部分成功协议：HTTP 200 ≠ 全成，坏消息藏在 `items[].error` 里，调用方必须逐条检查。ndjson 格式（行尾无逗号、整体以换行结尾、Content-Type 用 `application/x-ndjson`）是新手第一大翻车点。
3. PUT 同 id 默认整篇静默覆盖，要防丢写就带版本条件或 `op_type=create`。
4. standard 分词器把中文拆成单字（`_analyze` 眼见为实），所以 match 中文会"泛命中"——这是实验 05 要拆的坑。
5. term 查 keyword 原样精确命中（category=手机 → 9 条）；match 走分词；bool 里 filter 不算分（`max_score` 只来自 must）。
