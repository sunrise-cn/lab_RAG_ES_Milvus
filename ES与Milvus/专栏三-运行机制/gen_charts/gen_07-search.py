# -*- coding: utf-8 -*-
"""第 07 篇 一次检索的完整旅程 配图：请求旅程、多路归并"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

BLUE_F, BLUE_E = "#e8f0fe", "#4285f4"
RED_F, RED_E = "#fce8e6", "#ea4335"
GREEN_F, GREEN_E = "#e6f4ea", "#34a853"
YELLOW_F, YELLOW_E = "#fff8e1", "#f9ab00"
GRAY = "#5f6368"

OUT = r"D:\Documents\ob_new\01 后端\my-doc\ES与Milvus\专栏三-运行机制\assets"


def box(ax, x, y, w, h, text, fc, ec, fs=9.5, lw=1.4, zorder=3):
    ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, facecolor=fc,
                           edgecolor=ec, lw=lw, zorder=zorder))
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, zorder=zorder + 1)


def arrow(ax, x1, y1, x2, y2, color, lw=1.6, style="-", zorder=2, ms=13):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color=color, lw=lw, linestyle=style,
                                mutation_scale=ms, shrinkA=0, shrinkB=0), zorder=zorder)


def alabel(ax, x, y, text, color, fs=8.5, ha="center"):
    ax.text(x, y, text, ha=ha, va="center", fontsize=fs, color=color, zorder=6,
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                      edgecolor="none", alpha=0.85))


# ---------------------------------------------------------------- 图 1：请求旅程
def fig_flow():
    fig, ax = plt.subplots(figsize=(10, 7.2))
    ax.set_xlim(0, 12.4)
    ax.set_ylim(0, 10.3)
    ax.axis("off")
    ax.set_title("一条 search 请求的旅程", fontsize=13, pad=12)

    box(ax, 6, 9.5, 1.8, 0.7, "客户端", BLUE_F, BLUE_E)
    box(ax, 5.2, 8.2, 2.6, 0.8, "Proxy\n（无状态网关）", BLUE_F, BLUE_E, fs=9)
    box(ax, 10.2, 8.2, 3.2, 0.85, "Query Coord\n（segment 分配表）", BLUE_F, BLUE_E, fs=9)
    box(ax, 1.7, 8.2, 2.9, 0.85, "consistency level\n出发前生效", YELLOW_F, YELLOW_E, fs=8.5)

    arrow(ax, 6, 9.15, 6, 8.62, GRAY, lw=1.6)
    alabel(ax, 8.3, 9.0, "search(vec, top-k, ef, expr)", GRAY, ha="center")
    arrow(ax, 6.5, 8.2, 8.6, 8.2, GRAY, lw=1.4, style="--")
    alabel(ax, 7.55, 8.62, "① 问路由", GRAY)

    qn_txt = ("Query Node {}\nsealed ×3：走索引\n（ef/nprobe 生效处）\n"
              "growing ×1：暴力扫\nexpr → bitset 掩码")
    qxs = [1.85, 5.75, 9.65]
    for i, qx in enumerate(qxs):
        box(ax, qx, 5.75, 3.4, 1.75, qn_txt.format(i + 1), BLUE_F, BLUE_E, fs=8)
        arrow(ax, 5.2, 7.8, qx, 6.65, GRAY, lw=1.6)
    alabel(ax, 7.6, 7.3, "② 按 shard 扇出（并行广播）", GRAY)

    box(ax, 6, 2.9, 5.6, 0.9, "③ Proxy：多路归并（小顶堆）→ 全局 top-k",
        GREEN_F, GREEN_E, fs=10)
    for qx in qxs:
        arrow(ax, qx, 4.87, qx if qx == 5.75 else (4.1 if qx < 5 else 7.9), 3.37,
              GREEN_E, lw=1.6)
    alabel(ax, 6.55, 4.25, "局部 top-k", GREEN_E, ha="left")

    box(ax, 6, 1.2, 6.4, 0.85,
        "④ 返回 top-k + output_fields\n（字段随局部结果带回，无二次回表）", GREEN_F, GREEN_E, fs=9)
    arrow(ax, 6, 2.45, 6, 1.65, GRAY, lw=1.6)

    fig.savefig(OUT + r"\07-search-flow.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------- 图 2：多路归并
def fig_merge():
    fig, ax = plt.subplots(figsize=(10, 5.6))
    ax.set_xlim(0, 12.6)
    ax.set_ylim(0, 5.7)
    ax.axis("off")
    ax.set_title("归并 = 归并排序的 k 路合并：R 路局部 top-k → 全局 top-k", fontsize=12, pad=10)

    lists = {
        "路 A（节点 1）": [0.12, 0.25, 0.31, 0.47, 0.52],
        "路 B（节点 2）": [0.08, 0.19, 0.33, 0.40, 0.61],
        "路 C（节点 3）": [0.15, 0.22, 0.29, 0.38, 0.55],
    }
    xs = [1.3, 2.9, 4.5]
    top_y, step, bw, bh = 4.1, 0.72, 1.15, 0.55
    channels = [4.98, 4.73, 4.48]
    for (title, vals), x, ch in zip(lists.items(), xs, channels):
        for j, v in enumerate(vals):
            y = top_y - j * step
            head = (j == 0)
            box(ax, x, y, bw, bh, f"{v:.2f}",
                GREEN_F if head else BLUE_F, GREEN_E if head else BLUE_E, fs=9)
        ax.text(x, 0.55, title, ha="center", fontsize=9.5, color=GRAY)
        # 队头 → 垂直短柄 → 水平通道（高于所有方框）→ 堆
        ax.plot([x, x], [top_y + bh / 2, ch], color=GREEN_E, lw=1.5, zorder=2)
        arrow(ax, x, ch, 7.2, ch, GREEN_E, lw=1.5)

    box(ax, 8.65, 4.3, 2.8, 1.9, "小顶堆\n\n只看各路队头\n每次取最小出队\n（够 k 条即停）",
        YELLOW_F, YELLOW_E, fs=9.5)

    outs = [("0.08 ← B1", 4.3), ("0.12 ← A1", 3.55), ("0.15 ← C1", 2.8)]
    for (t, y), sy in zip(outs, [4.55, 4.3, 4.05]):
        box(ax, 11.5, y, 1.9, 0.58, t, GREEN_F, GREEN_E, fs=9)
        arrow(ax, 10.05, sy, 10.5, y, GRAY, lw=1.5)
    ax.text(11.5, 4.88, "全局 top-3", ha="center", fontsize=10, color=GREEN_E)

    ax.text(8.2, 1.15,
            "距离全局可比：全局 top-k 的任何一行，\n必然在其所在节点的局部 top-k 里 → 敢只传每路前 k 条",
            ha="center", fontsize=9.5,
            bbox=dict(boxstyle="round,pad=0.4", facecolor=YELLOW_F, edgecolor=YELLOW_E, lw=1.4))
    ax.text(2.9, 0.15, "已出队的队头由该路下一条顶上", ha="center", fontsize=8.5, color=GRAY)

    fig.savefig(OUT + r"\07-merge.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


fig_flow()
fig_merge()
print("done")
