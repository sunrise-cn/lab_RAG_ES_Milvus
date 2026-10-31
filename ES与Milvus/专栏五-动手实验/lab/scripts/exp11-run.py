# 实验 11「写入吞吐调优」吞吐矩阵：bulk 批大小 × refresh_interval，共 8 个组合
# 每个组合把同一份 30 万条数据（exp11-docs.jsonl，由 exp11-gen.py 生成）
# 灌进自己的独立索引（exp11_b批数_r模式），量导入耗时、算吞吐。
# 运行：先跑 exp11-gen.py，再跑 python scripts/exp11-run.py
#（先激活 lab/.venv，ES 在 http://localhost:9200；全跑完约 5~10 分钟）

import json
import time
from pathlib import Path

from elasticsearch import Elasticsearch, helpers

ES = Elasticsearch("http://localhost:9200")
TOTAL = 300_000
BATCH_SIZES = [200, 1000, 5000, 20000]
REFRESH_MODES = [("1s", "r1s"), ("-1", "roff")]  # (refresh_interval 值, 索引名后缀)
DATA = Path(__file__).resolve().parent.parent / "data" / "exp11-docs.jsonl"

MAPPINGS = {
    "properties": {
        "no": {"type": "long"},
        "text": {"type": "text"},
    }
}


def load_docs():
    docs = []
    with DATA.open(encoding="utf-8") as f:
        for line in f:
            docs.append(json.loads(line))
    if len(docs) != TOTAL:
        raise SystemExit(f"数据文件应为 {TOTAL} 条，实际 {len(docs)} 条，先跑 exp11-gen.py")
    return docs


def actions(index, docs):
    # 不给 _id：让 ES 自动生成，走 append 优化，比自定义 _id 略快
    for doc in docs:
        yield {"_index": index, "_source": doc}


def new_index(index, refresh_interval):
    if ES.indices.exists(index=index):
        ES.indices.delete(index=index)
    ES.indices.create(
        index=index,
        mappings=MAPPINGS,
        settings={
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "refresh_interval": refresh_interval,
        },
    )


def run_combo(docs, batch, refresh_interval, suffix):
    index = f"exp11_b{batch}_{suffix}"
    new_index(index, refresh_interval)

    t0 = time.perf_counter()
    ok, _ = helpers.bulk(ES, actions(index, docs), chunk_size=batch)
    write_s = time.perf_counter() - t0

    t1 = time.perf_counter()
    ES.indices.refresh(index=index)
    refresh_s = time.perf_counter() - t1

    count = ES.count(index=index)["count"]
    flag = "OK" if count == ok == TOTAL else "异常!请检查"
    print(f"{index:22} 批 {batch:5}  refresh {refresh_interval:>2}  "
          f"导入 {write_s:6.1f}s  吞吐 {TOTAL / write_s:7.0f} 条/秒  "
          f"末次 refresh {refresh_s:5.1f}s  count {count} {flag}")
    return index, write_s


def warmup(docs):
    """预热：把 JVM 编译和页缓存拉热，让 8 个组合在同一个起跑线上。"""
    index = "exp11_warm"
    new_index(index, "-1")
    helpers.bulk(ES, actions(index, docs[:50_000]), chunk_size=1000)
    ES.indices.delete(index=index)
    print("预热完成（5 万条，已删）")


def main():
    if not DATA.exists():
        raise SystemExit(f"数据文件不存在：{DATA}，先跑 exp11-gen.py")
    docs = load_docs()
    print(f"数据加载完成：{len(docs)} 条")
    warmup(docs)
    print()

    results = []
    for refresh_interval, suffix in REFRESH_MODES:
        for batch in BATCH_SIZES:
            results.append(run_combo(docs, batch, refresh_interval, suffix))

    print()
    fastest = min(results, key=lambda r: r[1])
    slowest = max(results, key=lambda r: r[1])
    print(f"最快：{fastest[0]}（{fastest[1]:.1f}s）  "
          f"最慢：{slowest[0]}（{slowest[1]:.1f}s）  "
          f"相差 {slowest[1] / fastest[1]:.1f} 倍")
    print("（绝对数值随机器和当时状态浮动，看相对关系）")


if __name__ == "__main__":
    main()
