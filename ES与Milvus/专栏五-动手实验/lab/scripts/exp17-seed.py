"""实验 17 材料：50 条小语料，同时灌进 ES 和 Milvus。

两类各 25 条：
  err-xx：精确词类——带错误码/型号/编号的 IT 工单（BM25 主场）
  col-xx：口语同义类——文档用标准术语写，口语提问对不上字面（向量主场）

ES 侧：索引 exp17-docs，text 用默认 standard 分词器。
Milvus 侧：collection exp17-docs，embedding 用
  paraphrase-multilingual-MiniLM-L12-v2（输出维度以实测为准，
  脚本先 encode 一条测试句量出维度再建 schema，保证维度对齐）。

前置：pip install sentence-transformers（首次运行会下载几百 MB 模型）。

运行方式（先激活 venv）：
  cd lab && source .venv/Scripts/activate
  python scripts/exp17-seed.py
"""
from elasticsearch import Elasticsearch
from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    connections,
    utility,
)
from sentence_transformers import SentenceTransformer

ES_INDEX = "exp17-docs"
MILVUS_COLLECTION = "exp17-docs"
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"   # 实测维度通常 384，以实际为准

# (doc_id, text)。err-* 精确词类 / col-* 口语同义类（文档侧用标准术语）
DOCS = [
    ("err-01", "报错 ERR-1002 连接超时，检查网关防火墙的出站规则后重试"),
    ("err-02", "GPU RTX-4090 驱动崩溃，回退到上一版稳定驱动 536.23 可解决"),
    ("err-03", "Windows 错误码 0x80070005 拒绝访问，多为文件 ACL 权限配置问题"),
    ("err-04", "K8s Pod 状态 ImagePullBackOff，检查镜像仓库凭证 imagePullSecrets 配置"),
    ("err-05", "Oracle 报 ORA-12170，客户端到监听器的会话长时间无响应，核对 1521 端口"),
    ("err-06", "HTTP 502 Bad Gateway，上游服务连接被网关重置或超时"),
    ("err-07", "npm install 报 ERR! code ELIFECYCLE，删除 node_modules 后重装依赖"),
    ("err-08", "浏览器提示 SSL_ERROR_RX_RECORD_TOO_LONG，检查 443 端口是否被明文服务占用"),
    ("err-09", "网关升级到 v2.3.4 后旧路由返回 404，2.x 系列变更过路由前缀"),
    ("err-10", "订单 ORD-2024-889923 的支付回调丢失，检查 MQ 死信队列里堆积的消息"),
    ("err-11", "Kafka 消费组报 OffsetOutOfRange，将该分区 offset 重置到 earliest"),
    ("err-12", "MySQL 报 Error 1205 Lock wait timeout，长事务持锁 50 秒触发回滚"),
    ("err-13", "Git push 报 ERR_CONNECTION_RESET，代理拦截了 22 端口，改走 443"),
    ("err-14", "蓝牙适配器报错 Code 43，设备管理器里显示该设备已被禁用"),
    ("err-15", "Docker 启动容器失败：driver failed programming external connectivity on port 8080"),
    ("err-16", "Spark 任务报 Executor lost due to OOM，executor 堆外内存占用超标"),
    ("err-17", "Redis 报 OOM command not allowed，maxmemory 达到上限且淘汰策略为 noeviction"),
    ("err-18", "登录接口报 ERR-AUTH-2048 会话过期，调用 /v2/token/refresh 换取新令牌"),
    ("err-19", "Windows 报 0x00000709 系统打印服务异常，重启 Print Spooler 组件"),
    ("err-20", "Gradle 构建报 Could not resolve all dependencies，仓库签名校验 FAILED"),
    ("err-21", "游戏引擎报 DX11 feature level 10.0 is required，显卡驱动版本过低"),
    ("err-22", "注册中心报 NACOS-503 service unavailable，健康检查线程池被打满"),
    ("err-23", "Flink 作业报 Checkpoint expired，barrier 对齐耗时超过 checkpoint timeout"),
    ("err-24", "硬盘 SMART 05 项 Reallocated Sectors Count 出现警告，尽快备份数据更换硬盘"),
    ("err-25", "编译报 fatal error C1083 找不到头文件，include 路径与工具链版本不匹配"),
    ("col-01", "系统启动耗时过长的常见原因：自启动项过多、磁盘存在坏道或 I/O 瓶颈"),
    ("col-02", "网络带宽不足导致视频播放缓冲，检查路由器 QoS 配置或升级宽带套餐"),
    ("col-03", "设备存储空间不足会导致应用安装失败，清理缓存或把照片迁移到云端"),
    ("col-04", "服务不可用应先确认进程是否存活，再检查负载均衡健康检查的阈值配置"),
    ("col-05", "笔记本散热不良引起处理器降频，表现为运行卡顿，需清理风扇更换硅脂"),
    ("col-06", "文件损坏无法打开，多为写入时进程异常终止，可用磁盘检查工具修复"),
    ("col-07", "无线信号衰减严重导致连接不稳定，调整路由器位置或更换高增益天线"),
    ("col-08", "系统运行内存占用过高，关闭后台驻留进程，必要时增加物理内存条"),
    ("col-09", "键盘输入出现重复字符，多为按键老化粘连，更换键盘或调低重复延迟"),
    ("col-10", "浏览器主页被篡改并弹广告，说明存在恶意扩展，排查后重置浏览器设置"),
    ("col-11", "手机续航时间异常缩短，检查常驻后台的定位服务并限制其唤醒频率"),
    ("col-12", "打印文档排版错乱，缺少对应字体文件导致，安装嵌入字体即可解决"),
    ("col-13", "视频会议画面卡顿延迟高，优先排查上行带宽与摄像头的编码负载"),
    ("col-14", "文件同步后版本冲突，多人协作应基于同一版本修改并手动合并"),
    ("col-15", "邮件附件无法下载，安全网关拦截了大附件，改用文件分享链接"),
    ("col-16", "系统更新后外接屏幕无法被检测到，回退显卡驱动或重新配置输出模式"),
    ("col-17", "应用启动即闪退，查看系统事件日志定位崩溃模块，再决定回退版本"),
    ("col-18", "数据库查询响应时间长，多为缺乏索引的全表扫描，为高频字段补建索引"),
    ("col-19", "网页加载不完整，浏览器缓存与新版资源不一致，强制刷新即可"),
    ("col-20", "运行中频繁自动重启，多为供电老化、输出功率不足，更换更大供电模块"),
    ("col-21", "远程桌面连接频繁掉线，网络丢包率高，建议改用有线并降低画质"),
    ("col-22", "备份任务迟迟未完成，增量备份链断裂后触发了全量备份，需重建备份链"),
    ("col-23", "摄像头画面出现条纹干扰，多为信号线路并行布线引入的干扰，分开走线"),
    ("col-24", "代码仓库拉取耗时很长，平台对出口流量限速，配置代理或切换镜像源"),
    ("col-25", "新显示器字体发虚，多为系统未启用字体平滑渲染，或缩放比例设置不当"),
]


