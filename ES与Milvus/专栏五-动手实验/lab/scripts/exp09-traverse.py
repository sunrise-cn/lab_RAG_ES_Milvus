# 实验 09「深分页的墙」遍历演示：PIT + search_after 顺序翻完 30 万条全量
# 思路：开一个 PIT（point in time，把打开那一刻的数据视图冻结成快照），
# 每页拿上一页最后一条的排序值当游标（search_after），一页 10000 条翻到底。
# 运行：先跑 exp09-gen.py 建好材料，再跑 python scripts/exp09-traverse.py
#（先激活 lab/.venv，ES 在 http://localhost:9200）

import time

from elasticsearch import Elasticsearch

ES = Elasticsearch("http://localhost:9200")
INDEX = "exp09_five"
PAGE_SIZE = 10_000   # search_after 没有"页深度"概念，每页都只取 size 条
KEEP_ALIVE = "3m"    # 每次搜索都会给 PIT 续期，两次翻页之间别停超过 3 分钟就行


def main():
    if not ES.indices.exists(index=INDEX):
        raise SystemExit(f"索引 {INDEX} 不存在，先跑 exp09-gen.py 建材料")

    pit_id = ES.open_point_in_time(index=INDEX, keep_alive=KEEP_ALIVE)["id"]
    print(f"PIT 已建立：{pit_id[:24]}...（id 是 base64，很长，截断显示）")

    total = 0
    pages = 0
    last_sort = None
    t0 = time.perf_counter()

    while True:
        params = dict(
            index=INDEX,
            pit={"id": pit_id, "keep_alive": KEEP_ALIVE},
            size=PAGE_SIZE,
            sort=[{"no": "asc"}],
        )
        if last_sort is not None:
            params["search_after"] = last_sort
        resp = ES.search(**params)
        hits = resp["hits"]["hits"]
        if not hits:
            break
        total += len(hits)
        pages += 1
        last_sort = hits[-1]["sort"]
        if pages % 5 == 0:
            print(f"  第 {pages} 页，累计 {total} 条，游标 no={hits[-1]['_source']['no']}")

    elapsed = time.perf_counter() - t0
    print(f"遍历完成：{pages} 页，共 {total} 条，耗时 {elapsed:.1f}s")

    # 关闭 PIT，别让搜索上下文一直挂着占资源。
    # 不同版本的 elasticsearch 客户端参数名不同，两种写法都试一下
    try:
        ES.close_point_in_time(id=pit_id)
    except TypeError:
        ES.close_point_in_time(body={"id": pit_id})
    print("PIT 已关闭")


if __name__ == "__main__":
    main()
