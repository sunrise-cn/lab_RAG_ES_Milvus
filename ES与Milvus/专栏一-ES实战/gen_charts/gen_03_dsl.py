# -*- coding: utf-8 -*-
"""第 03 篇配图：term vs match / bool 四子句"""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

BLUE_F, BLUE_E = "#e8f0fe", "#4285f4"
RED_F, RED_E = "#fce8e6", "#ea4335"
GREEN_F, GREEN_E = "#e6f4ea", "#34a853"
YELLOW_F, YELLOW_E = "#fff8e1", "#f9ab00"

def box(ax, x, y, w, h, text, fc, ec, fs=10, lw=1.4, ls="-", bold=False):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08", fc=fc, ec=ec, lw=lw, linestyle=ls)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            fontweight="bold" if bold else "normal", color="#202124")
    return p

def arrow(ax, x1, y1, x2, y2, color, lw=1.6, ls="-"):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=14,
                        color=color, lw=lw, linestyle=ls)
    ax.add_patch(a)

# ============================================================
# 图 1：term vs match
# ============================================================
fig, ax = plt.subplots(figsize=(11, 7.2))
ax.set_xlim(0, 12)
ax.set_ylim(0, 10.4)
ax.axis("off")

# 行 A：写入（蓝）
ax.text(0.4, 9.9, "写入时", fontsize=10, color="#5f6368")
box(ax, 0.4, 8.7, 3.1, 0.95, 'content = "申请退款"', BLUE_F, BLUE_E)
arrow(ax, 3.6, 9.18, 4.7, 9.18, BLUE_E)
box(ax, 4.8, 8.7, 3.4, 0.95, "standard 分词（逐字切分）", BLUE_F, BLUE_E)
arrow(ax, 8.3, 9.18, 9.4, 9.18, BLUE_E)
box(ax, 9.5, 8.7, 2.1, 0.95, "词典里存的是：\n申 / 请 / 退 / 款", BLUE_F, BLUE_E, fs=9.5)

# 行 B：term（红）
ax.text(0.4, 7.35, "查询 term", fontsize=10, color=RED_E)
box(ax, 0.4, 6.1, 3.1, 0.95, 'term：content = "退款"', RED_F, RED_E)
arrow(ax, 3.6, 6.58, 4.7, 6.58, RED_E)
box(ax, 4.8, 6.1, 3.4, 0.95, "不分词，拿「退款」\n原样查词典", RED_F, RED_E, fs=9.5)
arrow(ax, 8.3, 6.58, 9.4, 6.58, RED_E)
box(ax, 9.5, 6.1, 2.1, 0.95, "词典里没有「退款」\n0 条命中", RED_F, RED_E, fs=9.5, lw=1.8)

# 行 C：match（绿）
ax.text(0.4, 4.75, "查询 match", fontsize=10, color=GREEN_E)
box(ax, 0.4, 3.5, 3.1, 0.95, 'match：content = "退款"', GREEN_F, GREEN_E)
arrow(ax, 3.6, 3.98, 4.7, 3.98, GREEN_E)
box(ax, 4.8, 3.5, 3.4, 0.95, "先用同样的分词器\n切成：退 / 款", GREEN_F, GREEN_E, fs=9.5)
arrow(ax, 8.3, 3.98, 9.4, 3.98, GREEN_E)
box(ax, 9.5, 3.5, 2.1, 0.95, "词典里有，命中\n并按相关性排序", GREEN_F, GREEN_E, fs=9.5, lw=1.8)

box(ax, 0.4, 1.4, 11.2, 1.3,
    "法则：字段怎么进的索引，查询就得怎么查\ntext 字段进索引前被分词过，查询也要过同一道处理（match）；\nkeyword / 数字 / 日期不分词，用 term 精确匹配",
    YELLOW_F, YELLOW_E, fs=9.5)

fig.savefig(r"D:\Documents\ob_new\01 后端\my-doc\ES与Milvus\专栏一-ES实战\assets\03-term-vs-match.png",
            dpi=150, bbox_inches="tight")
plt.close(fig)

# ============================================================
# 图 2：bool 四子句，算分与缓存
# ============================================================
fig, ax = plt.subplots(figsize=(11, 6.4))
ax.set_xlim(0, 12)
ax.set_ylim(0, 9.4)
ax.axis("off")

box(ax, 4.0, 7.9, 4.0, 0.95, "bool：组合条件", BLUE_F, BLUE_E, fs=11.5, bold=True)

cols = [
    (0.4, "must", "相当于 AND\n参与相关性算分", BLUE_F, BLUE_E, "must / should\n的问题：\n「匹配得多好？」"),
    (3.4, "should", "加分项，非必须\n参与算分", BLUE_F, BLUE_E, None),
    (6.4, "must_not", "相当于 NOT\n不算分", "#ffffff", BLUE_E, "filter / must_not\n的问题：\n「匹配吗？」"),
    (9.4, "filter", "相当于 AND\n不算分，结果可缓存", GREEN_F, GREEN_E, None),
]
for x, name, desc, fc, ec, _ in cols:
    arrow(ax, 6.0, 7.85, x + 1.3, 6.85, ec, lw=1.3)
    box(ax, x, 5.7, 2.6, 1.0, name, fc, ec, fs=11.5, bold=True,
        lw=1.8 if name == "filter" else 1.4)
    ax.text(x + 1.3, 5.25, desc, ha="center", va="top", fontsize=9, color="#202124")

# filter 的缓存标注
box(ax, 8.9, 2.3, 2.6, 1.4, "结果缓存成位图\n下次直接复用\n不碰倒排索引", GREEN_F, GREEN_E, fs=9)
arrow(ax, 10.7, 3.75, 10.7, 4.62, GREEN_E, lw=1.4, ls="--")

# 两个问题域的标注
box(ax, 0.4, 2.3, 5.3, 1.4, "must / should 回答：\n「匹配吗？匹配得多好？」\n→ 每条结果带 _score", BLUE_F, BLUE_E, fs=9)
box(ax, 6.0, 0.35, 5.5, 1.35, "filter 回答：\n「匹配吗？」非黑即白 → 状态 / 时间 / 权限放这里", GREEN_F, GREEN_E, fs=9)

fig.savefig(r"D:\Documents\ob_new\01 后端\my-doc\ES与Milvus\专栏一-ES实战\assets\03-query-vs-filter.png",
            dpi=150, bbox_inches="tight")
plt.close(fig)
print("done")