def main():
    connections.connect(host="localhost", port="19530")
    es = Elasticsearch("http://localhost:9200")

    print(f"加载 embedding 模型 {MODEL_NAME}（首次运行会先下载）...")
    model = SentenceTransformer(MODEL_NAME)
    dim = int(model.encode("维度测试").shape[0])
    print(f"模型输出维度 dim={dim}（以实际为准，schema 按它建）")

    # ---- ES 侧 ----
    if es.indices.exists(index=ES_INDEX):
        es.indices.delete(index=ES_INDEX)
    es.indices.create(index=ES_INDEX, mappings={"properties": {
        "doc_id": {"type": "keyword"},
        "text": {"type": "text"},        # 默认 standard 分词器
        "kind": {"type": "keyword"},
    }})
    for doc_id, text in DOCS:
        es.index(index=ES_INDEX, id=doc_id,
                 document={"doc_id": doc_id, "text": text,
                           "kind": doc_id.split("-")[0]})
    es.indices.refresh(index=ES_INDEX)
    print(f"ES 索引 {ES_INDEX} 灌入 {es.count(index=ES_INDEX)['count']} 条")

    # ---- Milvus 侧 ----
    if utility.has_collection(MILVUS_COLLECTION):
        utility.drop_collection(MILVUS_COLLECTION)
    schema = CollectionSchema([
        FieldSchema("doc_id", DataType.VARCHAR, max_length=16, is_primary=True),
        FieldSchema("text", DataType.VARCHAR, max_length=512),
        FieldSchema("vector", DataType.FLOAT_VECTOR, dim=dim),
    ])
    col = Collection(MILVUS_COLLECTION, schema)
    texts = [t for _, t in DOCS]
    vectors = model.encode(texts, normalize_embeddings=True)
    col.insert([[d for d, _ in DOCS], texts, vectors.tolist()])
    col.flush()
    col.create_index(field_name="vector", index_params={
        "index_type": "FLAT", "metric_type": "COSINE", "params": {}})
    col.load()
    print(f"Milvus collection {MILVUS_COLLECTION} 灌入 {col.num_entities} 条"
          f"（FLAT/COSINE，已 load）")
    print("材料就绪。下一步：python scripts/exp17-search.py")


if __name__ == "__main__":
    main()
