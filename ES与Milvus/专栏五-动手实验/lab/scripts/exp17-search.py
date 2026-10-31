"""实验 17 主测量：双路检索 + 手写 RRF + 分数相加对照组。

对每个查询做四件事：
  1. ES BM25 检索 top-5
  2. Milvus 向量检索 top-5（COSINE，distance 越小越相似）
  3. RRF 合并：score = Σ 1/(k + rank)，k=60，只用排名不用分数
  4. 对照组：两路分数各自 min-max 归一化后直接相加

运行方式（先激活 venv）：
  cd lab && source .venv/Scripts/activate
  python scripts/exp17-search.py
"""
from elasticsearch import Elasticsearch
from pymilvus import Collection, connections
from sentence_transformers import SentenceTransformer

ES_INDEX = "exp17-docs"
MILVUS_COLLECTION = "exp17-docs"
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
TOPK = 5
RRF_K = 60   # RRF 惯用值：第 1 名 1/61、第 2 名 1/62，压低单路头部的垄断性

QUERIES = [
    "报错 ERR-1002 连接超时怎么处理",   # 偏精确词：错误码是 BM25 的独门武器
    "RTX-4090 显卡驱动老是崩溃",        # 偏精确词：型号靠精确匹配
    "电脑开机特别慢要好几分钟",          # 偏口语：和标准术语文档几乎零字面重叠
    "网太卡了视频一直转圈",              # 偏口语：共享"视频/网"等字，两路都能沾边
]


def tag(doc_id):
    return "精确词" if doc_id.startswith("err-") else "口语类"


def brief(text):
    return text if len(text) <= 18 else text[:18] + "…"


def es_search(es, query):
    resp = es.search(index=ES_INDEX, query={"match": {"text": query}}, size=TOPK)
    return [(h["_id"], h["_score"], h["_source"]["text"])
            for h in resp["hits"]["hits"]]


def mv_search(col, model, query):
    emb = model.encode([query], normalize_embeddings=True)[0]
    hits = col.search(data=[emb.tolist()], anns_field="vector",
                      param={"metric_type": "COSINE", "params": {}},
                      limit=TOPK, output_fields=["text"])[0]
    return [(str(h.id), float(h.distance), h.entity.get("text")) for h in hits]


def rrf_fuse(*routes):
    """routes: 每路一个 [(doc_id, score, text)]，只用排名：Σ 1/(k + rank)。"""
    scores = {}
    for route in routes:
        for rank, item in enumerate(route, start=1):
            doc_id = item[0]
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (RRF_K + rank)
    return sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))


def minmax_norm(pairs):
    """[(doc_id, score)]（score 越大越好）→ {doc_id: 归一化分数}。"""
    if not pairs:
        return {}
    vals = [s for _, s in pairs]
    lo, hi = min(vals), max(vals)
    if hi == lo:
        return {d: 0.5 for d, _ in pairs}
    return {d: (s - lo) / (hi - lo) for d, s in pairs}


def sum_fuse(es_route, mv_route):
    """对照组：min-max 归一化后直接相加。缺某一路记 0。"""
    es_norm = minmax_norm([(d, s) for d, s, _ in es_route])
    # distance 越小越好，取负变成"越大越好"再归一化
    mv_norm = minmax_norm([(d, -s) for d, s, _ in mv_route])
    scores = {}
    for doc_id in set(es_norm) | set(mv_norm):
        scores[doc_id] = es_norm.get(doc_id, 0.0) + mv_norm.get(doc_id, 0.0)
    return sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))


def show(title, items):
    print(f"[{title}]")
    for rank, item in enumerate(items, start=1):
        if len(item) == 2:                       # 融合结果 (doc_id, score)
            doc_id, score = item
            print(f"  {rank}. {doc_id}({tag(doc_id)})  {score:.4f}")
        else:                                    # 单路结果 (doc_id, score, text)
            doc_id, score, text = item
            print(f"  {rank}. {doc_id}({tag(doc_id)})  {score:.3f}  {brief(text)}")


def main():
    connections.connect(host="localhost", port="19530")
    es = Elasticsearch("http://localhost:9200")
    model = SentenceTransformer(MODEL_NAME)
    col = Collection(MILVUS_COLLECTION)

    for query in QUERIES:
        print(f"\n================ {query} ================")
        es_route = es_search(es, query)
        mv_route = mv_search(col, model, query)
        show("BM25 路", es_route)
        show("向量路", mv_route)
        show(f"RRF 合并（k={RRF_K}）", rrf_fuse(es_route, mv_route))
        show("对照组：归一化相加", sum_fuse(es_route, mv_route))


if __name__ == "__main__":
    main()
