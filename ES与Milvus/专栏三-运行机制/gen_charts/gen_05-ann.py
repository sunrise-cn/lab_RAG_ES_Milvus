# -*- coding: utf-8 -*-
"""第 05 篇 ANN 索引原理 配图：HNSW 多层图、IVF 分桶、PQ 压缩"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

BLUE_F, BLUE_E = "#e8f0fe", "#4285f4"
RED_F, RED_E = "#fce8e6", "#ea4335"
GREEN_F, GREEN_E = "#e6f4ea", "#34a853"
YELLOW_F, YELLOW_E = "#fff8e1", "#f9ab00"
GRAY = "#5f6368"

OUT = r"D:\Documents\ob_new\01 后端\my-doc\ES与Milvus\专栏三-运行机制\assets"


def box(ax, x, y, w, h, text, fc, ec, fs=10, lw=1.4, tc="black", zorder=3):
    ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, facecolor=fc,
                           edgecolor=ec, lw=lw, zorder=zorder))
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, color=tc, zorder=zorder + 1)


def arrow(ax, x1, y1, x2, y2, color, lw=1.6, style="-", zorder=2, ms=12):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color=color, lw=lw, linestyle=style,
                                mutation_scale=ms, shrinkA=0, shrinkB=0), zorder=zorder)


# ---------------------------------------------------------------- 图 1：跳表 vs HNSW
def fig_hnsw():
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8.2))

    # ===== 上：Redis 跳表 =====
    NW, NH = 0.85, 0.42
    ax1.set_xlim(0, 10.6)
    ax1.set_ylim(0.1, 4.25)
    ax1.axis("off")
    ax1.set_title("Redis 跳表：索引的是一维有序链表", fontsize=12, pad=10)

    keys = [3, 7, 12, 19, 25, 34]
    xs = [1.0 + i * 1.55 for i in range(6)]
    lv = {3: 2, 7: 1, 12: 1, 19: 2, 25: 1, 34: 1}
    rows = {2: 3.4, 1: 2.4, 0: 1.4}

    for k, x in zip(keys, xs):
        for l in range(lv[k] + 1):
            y = rows[l]
            hit = (k == 25)
            box(ax1, x, y, NW, NH, str(k),
                YELLOW_F if hit else BLUE_F, YELLOW_E if hit else BLUE_E, fs=9)
        for l in range(lv[k]):
            ax1.plot([x, x], [rows[l] - NH / 2, rows[l + 1] + NH / 2],
                     color=GRAY, lw=0.9, ls=":", zorder=1)

    def row_nodes(l):
        return [(k, x) for k, x in zip(keys, xs) if lv[k] >= l]

    for l in range(3):
        ns = row_nodes(l)
        for (k1, x1), (k2, x2) in zip(ns, ns[1:]):
            arrow(ax1, x1 + NW / 2, rows[l], x2 - NW / 2, rows[l], BLUE_E, lw=1.4)
        ax1.text(0.28, rows[l], f"L{l}", ha="center", va="center", fontsize=9, color=GRAY)
    ax1.text(0.28, 3.95, "head", ha="center", va="center", fontsize=8, color=GRAY)

    # 查找 25 的路径（绿）
    arrow(ax1, 0.45, 3.4, xs[0] - NW / 2, 3.4, GREEN_E, lw=2.2)
    arrow(ax1, xs[0] + NW / 2, 3.4, xs[3] - NW / 2, 3.4, GREEN_E, lw=2.2)
    ax1.plot([xs[3], xs[3]], [3.4 - NH / 2, 2.4 + NH / 2], color=GREEN_E, lw=2.2)
    ax1.plot([xs[3], xs[3]], [2.4 - NH / 2, 1.4 + NH / 2], color=GREEN_E, lw=2.2)
    arrow(ax1, xs[3] + NW / 2, 1.4, xs[4] - NW / 2, 1.4, GREEN_E, lw=2.2)
    ax1.text(5.8, 3.95, "查 25：每层发现“下一个已超过目标”就下沉", fontsize=9, color=GREEN_E)

    ax1.text(0.5, 0.62,
             "像：高层稀疏走大步、底层稠密走小步、随机定层高、近似 O(log N) 定位",
             fontsize=10, color=GRAY)
    ax1.text(0.5, 0.3,
             "底：层间是同一份有序数据的稀疏化，有序性保证每跳安全砍掉一半，O(log N) 有数学保证",
             fontsize=10, color=RED_E)

    # ===== 下：HNSW =====
    NW2, NH2 = 0.6, 0.4
    ax2.set_xlim(0, 10.6)
    ax2.set_ylim(0.1, 4.25)
    ax2.axis("off")
    ax2.set_title("HNSW：索引的是近邻图（向量间没有全序）", fontsize=12, pad=10)

    bot = {"E": 1.0, "n1": 1.75, "C": 2.5, "n2": 3.25, "D": 4.0, "n3": 4.75,
           "B": 5.5, "n4": 6.25, "n5": 7.0, "T": 7.75, "n6": 8.5, "n7": 9.25}
    y0 = 1.4
    mid = {"E": 1.0, "C": 2.5, "D": 4.0, "B": 5.5}
    y1 = 2.4
    top = {"E": 1.0, "D": 4.0}
    y2 = 3.4

    order = list(bot.keys())
    for a, b in zip(order, order[1:]):
        ax2.plot([bot[a], bot[b]], [y0, y0], color=BLUE_E, lw=1.0, zorder=1)
    for a, b in [("E", "n2"), ("n1", "C"), ("C", "n3"), ("D", "n4"), ("n3", "B"),
                 ("B", "n5"), ("n4", "n5"), ("n5", "T"), ("T", "n7"), ("n2", "D")]:
        ax2.plot([bot[a], bot[b]], [y0, y0], color=BLUE_E, lw=1.0, zorder=1)
    mo = list(mid.keys())
    for a, b in zip(mo, mo[1:]):
        ax2.plot([mid[a], mid[b]], [y1, y1], color=BLUE_E, lw=1.2, zorder=1)
    ax2.plot([mid["E"], mid["D"]], [y1, y1], color=BLUE_E, lw=1.2, zorder=1)
    ax2.plot([top["E"], top["D"]], [y2, y2], color=BLUE_E, lw=1.4, zorder=1)

    for k, x in mid.items():
        ax2.plot([x, x], [y0 + NH2 / 2, y1 - NH2 / 2], color=GRAY, lw=0.9, ls=":", zorder=1)
    for k, x in top.items():
        ax2.plot([x, x], [y1 + NH2 / 2, y2 - NH2 / 2], color=GRAY, lw=0.9, ls=":", zorder=1)

    path_nodes = {"E", "D", "B"}
    for k, x in bot.items():
        if k == "T":
            box(ax2, x, y0, NW2, NH2, k, YELLOW_F, YELLOW_E, fs=8)
        elif k in path_nodes:
            box(ax2, x, y0, NW2, NH2, k, GREEN_F, GREEN_E, fs=8)
        else:
            box(ax2, x, y0, NW2, NH2, k, BLUE_F, BLUE_E, fs=8)
    for k, x in mid.items():
        if k in path_nodes:
            box(ax2, x, y1, NW2, NH2, k, GREEN_F, GREEN_E, fs=8)
        else:
            box(ax2, x, y1, NW2, NH2, k, BLUE_F, BLUE_E, fs=8)
    for k, x in top.items():
        box(ax2, x, y2, NW2, NH2, k, GREEN_F, GREEN_E, fs=8)
    for l, y in [(2, y2), (1, y1), (0, y0)]:
        ax2.text(0.25, y, f"L{l}", ha="center", va="center", fontsize=9, color=GRAY)
    ax2.text(0.25, 3.95, "入口", ha="center", va="center", fontsize=8, color=GRAY)
    ax2.text(bot["T"], y0 - 0.42, "查询目标", ha="center", fontsize=9, color=YELLOW_E)

    # 查询路径（绿）：入口→E→D（顶层）→下沉→B（中间层）→下沉→T（底层）
    arrow(ax2, 0.45, y2, top["E"] - NW2 / 2, y2, GREEN_E, lw=2.2)
    arrow(ax2, top["E"] + NW2 / 2, y2, top["D"] - NW2 / 2, y2, GREEN_E, lw=2.2)
    ax2.plot([top["D"], top["D"]], [y2 - NH2 / 2, y1 + NH2 / 2], color=GREEN_E, lw=2.2)
    arrow(ax2, mid["D"] + NW2 / 2, y1, mid["B"] - NW2 / 2, y1, GREEN_E, lw=2.2)
    ax2.plot([mid["B"], mid["B"]], [y1 - NH2 / 2, y0 + NH2 / 2], color=GREEN_E, lw=2.2)
    for a, b in [("B", "n5"), ("n5", "T")]:
        arrow(ax2, bot[a] + NW2 / 2, y0, bot[b] - NW2 / 2, y0, GREEN_E, lw=2.2)
    ax2.text(5.2, 3.95, "贪心：每步走向邻居里离查询更近的，没有单调性保证", fontsize=9, color=GREEN_E)

    ax2.text(0.5, 0.62,
             "本质不同：高层不是“每隔几个取一个”，是随机抽上去的节点 + 恰好更长的近邻边",
             fontsize=10, color=GRAY)
    ax2.text(0.5, 0.3,
             "底：无全序可依，对数复杂度靠图质量撑着（M、ef_construction），没有数学保证",
             fontsize=10, color=RED_E)

    fig.tight_layout()
    fig.savefig(OUT + r"\05-hnsw.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------- 图 2：IVF 分桶
def fig_ivf():
    rng = np.random.default_rng(42)
    fig, ax = plt.subplots(figsize=(10, 6))

    centers = np.array([[2.0, 7.0], [5.0, 8.0], [8.2, 7.0],
                        [2.6, 3.1], [5.4, 3.5], [8.6, 3.3]])
    pts = []
    for c in centers:
        pts.append(c + rng.normal(0, 0.55, size=(14, 2)))
    pts = np.vstack(pts)

    query = np.array([5.15, 5.6])
    d = np.linalg.norm(centers - query, axis=1)
    order = np.argsort(d)
    scan = set(order[:2])  # nprobe = 2

    for i, c in enumerate(centers):
        if i in scan:
            circ = Circle(c, 1.4, facecolor=GREEN_F, edgecolor=GREEN_E,
                          lw=1.8, alpha=0.55, zorder=1)
        else:
            circ = Circle(c, 1.4, facecolor=BLUE_F, edgecolor=BLUE_E,
                          lw=1.0, alpha=0.30, zorder=1)
        ax.add_patch(circ)

    for i in range(6):
        seg = pts[i * 14:(i + 1) * 14]
        col = GREEN_E if i in scan else BLUE_E
        ax.scatter(seg[:, 0], seg[:, 1], s=16, color=col, zorder=2)
    ax.scatter(centers[:, 0], centers[:, 1], marker="x", s=90, c="black",
               lw=1.6, zorder=3, label="簇心（k-means 质心）")
    ax.scatter([query[0]], [query[1]], marker="^", s=150, c=RED_E, zorder=4, label="查询向量")

    for i in sorted(scan):
        ax.plot([query[0], centers[i, 0]], [query[1], centers[i, 1]],
                ls="--", color=GREEN_E, lw=1.8, zorder=3)
    ax.plot([query[0], centers[order[2], 0]], [query[1], centers[order[2], 1]],
            ls="--", color=GRAY, lw=1.2, zorder=3)

    lab = dict(fontsize=10, ha="center", va="center", zorder=5,
               bbox=dict(boxstyle="round,pad=0.25", facecolor="white",
                         edgecolor="none", alpha=0.85))
    ax.text(centers[1, 0], centers[1, 1] - 0.85, "桶 2\n（扫）", color=GREEN_E, **lab)
    ax.text(centers[4, 0], centers[4, 1] - 0.85, "桶 5\n（扫）", color=GREEN_E, **lab)
    ax.text(centers[order[2], 0], centers[order[2], 1] - 0.85,
            "第 3 近的桶\n整体跳过", color=GRAY, **lab)

    steps = ("① 查询点与全部 6 个簇心算距离（nlist 次，很便宜）\n"
             "② 挑最近的 nprobe=2 个桶（绿色）\n"
             "③ 只在桶内暴力扫，其余桶整体跳过")
    ax.text(0.02, 0.02, steps, transform=ax.transAxes, fontsize=10.5, va="bottom",
            bbox=dict(boxstyle="round,pad=0.5", facecolor=YELLOW_F, edgecolor=YELLOW_E, lw=1.4))

    ax.set_xlim(0, 11)
    ax.set_ylim(0.5, 10.0)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("IVF：k-means 分桶，只扫离查询最近的 nprobe 个桶", fontsize=12)
    ax.legend(loc="upper right", fontsize=9, frameon=False)
    fig.savefig(OUT + r"\05-ivf.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------- 图 3：PQ 压缩
def fig_pq():
    fig, ax = plt.subplots(figsize=(10, 5.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5.4)
    ax.axis("off")

    # 原始向量条（示意切成 8 段）
    seg_colors = ["#c3d7f5", "#a8c6f0"] * 4
    bx, by, bw, bh = 0.4, 3.7, 2.4, 0.5
    for i in range(8):
        ax.add_patch(Rectangle((bx + i * bw / 8, by), bw / 8, bh,
                               facecolor=seg_colors[i], edgecolor=BLUE_E, lw=1.0))
    ax.text(bx + bw / 2, by + bh + 0.24,
            "原始向量：768 维 float32\n= 3072 字节", ha="center", fontsize=10)

    box(ax, 4.7, 3.95, 3.0, 0.95, "切成 m 段，每段独立\nk-means 聚 256 个质心",
        BLUE_F, BLUE_E, fs=10)
    box(ax, 8.2, 3.95, 3.0, 0.95, "编码：m 字节\n（每段 = 质心编号）", GREEN_F, GREEN_E, fs=10)

    arrow(ax, bx + bw + 0.15, 3.95, 4.7 - 1.55, 3.95, GRAY, lw=1.6)
    arrow(ax, 4.7 + 1.55, 3.95, 8.2 - 1.55, 3.95, GRAY, lw=1.6)

    # 下方：单段放大示例
    box(ax, 1.9, 1.85, 3.0, 1.15, "单段放大：某一段（8 维）\n的码本 = 256 个质心向量", BLUE_F, BLUE_E, fs=10)
    box(ax, 6.3, 1.85, 3.6, 1.15, "这一段只存 1 个字节：\n最近质心的编号（如 0x5C）", GREEN_F, GREEN_E, fs=10)
    arrow(ax, 3.45, 1.85, 4.45, 1.85, GRAY, lw=1.6)
    ax.plot([4.7, 4.7], [3.45, 3.0], color=GRAY, lw=1.0, ls=":")
    ax.plot([4.7, 1.9], [3.0, 2.45], color=GRAY, lw=1.0, ls=":")

    ax.text(5.0, 0.85,
            "查询距离：查 m × 256 的距离表再求和，浮点乘加变成查表",
            ha="center", fontsize=10.5,
            bbox=dict(boxstyle="round,pad=0.45", facecolor=YELLOW_F, edgecolor=YELLOW_E, lw=1.4))
    ax.text(5.0, 0.3, "代价：量化有损，编码距离只是近似 → 召回率下降，常配 rerank 补救",
            ha="center", fontsize=10.5, color=RED_E)
    ax.text(9.3, 4.9, "约 32 倍压缩", ha="center", fontsize=11, color=GREEN_E, weight="bold")

    ax.set_title("PQ 乘积量化：用“最近的质心编号”代替原始向量", fontsize=12)
    fig.savefig(OUT + r"\05-pq.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


fig_hnsw()
fig_ivf()
fig_pq()
print("done")
