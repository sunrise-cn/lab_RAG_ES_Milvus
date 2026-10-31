# -*- coding: utf-8 -*-
"""第 01 篇配图：正排 vs 倒排 / 写入放大"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

BLUE_F, BLUE_E = "#e8f0fe", "#4285f4"
RED_F, RED_E = "#fce8e6", "#ea4335"
GREEN_F, GREEN_E = "#e6f4ea", "#34a853"
YELLOW_F, YELLOW_E = "#fff8e1", "#f9ab00"

def box(ax, x, y, w, h, text, fc, ec, fs=10, lw=1.4, bold=False, style="round,pad=0.08"):
    p = FancyBboxPatch((x, y), w, h, boxstyle=style, fc=fc, ec=ec, lw=lw)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, fontweight="bold" if bold else "normal", color="#202124")
    return p

def arrow(ax, x1, y1, x2, y2, color, lw=1.6, style="-|>", ls="-", rad=0.0):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=14,
                        color=color, lw=lw, linestyle=ls,
                        connectionstyle=f"arc3,rad={rad}")
    ax.add_patch(a)

def new_ax(w, h):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 10.6)
    ax.axis("off")
    return fig, ax

# ============================================================
# 图 1：正排 vs 倒排
# ============================================================
fig, ax = new_ax(11, 8.2)

# 顶部查询横幅
box(ax, 0.8, 9.7, 10.4, 0.8, "查询：哪些文档包含「退款」？", YELLOW_F, YELLOW_E, fs=12, bold=True)

# ---- 左：正排 ----
ax.text(2.7, 9.25, "正排：文档 → 内容（MySQL 行存视角）", ha="center", fontsize=11,
        fontweight="bold", color="#202124")

rows = [
    ("1", "申请退款，多久到账", True),
    ("2", "物流太慢，等了一周", False),
    ("3", "发票怎么开", False),
    ("4", "退款政策是什么", True),
]
y = 8.35
for rid, content, hit in rows:
    box(ax, 0.5, y, 0.7, 0.62, rid, BLUE_F, BLUE_E, fs=10)
    fc, ec = (GREEN_F, GREEN_E) if hit else (BLUE_F, BLUE_E)
    box(ax, 1.2, y, 3.4, 0.62, content, fc, ec, fs=10)
    # 扫描箭头：从上到下逐行
    arrow(ax, 5.0, y + 0.62, 5.0, y + 0.06, RED_E, lw=1.4)
    y -= 0.82

ax.text(5.0, 5.45, "逐行扫描匹配", ha="center", va="center", fontsize=9,
        color=RED_E)
box(ax, 0.5, 2.6, 4.7, 1.15,
    "O(n)：500 万行就得扫 500 万行\n且匹配只有 0/1，算不出相关性", RED_F, RED_E, fs=9.5)

# ---- 右：倒排 ----
ax.text(8.9, 9.25, "倒排：词 → 文档列表", ha="center", fontsize=11,
        fontweight="bold", color="#202124")

# 词典
box(ax, 6.5, 6.0, 1.7, 2.6, "", BLUE_F, BLUE_E, fs=10)
ax.text(7.35, 8.75, "词典（有序）", ha="center", fontsize=10, fontweight="bold", color="#202124")
for i, term in enumerate(["发票", "物流", "退款"]):
    fc, ec = (GREEN_F, GREEN_E) if term == "退款" else ("white", BLUE_E)
    box(ax, 6.68, 6.18 + i * 0.82, 1.34, 0.62, term, fc, ec, fs=10,
        lw=1.8 if term == "退款" else 1.0)

# posting list
ax.text(9.85, 8.75, "posting list", ha="center", fontsize=10, fontweight="bold", color="#202124")
pl = [("发票", "[3]", False), ("物流", "[2]", False), ("退款", "[1, 4]", True)]
for i, (term, lst, hit) in enumerate(pl):
    fc, ec = (GREEN_F, GREEN_E) if hit else (BLUE_F, BLUE_E)
    py = 6.18 + i * 0.82
    box(ax, 8.8, py, 2.2, 0.62, lst, fc, ec, fs=10, lw=1.8 if hit else 1.0)
    # 词典 → posting list
    x1 = 8.02 if not hit else 8.02
    arrow(ax, x1, py + 0.31, 8.76, py + 0.31, GREEN_E if hit else BLUE_E,
          lw=1.8 if hit else 1.0)

# 查询 → 词典「退款」定位
arrow(ax, 7.35, 9.66, 7.35, 8.9, GREEN_E, lw=2.0)
ax.text(6.35, 9.3, "二分定位「退款」", fontsize=9, color=GREEN_E, ha="center")

box(ax, 6.5, 2.5, 4.7, 1.35,
    "O(log n) 定位 + 读一个列表\n词频、文档频率就存在索引里\n命中后按文档号回取原文", GREEN_F, GREEN_E, fs=9.5)

fig.savefig(r"D:\Documents\ob_new\01 后端\my-doc\ES与Milvus\专栏一-ES实战\assets\01-inverted-vs-forward.png",
            dpi=150, bbox_inches="tight")
plt.close(fig)

# ============================================================
# 图 2：写入放大
# ============================================================
fig, ax = new_ax(11, 5.6)

ax.text(0.5, 6.9, "MySQL：一次写入", fontsize=11, fontweight="bold", color="#202124")
box(ax, 0.5, 5.2, 2.6, 1.2, "INSERT\n1 行工单", BLUE_F, BLUE_E, fs=10)
arrow(ax, 3.2, 5.8, 4.2, 5.8, BLUE_E, lw=1.8)
box(ax, 4.3, 5.2, 3.4, 1.2, "B+ 树上\n写入一个页", BLUE_F, BLUE_E, fs=10)
arrow(ax, 7.8, 5.8, 8.8, 5.8, BLUE_E, lw=1.8)
box(ax, 8.9, 5.2, 2.7, 1.2, "结构更新次数：1", GREEN_F, GREEN_E, fs=10)

ax.text(0.5, 3.9, "ES：一次写入", fontsize=11, fontweight="bold", color="#202124")
box(ax, 0.5, 2.1, 2.6, 1.2, "写入\n1 篇文档", BLUE_F, BLUE_E, fs=10)
arrow(ax, 3.2, 2.7, 4.2, 2.7, RED_E, lw=1.8)
box(ax, 4.3, 2.1, 3.4, 1.2, "分词：退款 / 政策\n到账 / …（N 个词）", BLUE_F, BLUE_E, fs=10)
arrow(ax, 7.8, 2.7, 8.8, 2.7, RED_E, lw=1.8)
box(ax, 8.9, 1.7, 2.7, 2.0, "词典登记 × N\nposting list\n追加 × N", RED_F, RED_E, fs=10)

box(ax, 0.5, 0.2, 11.1, 1.0,
    "1 次业务写入 = 几十上百次结构更新：吞吐差距不是实现问题，是结构本身的账",
    YELLOW_F, YELLOW_E, fs=10)

fig.savefig(r"D:\Documents\ob_new\01 后端\my-doc\ES与Milvus\专栏一-ES实战\assets\01-write-amplification.png",
            dpi=150, bbox_inches="tight")
plt.close(fig)
print("done")
