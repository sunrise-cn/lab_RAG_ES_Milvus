# -*- coding: utf-8 -*-
"""专栏三 04 集群与分布式 配图（2 张）"""
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


# ============ 图 1：分片路由 ============
fig, ax = plt.subplots(figsize=(10.4, 7.2))
ax.set_xlim(0, 12)
ax.set_ylim(0, 9)
ax.axis("off")

ax.text(6.0, 8.65, "分片路由：同一个模子", fontsize=13, fontweight="bold", ha="center")

# 左：ES
ax.add_patch(FancyBboxPatch((0.3, 4.3), 5.5, 3.9, boxstyle="round,pad=0.04",
                            fc="#f8f9fa", ec="#9aa0a6", lw=1.1, linestyle="--"))
ax.text(0.5, 7.95, "ES", fontsize=11, color="#5f6368", fontweight="bold")
box(ax, 0.6, 6.9, 4.9, 0.8, "文档 _id = \"abc123\"", YELL_F, YELL_E, fs=10)
arrow(ax, 3.05, 6.85, 3.05, 6.45)
box(ax, 0.6, 5.7, 4.9, 0.7, "hash(\"abc123\") % 3 = 2", BLUE_F, BLUE_E, fs=10)
arrow(ax, 3.05, 5.65, 3.05, 5.25)
box(ax, 0.6, 4.45, 1.5, 0.8, "主分片 0", BLUE_F, BLUE_E, fs=9)
box(ax, 2.3, 4.45, 1.5, 0.8, "主分片 1", BLUE_F, BLUE_E, fs=9)
box(ax, 4.0, 4.45, 1.5, 0.8, "主分片 2", GREEN_F, GREEN_E, fs=9, bold=True)

# 右：分库分表
ax.add_patch(FancyBboxPatch((6.2, 4.3), 5.5, 3.9, boxstyle="round,pad=0.04",
                            fc="#f8f9fa", ec="#9aa0a6", lw=1.1, linestyle="--"))
ax.text(6.4, 7.95, "MySQL 分库分表", fontsize=11, color="#5f6368", fontweight="bold")
box(ax, 6.5, 6.9, 4.9, 0.8, "user_id = 10086", YELL_F, YELL_E, fs=10)
arrow(ax, 8.95, 6.85, 8.95, 6.45)
box(ax, 6.5, 5.7, 4.9, 0.7, "10086 % 4 = 2", BLUE_F, BLUE_E, fs=10)
arrow(ax, 8.95, 5.65, 8.95, 5.25)
box(ax, 6.5, 4.45, 1.1, 0.8, "库 0", BLUE_F, BLUE_E, fs=9)
box(ax, 7.75, 4.45, 1.1, 0.8, "库 1", BLUE_F, BLUE_E, fs=9)
box(ax, 9.0, 4.45, 1.1, 0.8, "库 2", GREEN_F, GREEN_E, fs=9, bold=True)
box(ax, 10.25, 4.45, 1.1, 0.8, "库 3", BLUE_F, BLUE_E, fs=9)

box(ax, 0.3, 2.5, 11.4, 1.3,
    "同一个模子的推论：分母（主分片数 / 库数）定死后不能改\n扩容 = 新建一批 + 迁数据 + 双写切换（ES 里叫 reindex）",
    YELL_F, YELL_E, fs=10)

box(ax, 0.3, 0.6, 11.4, 1.5,
    "本质差异：分库分表的查询大多带分片键 → 精确路由 1 个库\nES 的搜索词（如「退款政策」）不带键 → 不知道文档在哪个分片\n→ 广播所有分片，各自查完再归并",
    GREEN_F, GREEN_E, fs=10)

plt.tight_layout()
plt.savefig(os.path.join(OUT, "04-routing.png"), dpi=150, bbox_inches="tight")
plt.close(fig)

# ============ 图 2：脑裂与 quorum ============
fig, ax = plt.subplots(figsize=(10.4, 7.6))
ax.set_xlim(0, 12)
ax.set_ylim(0, 9.2)
ax.axis("off")

ax.text(6.0, 8.85, "脑裂与多数派（5 个 master 候选节点，网络分成 2 + 3）",
        fontsize=12.5, fontweight="bold", ha="center")

