# AGENTS.md

## 项目简介

这是一个 RAG 检索技术的学习仓库，主内容是 `ES与Milvus/` 下的学习专栏：以 RAG 为目标，先用 Elasticsearch 打好关键词检索地基、用 Milvus 打好向量检索地基，最后合龙成混合检索。

## 目录结构

- `ES与Milvus/专栏一-ES实战/`：ES 实战（会用）
- `ES与Milvus/专栏二-Milvus实战/`：Milvus 实战（会用）
- `ES与Milvus/专栏三-运行机制/`：底层原理深挖
- `ES与Milvus/专栏四-RAG实战/`：RAG 项目落地
- `ES与Milvus/专栏五-动手实验/`：17 个动手实验的文档与官方材料（见下文）
- `ES与Milvus/labs/`：**本仓库的实验工作目录**（用户实际跑实验的地方）
- `ES与Milvus/notes/`：学习笔记与速查卡

## 实验目录规范（重要）

用户会按 `ES与Milvus/专栏五-动手实验/` 中的文档顺序（01~17）依次跑实验。**每个实验都在 `ES与Milvus/labs/` 下创建一个独立文件夹，命名为 `NN_lab_XXX`**：

- `NN`：两位数字的实验编号，与专栏五文档编号一致（如 `01`、`12`）
- `XXX`：实验名称（英文，简短描述实验主题）

示例：`01_lab_es_rest_api`、`03_lab_milvus_first_touch`、`12_lab_ann_recall`。

每个实验文件夹里放该实验的执行记录：复现用的命令/脚本副本、实际输出、观察笔记、与文档"预期输出"的差异记录等。

## 实验环境

所有实验共用一套版本钉死的 Docker 环境，compose 文件在 `ES与Milvus/专栏五-动手实验/lab/`：

- `docker-compose.yml`：主环境——ES 8.11.4 单节点（9200，认证已关）、Kibana 8.11.4（5601）、Milvus standalone v2.4.4（19530/9091）、attu（3000）、etcd、MinIO（控制台 9001，账密均 minioadmin）
  - 2026-10 环境修复：原 MinIO 镜像 `minio/minio:RELEASE.2023-03-20T20-16-18Z` 已随官方停止分发而下架，compose 中替换为 `bitnamilegacy/minio:2025.4.22-debian-12-r1`（S3 兼容，控制台/对象浏览器保留；注意 bitnamilegacy 的 `latest` 是 2025-05-24 版，已移除控制台，不可用）
  - 2026-10 注：曾因本机 Docker 磁盘余量不足触发 ES 高水位（集群 RED），清理磁盘后已恢复默认水位配置；若再遇分片不分配，先查 `_cluster/allocation/explain` 和磁盘余量
- `es-cluster.yml`：实验 10 专用的三节点 ES 集群（9210~9212，各 512m 堆，不挂数据卷）
- `requirements.txt` + `.venv/`：Python 工具环境（elasticsearch 8.12.1、pymilvus 2.4.4、numpy、matplotlib；实验 17 另需 sentence-transformers）
  - 2026-10 环境修复：Python 3.12 下需额外 `pip install "setuptools<81" "marshmallow<4"`（pymilvus 2.4.4 依赖 pkg_resources，environs 与 marshmallow 4.x 不兼容），已在 .venv 中装好
- `scripts/expNN-*.py`：各实验的官方材料脚本（实验的"事实来源"，应照此复现）
- `install-ik.sh`：IK 中文分词插件安装（实验 05 前置；`docker compose down` 后插件会丢失，需重跑）
  - 2026-10 环境修复：IK 插件包已从 GitHub Releases 迁移，脚本改用 `https://get.infini.cloud/elasticsearch/analysis-ik/8.11.4`（旧 GitHub URL 已 404）
  - 安装 IK 会重启 es01，务必等 Kibana 完全就绪（5601 返回 200）后再装，否则 Kibana 迁移会被打断

### 常用命令（在 `ES与Milvus/专栏五-动手实验/lab/` 下执行）

compose 项目名已显式指定为 `lab_rag_es_milvus`（数据卷/网络前缀均为 `lab_rag_es_milvus_*`；实验 10 的集群项目名为 `lab_rag_es_milvus_cluster`）。

```bash
docker compose up -d            # 启动主环境
docker compose down -v          # 重置：连数据卷一起删，回出厂状态
docker compose ps               # 查看六个容器状态
source .venv/bin/activate       # 激活 Python 环境（macOS/Linux）
```

验证：`curl http://localhost:9200`（ES）、`curl http://localhost:9091/healthz`（Milvus）。

## Git 规范（重要）

远程仓库：`github.com/sunrise-cn/lab_RAG_ES_Milvus`（public）。

- **main 分支**：包含所有 lab 的完整内容。
- **每个实验一个 feature 分支**：分支名 `feature/NN_lab_XXX`（与 `ES与Milvus/labs/` 下的实验目录同名）。该分支上只放该实验的内容，或该实验必须依赖的前置资料。
- **实验说明**：每个 `labs/NN_lab_XXX/` 目录内必须有一份简短的实验说明（`README.md`），记录本实验得到的结论和实践经验（含与文档"预期输出"的差异）。
- 典型流程：`git checkout -b feature/NN_lab_XXX` → 做实验、写说明 → 提交 → 合并回 main。

## 跑实验的约定

1. 每个实验自带材料构建，不依赖其他实验留下的数据；从专栏五文档的"实验材料构建"小节照抄即可从干净状态复现。
2. 搞砸了第一反应是 `docker compose down -v` 重置重建，而不是修复脏数据（注意会清掉所有实验的数据）。
3. 文档中的"预期输出"是机制推理写出的示意，不是实录；实际输出对不上时，在实验文件夹里记录差异。
4. 进阶实验（10、11、16）完全隔离，可跳过；实验 10 用独立 compose 的三节点集群。
5. 实验的正确姿势是"预测"：每步执行前先猜结果，再按回车。
