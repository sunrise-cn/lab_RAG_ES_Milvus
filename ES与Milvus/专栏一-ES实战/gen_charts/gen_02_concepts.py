# -*- coding: utf-8 -*-
"""第 02 篇配图：index → shard → replica 拓扑"""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

BLUE_F, BLUE_E = "#e8f0fe", "#4285f4"
RED_F, RED_E = "#fce8e6", "#ea4335"
GREEN_F, GREEN_E = "#e6f4ea", "#34a853"
YELLOW_F, YELLOW_E = "#fff8e1", "#f9ab00"

def box(ax, x, y, w, h, text, fc, ec, fs=10, lw=1.4, ls="-"):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08", fc=fc, ec=ec, lw=lw, linestyle=ls)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color="#202124")
    return p

def arrow(ax, x1, y1, x2, y2, color, lw=1.6, ls="-", rad=0.0):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=14,
                        color=color, lw=lw, linestyle=ls, connectionstyle=f"arc3,rad={rad}")
    ax.add_patch(a)

fig, ax = plt.subplots(figsize=(11, 7))
ax.set_xlim(0, 12)
ax.set_ylim(0, 10.3)
ax.axis("off")

# 顶部：index（逻辑）
box(ax, 2.5, 9.2, 7.0, 0.85, "index：work_orders（逻辑命名空间）", BLUE_F, BLUE_E,
    fs=11.5, lw=1.8)

# 写入路由箭头：index → P0 / P1
arrow(ax, 4.6, 9.12, 2.5, 7.0, BLUE_E, lw=1.8, rad=0.12)
arrow(ax, 7.4, 9.12, 9.5, 7.0, BLUE_E, lw=1.8, rad=-0.12)
ax.text(6.0, 8.35, "写入：hash(_id) % 主分片数 路由", fontsize=10, ha="center", color=BLUE_E)

# 两个节点容器
box(ax, 0.5, 1.9, 5.2, 5.9, "", "#ffffff", BLUE_E, ls="--", lw=1.2)
box(ax, 6.3, 1.9, 5.2, 5.9, "", "#ffffff", BLUE_E, ls="--", lw=1.2)
ax.text(3.1, 7.5, "Node 1", fontsize=11, fontweight="bold", ha="center", color="#202124")
ax.text(8.9, 7.5, "Node 2", fontsize=11, fontweight="bold", ha="center", color="#202124")

# 分片：Node1 上是 P0 + R1，Node2 上是 P1 + R0（错开）
box(ax, 1.3, 5.6, 2.2, 1.0, "P0\n主分片", BLUE_F, BLUE_E, fs=10, lw=1.8)
box(ax, 3.3, 2.5, 2.2, 1.0, "R1\n副本", "#ffffff", BLUE_E, fs=10)
box(ax, 7.3, 5.6, 2.2, 1.0, "P1\n主分片", BLUE_F, BLUE_E, fs=10, lw=1.8)
box(ax, 8.5, 2.5, 2.2, 1.0, "R0\n副本", "#ffffff", BLUE_E, fs=10)

# 复制箭头（交叉：P 的副本总在另一个节点上）
arrow(ax, 3.55, 6.1, 8.45, 3.1, GREEN_E, lw=1.6, rad=0.15)
arrow(ax, 7.25, 6.1, 5.55, 3.05, GREEN_E, lw=1.6, rad=0.15)
ax.text(6.0, 4.6, "主分片同步复制到副本\n（副本与主分片错开节点）", fontsize=9.5,
        ha="center", color=GREEN_E)

# 查询说明
ax.text(6.0, 1.45, "查询：主分片与副本均可承担", fontsize=9.5, ha="center", color="#5f6368")

# 底部结论
box(ax, 0.5, 0.15, 11.0, 1.0,
    "任一节点挂掉，另一节点上仍有全量数据；主分片数建索引时定死，副本数随时可调",
    YELLOW_F, YELLOW_E, fs=10)

fig.savefig(r"D:\Documents\ob_new\01 后端\my-doc\ES与Milvus\专栏一-ES实战\assets\02-index-shard-replica.png",
            dpi=150, bbox_inches="tight")
plt.close(fig)
print("done")
