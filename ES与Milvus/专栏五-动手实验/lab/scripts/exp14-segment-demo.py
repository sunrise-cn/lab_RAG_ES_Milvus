"""实验 14 补充：insert 一批，去 attu 看 growing segment，flush 后看它变 sealed。"""
from pathlib import Path

import numpy as np
from pymilvus import Collection, connections

LAB = Path(__file__).resolve().parent.parent
DATA = LAB / "data"

COLLECTION = "exp14"
BATCH = 100
OFFSET = 3400          # 用 gen 预留的最后一批


def main():
    connections.connect(host="localhost", port="19530")
    data = np.load(DATA / "exp14.npz")
    ids = data["ids"][OFFSET:OFFSET + BATCH]
    vecs = data["vectors"][OFFSET:OFFSET + BATCH]

    col = Collection(COLLECTION)
    mr = col.insert([ids.tolist(), vecs.tolist()])
    print(f"insert 完成：insert_count={mr.insert_count}")
    print("现在去 attu（http://localhost:3000）打开 Collection exp14 的 Segments 页，")
    print("找 state 为 Growing 的那一行，记下它的 rows。看完回来按回车，我会执行 flush……")
    input()
    col.flush()
    print("flush 完成。回 attu 刷新 Segments 页：刚才那行 Growing 变成 Sealed/Flushed。")
    print("（页面名和状态用词以 attu v2.4 实际界面为准）")


if __name__ == "__main__":
    main()
