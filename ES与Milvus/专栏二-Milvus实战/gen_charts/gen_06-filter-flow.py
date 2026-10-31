# -*- coding: utf-8 -*-
"""第 06 篇配图：post-filter vs 引擎内过滤（pre-filter）流程对比"""
import os
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

BLUE_FILL, BLUE_EDGE = "#e8f0fe", "#4285f4"
RED_FILL, RED_EDGE = "#fce8e6", "#ea4335"
GREEN_FILL, GREEN_EDGE = "#e6f4ea", "#34a853"
YELLOW_FILL, YELLOW_EDGE = "#fff8e1", "#f9ab00"

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
os.makedirs(OUT_DIR, exist_ok=True)


def box(ax, x, y, w, h, text, fc, ec, fontsize=10.5):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06",
                       fc=fc, ec=ec, linewidth=1.8)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fontsize, zorder=5)


def arrow(ax, x1, y, x2):
    a = FancyArrowPatch((x1, y), (x2, y), arrowstyle="-|>",
                        mutation_scale=16, linewidth=1.8, color="#5f6368")
    ax.add_patch(a)


def draw():
    fig, ax = plt.subplots(figsize=(10.6, 5.0))
    ax.set_xlim(0, 13.4)
    ax.set_ylim(0, 5.2)
    ax.axis("off")

    bw, bh = 2.55, 1.15
    xs = [0.25, 3.55, 6.85, 10.15]

    # ---- 上排：post-filter（红）----
    y1 = 3.35
    ax.text(0.25, y1 + bh + 0.28,
            "post-filter：检索后过滤（应用层过滤就是它）",
            fontsize=12, fontweight="bold", color=RED_EDGE)
    box(ax, xs[0], y1, bw, bh, "查询向量", BLUE_FILL, BLUE_EDGE)
    box(ax, xs[1], y1, bw, bh, "ANN 全库检索\n取全局 top-k", RED_FILL, RED_EDGE)
    box(ax, xs[2], y1, bw, bh, "再按 tenant_id\n逐条过滤", RED_FILL, RED_EDGE)
    box(ax, xs[3], y1, bw, bh, "结果剩 0~3 条\n数量不保证", RED_FILL, RED_EDGE)
    for i in range(3):
        arrow(ax, xs[i] + bw + 0.15, y1 + bh / 2, xs[i + 1] - 0.15)
    ax.text(xs[3] + bw / 2, y1 - 0.32,
            "相似的前 k 条可能全在别的租户，过滤完就没了",
            ha="center", fontsize=9.5, color=RED_EDGE)

    # ---- 下排：引擎内过滤（绿）----
    y2 = 0.75
    ax.text(0.25, y2 + bh + 0.28,
            "引擎内过滤（pre-filter）：filter 传进 Milvus，bitset 伴随检索",
            fontsize=12, fontweight="bold", color="#1e7e34")
    box(ax, xs[0], y2, bw, bh, "查询向量\n+ filter 表达式", BLUE_FILL, BLUE_EDGE)
    box(ax, xs[1], y2, bw, bh, "编译成 bitset\n标记允许的行", GREEN_FILL, GREEN_EDGE)
    box(ax, xs[2], y2, bw, bh, "ANN 搜索时\n跳过被排除的行", GREEN_FILL, GREEN_EDGE)
    box(ax, xs[3], y2, bw, bh, "稳定返回 k 条\n（只要够 k 条）", GREEN_FILL, GREEN_EDGE)
    for i in range(3):
        arrow(ax, xs[i] + bw + 0.15, y2 + bh / 2, xs[i + 1] - 0.15)
    ax.text(xs[3] + bw / 2, y2 - 0.32,
            "被排除的行不进结果，但在 HNSW 图上仍可作为路径",
            ha="center", fontsize=9.5, color="#1e7e34")

    fig.savefig(os.path.join(OUT_DIR, "06-filter-flow.png"), dpi=150,
                bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    draw()
    print("done")
