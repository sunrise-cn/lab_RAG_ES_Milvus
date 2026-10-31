# -*- coding: utf-8 -*-
"""专栏三 03 查询执行流程 配图（2 张）"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import os

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

BLUE_F, BLUE_E = "#e8f0fe", "#4285f4"
RED_F, RED_E = "#fce8e6", "#ea4335"
GREEN_F, GREEN_E = "#e6f4ea", "#34a853"
YELL_F, YELL_E = "#fff8e1", "#f9ab00"
GRAY_F, GRAY_E = "#f1f3f4", "#9aa0a6"

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
os.makedirs(OUT, exist_ok=True)


def box(ax, x, y, w, h, text, fc, ec, fs=9.5, bold=False, ls="-", tc=None):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05",
                                fc=fc, ec=ec, lw=1.5, linestyle=ls))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, fontweight="bold" if bold else "normal",
            color=tc or "#202124")


def arrow(ax, x1, y1, x2, y2, color="#5f6368", lw=1.6):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                 mutation_scale=14, color=color, lw=lw))


# ============ 图 1：QUERY_THEN_FETCH 两阶段 ============
fig, ax = plt.subplots(figsize=(10.4, 9.8))
ax.set_xlim(0, 12)
ax.set_ylim(0, 12)
ax.axis("off")

box(ax, 4.9, 11.0, 2.2, 0.8, "客户端", YELL_F, YELL_E, fs=11, bold=True)
arrow(ax, 6.0, 10.95, 6.0, 10.3, color="#ea4335", lw=2.0)
ax.text(6.25, 10.6, "① 搜索请求（from=0, size=10）", fontsize=9.5, color="#5f6368")

# QUERY 阶段
ax.add_patch(FancyBboxPatch((0.4, 7.0), 11.2, 3.15, boxstyle="round,pad=0.04",
                            fc="#f8f9fa", ec="#9aa0a6", lw=1.1, linestyle="--"))
ax.text(0.6, 9.9, "QUERY 阶段：只要 doc id 和分数", fontsize=10.5,
        color="#5f6368", fontweight="bold")

box(ax, 1.0, 7.6, 2.6, 1.6, "协调节点\n（收到请求的\n任意节点）", BLUE_F, BLUE_E, fs=10)
box(ax, 6.2, 9.0, 2.6, 0.85, "主分片 0", BLUE_F, BLUE_E, fs=10)
box(ax, 6.2, 8.0, 2.6, 0.85, "主分片 1", BLUE_F, BLUE_E, fs=10)
box(ax, 6.2, 7.05, 2.6, 0.85, "主分片 2", BLUE_F, BLUE_E, fs=10)

arrow(ax, 3.65, 8.85, 6.15, 9.42, color="#4285f4")
arrow(ax, 3.65, 8.4, 6.15, 8.42, color="#4285f4")
arrow(ax, 3.65, 7.95, 6.15, 7.47, color="#4285f4")
ax.text(4.7, 9.85, "② 广播查询", fontsize=9.5, color="#4285f4", ha="center")

arrow(ax, 6.15, 7.25, 3.7, 7.7)
ax.text(4.5, 7.1, "③ 回 doc id + _score\n（各分片前 from+size 条，无 _source）",
        fontsize=9, ha="center", color="#5f6368")

# 归并
arrow(ax, 6.9, 6.95, 6.9, 6.5, color="#ea4335", lw=2.0)
box(ax, 3.3, 5.25, 5.4, 1.2,
    "④ 归并排序：局部 top N → 全局 top 10\n（谁上榜、各自在哪个分片）",
    YELL_F, YELL_E, fs=9.5, bold=True)

# FETCH 阶段
ax.add_patch(FancyBboxPatch((0.4, 1.7), 11.2, 3.15, boxstyle="round,pad=0.04",
                            fc="#f8f9fa", ec="#9aa0a6", lw=1.1, linestyle="--"))
ax.text(0.6, 4.6, "FETCH 阶段：只为上榜文档取 _source", fontsize=10.5,
        color="#5f6368", fontweight="bold")

box(ax, 1.0, 2.3, 2.6, 1.6, "协调节点", BLUE_F, BLUE_E, fs=10)
box(ax, 5.3, 3.4, 3.0, 0.9, "分片 1：3 篇上榜", GREEN_F, GREEN_E, fs=9.5)
box(ax, 5.3, 2.2, 3.0, 0.9, "分片 2：7 篇上榜", GREEN_F, GREEN_E, fs=9.5)
box(ax, 8.9, 2.75, 2.5, 0.95, "分片 0：0 篇上榜\n（不打扰）", GRAY_F, GRAY_E, fs=9, ls="--")

arrow(ax, 3.65, 3.35, 5.25, 3.85, color="#34a853")
arrow(ax, 3.65, 2.95, 5.25, 2.65, color="#34a853")
ax.text(4.35, 4.15, "⑤ 批量取 _source", fontsize=9.5, color="#34a853", ha="center")

arrow(ax, 6.0, 1.65, 6.0, 1.2, color="#ea4335", lw=2.0)
box(ax, 4.3, 0.15, 3.4, 1.0, "⑥ 客户端拿到 top 10", GREEN_F, GREEN_E, fs=10, bold=True)

plt.tight_layout()
plt.savefig(os.path.join(OUT, "03-query-then-fetch.png"), dpi=150, bbox_inches="tight")
plt.close(fig)

# ============ 图 2：分布式打分与 DFS ============
fig, ax = plt.subplots(figsize=(10.6, 7.6))
ax.set_xlim(0, 12)
ax.set_ylim(0, 10.4)
ax.axis("off")

ax.text(6.0, 10.05, "QUERY_THEN_FETCH：各分片用各自的尺子", fontsize=12,
        fontweight="bold", ha="center", color="#c5221f")

box(ax, 0.5, 7.6, 5.1, 2.0,
    "分片 0：「退款」docFreq = 100 万\n含「退款」的文档 A\nscore = 8.1",
    RED_F, RED_E, fs=10)
box(ax, 6.4, 7.6, 5.1, 2.0,
    "分片 1：「退款」docFreq = 10 万\n内容相同的文档 B\nscore = 12.7",
    RED_F, RED_E, fs=10)

box(ax, 0.5, 6.4, 11.0, 0.95,
    "idf：词越常见越不值钱。同一篇文档落在哪个分片全凭 hash →\n分数不可比，第一阶段归并出的排序可能错乱",
    YELL_F, YELL_E, fs=9.5)

ax.plot([0.5, 11.5], [6.1, 6.1], color="#bdc1c6", lw=1.0, linestyle="--")

ax.text(6.0, 5.6, "DFS_QUERY_THEN_FETCH：先统一尺子，再打分", fontsize=12,
        fontweight="bold", ha="center", color="#137333")

box(ax, 0.5, 2.9, 3.5, 2.0,
    "第 0 轮（DFS）\n各分片上报查询词的\n统计量（docFreq 等）",
    GREEN_F, GREEN_E, fs=9.5)
box(ax, 4.6, 2.9, 3.5, 2.0,
    "协调节点汇总\n全局统计随查询下发\n所有分片同一把尺子",
    GREEN_F, GREEN_E, fs=9.5)
box(ax, 8.7, 2.9, 2.8, 2.0,
    "照常执行\nQUERY → FETCH\n分数全局可比",
    BLUE_F, BLUE_E, fs=9.5)

arrow(ax, 4.05, 3.9, 4.55, 3.9, color="#34a853")
arrow(ax, 8.15, 3.9, 8.65, 3.9, color="#34a853")

box(ax, 0.5, 1.0, 11.0, 1.4,
    "修的是分数可比性；代价：每个查询多一整轮网络往返（三阶段 vs 两阶段）\n更根本的解法：别过度分片，让每个分片的局部统计 ≈ 全局统计的 1/N",
    YELL_F, YELL_E, fs=9.5)

plt.tight_layout()
plt.savefig(os.path.join(OUT, "03-dfs-scoring.png"), dpi=150, bbox_inches="tight")
plt.close(fig)

print("done")