# 左：无 quorum
ax.add_patch(FancyBboxPatch((0.3, 0.9), 5.5, 7.3, boxstyle="round,pad=0.04",
                            fc="#fff8f8", ec="#ea4335", lw=1.2, linestyle="--"))
ax.text(0.55, 7.85, "没有多数派约束（配错的年代）", fontsize=10.5,
        color="#c5221f", fontweight="bold")

box(ax, 0.7, 6.6, 1.9, 0.85, "自封 master ①", RED_F, RED_E, fs=9.5, bold=True)
box(ax, 0.7, 5.5, 1.9, 0.7, "节点 A", BLUE_F, BLUE_E, fs=9.5)
box(ax, 0.7, 4.6, 1.9, 0.7, "节点 B", BLUE_F, BLUE_E, fs=9.5)
arrow(ax, 1.65, 5.5, 1.65, 6.55, color="#ea4335")

ax.plot([3.15, 3.15], [3.9, 6.9], color="#ea4335", lw=1.8, linestyle=(0, (4, 3)))
ax.text(3.15, 3.55, "网络分区", fontsize=9, color="#c5221f", ha="center")

box(ax, 3.5, 6.6, 1.9, 0.85, "自封 master ②", RED_F, RED_E, fs=9.5, bold=True)
box(ax, 3.5, 5.5, 1.9, 0.7, "节点 C", BLUE_F, BLUE_E, fs=9.5)
box(ax, 3.5, 4.6, 1.9, 0.7, "节点 D", BLUE_F, BLUE_E, fs=9.5)
box(ax, 3.5, 3.7, 1.9, 0.7, "节点 E", BLUE_F, BLUE_E, fs=9.5)
arrow(ax, 4.45, 5.5, 4.45, 6.55, color="#ea4335")

box(ax, 0.6, 1.2, 4.9, 1.9,
    "两本「户口本」各自分配分片、\n各自接受变更\n分区愈合 → 视图错乱\n已确认的写入可能被覆盖",
    RED_F, RED_E, fs=9.5)

# 右：quorum
ax.add_patch(FancyBboxPatch((6.2, 0.9), 5.5, 7.3, boxstyle="round,pad=0.04",
                            fc="#f6fbf7", ec="#34a853", lw=1.2, linestyle="--"))
ax.text(6.45, 7.85, "quorum：多数派才合法", fontsize=10.5,
        color="#137333", fontweight="bold")

box(ax, 6.6, 6.5, 1.9, 0.95, "凑不够 3 票\n不选举", GRAY_F, GRAY_E, fs=9.5)
box(ax, 6.6, 5.4, 1.9, 0.7, "节点 A", GRAY_F, GRAY_E, fs=9.5)
box(ax, 6.6, 4.5, 1.9, 0.7, "节点 B", GRAY_F, GRAY_E, fs=9.5)

ax.plot([9.05, 9.05], [3.9, 6.9], color="#ea4335", lw=1.8, linestyle=(0, (4, 3)))
ax.text(9.05, 3.55, "网络分区", fontsize=9, color="#c5221f", ha="center")

box(ax, 9.4, 6.5, 2.1, 0.95, "3 / 5 多数票\n合法 master", GREEN_F, GREEN_E, fs=9.5, bold=True)
box(ax, 9.4, 5.4, 1.9, 0.7, "节点 C", BLUE_F, BLUE_E, fs=9.5)
box(ax, 9.4, 4.5, 1.9, 0.7, "节点 D", BLUE_F, BLUE_E, fs=9.5)
box(ax, 9.4, 3.7, 1.9, 0.7, "节点 E", BLUE_F, BLUE_E, fs=9.5)
arrow(ax, 10.35, 5.4, 10.35, 6.45, color="#34a853")

box(ax, 6.5, 1.2, 4.9, 1.9,
    "两个「超过半数」必有交集\n交集节点不会投两次票\n→ 同一时刻最多一个合法 master\n代价：少数派一侧冻结，不可用",
    GREEN_F, GREEN_E, fs=9.5)

plt.tight_layout()
plt.savefig(os.path.join(OUT, "04-quorum.png"), dpi=150, bbox_inches="tight")
plt.close(fig)

print("done")
