# -*- coding: utf-8 -*-
"""专栏三 01 倒排索引内部结构 配图（3 张）"""
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

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
os.makedirs(OUT, exist_ok=True)


def box(ax, x, y, w, h, text, fc, ec, fs=10, bold=False, ls="-"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06",
                                fc=fc, ec=ec, lw=1.6, linestyle=ls))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, fontweight="bold" if bold else "normal")


def arrow(ax, x1, y1, x2, y2, label=None, color="#5f6368", fs=9, dx=0.12, style="-|>"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style,
                                 mutation_scale=14, color=color, lw=1.6))
    if label:
        ax.text((x1 + x2) / 2 + dx, (y1 + y2) / 2, label, fontsize=fs,
                color=color, ha="left", va="center")


# ============ 图 1：三层结构与查找路径 ============
fig, ax = plt.subplots(figsize=(8.6, 6.4))
ax.set_xlim(0, 10)
ax.set_ylim(0, 10.6)
ax.axis("off")

# 分区背景：内存 / 磁盘
ax.add_patch(FancyBboxPatch((0.25, 6.6), 9.5, 3.5, boxstyle="round,pad=0.05",
                            fc="#f8f9fa", ec="#9aa0a6", lw=1.2, linestyle="--"))
ax.text(0.55, 9.78, "内存（常驻）", fontsize=11, color="#5f6368", fontweight="bold")
ax.add_patch(FancyBboxPatch((0.25, 0.3), 9.5, 6.0, boxstyle="round,pad=0.05",
                            fc="#f1f3f4", ec="#9aa0a6", lw=1.2, linestyle="--"))
ax.text(0.55, 6.05, "磁盘（mmap 进 OS page cache）", fontsize=11, color="#5f6368", fontweight="bold")

# 查询入口
box(ax, 0.7, 7.5, 2.0, 1.1, "查询\nterm = 退款", YELL_F, YELL_E, fs=11, bold=True)

# Term Index / FST
box(ax, 3.4, 7.05, 5.6, 2.0,
    "Term Index（.tip，FST）\n前缀+后缀共享，只存 block 入口\n退款 → block 37",
    BLUE_F, BLUE_E, fs=11, bold=True)

arrow(ax, 2.75, 8.05, 3.35, 8.05)
ax.text(3.05, 8.55, "O(词长) 定位", fontsize=9, color="#5f6368", ha="center")

# Term Dictionary blocks
box(ax, 3.4, 4.6, 1.7, 0.95, "block 36\n售后 售前 …", "#ffffff", BLUE_E, fs=9)
box(ax, 5.35, 4.6, 2.0, 0.95, "block 37\n退款 退款流程\n退款政策 退货", GREEN_F, GREEN_E, fs=9, bold=True)
box(ax, 7.55, 4.6, 1.45, 0.95, "block 38\n银行 销量 …", "#ffffff", BLUE_E, fs=9)
ax.text(6.2, 5.85, "Term Dictionary（.tim，按 block 有序存放）",
        fontsize=11, color="#202124", ha="center", fontweight="bold")

arrow(ax, 6.2, 7.0, 6.2, 5.62)
ax.text(6.45, 6.5, "顺序读一个 block", fontsize=9, color="#5f6368", ha="left")

# Posting list
box(ax, 3.4, 2.6, 5.6, 1.15,
    "Posting List（.doc）\ndoc ids: 1  5  9  47  210 …（FOR 压缩）", BLUE_F, BLUE_E, fs=10)
arrow(ax, 6.35, 4.55, 6.35, 3.8, "term 命中，取列表", dx=0.15)

# 返回
box(ax, 3.4, 0.9, 5.6, 0.9, "返回文档列表（含词频、位置信息）", GREEN_F, GREEN_E, fs=10)
arrow(ax, 6.2, 2.55, 6.2, 1.85, None, dx=0.1)

# miss 说明
box(ax, 0.55, 2.3, 2.4, 1.75,
    "FST 不含全部 term\nmiss 时多读一个 block\n（B+ 树非叶子层做不到\n这种稀疏）",
    YELL_F, YELL_E, fs=9)

plt.tight_layout()
plt.savefig(os.path.join(OUT, "01-inverted-structure.png"), dpi=150, bbox_inches="tight")
plt.close(fig)

# ============ 图 2：delta + FOR 压缩 ============
fig, ax = plt.subplots(figsize=(9.2, 5.6))
ax.set_xlim(0, 10)
ax.set_ylim(0, 6.2)
ax.axis("off")

ax.text(5, 5.95, "posting list 压缩：从 160 bit 到 40 bit", fontsize=13,
        fontweight="bold", ha="center")

# 原始列表
ids = [73, 300, 302, 332, 500]
x0 = 1.0
for i, v in enumerate(ids):
    box(ax, x0 + i * 1.35, 4.7, 1.15, 0.85, str(v), BLUE_F, BLUE_E, fs=12)
ax.text(1.0, 5.72, "原始 doc id 列表", fontsize=10.5, color="#202124")
ax.text(x0 + 5 * 1.35 + 0.25, 5.12, "32 bit × 5 = 160 bit",
        fontsize=10, va="center", color="#5f6368")

arrow(ax, 5, 4.55, 5, 3.95, "delta 编码：升序列表只存相邻差值", dx=0.15)

deltas = [73, 227, 2, 30, 168]
for i, v in enumerate(deltas):
    box(ax, x0 + i * 1.35, 3.0, 1.15, 0.85, str(v), BLUE_F, BLUE_E, fs=12)
ax.text(x0 + 5 * 1.35 + 0.25, 3.42, "差值大多变小",
        fontsize=10, va="center", color="#5f6368")

arrow(ax, 5, 2.85, 5, 2.25, "FOR：按组定 bit 宽度（Lucene 128 个/组）", dx=0.15)

# FOR 位流
bits = ["01001001", "11100011", "00000010", "00011110", "10101000"]
for i, b in enumerate(bits):
    box(ax, x0 + i * 1.35, 1.3, 1.15, 0.85, b, GREEN_F, GREEN_E, fs=10.5)
ax.text(x0 + 5 * 1.35 + 0.25, 1.72, "最大差值 227 → 8 bit\n8 bit × 5 = 40 bit",
        fontsize=10, va="center", color="#1e8e3e")

box(ax, 1.0, 0.15, 8.0, 0.75,
    "代价：组内混进一个大数，整组宽度被拉高（赌差值分布均匀）",
    YELL_F, YELL_E, fs=10)

plt.tight_layout()
plt.savefig(os.path.join(OUT, "01-for-compression.png"), dpi=150, bbox_inches="tight")
plt.close(fig)

# ============ 图 3：doc values 列存 ============
fig, ax = plt.subplots(figsize=(9.4, 5.6))
ax.set_xlim(0, 10)
ax.set_ylim(0, 6.6)
ax.axis("off")

ax.text(2.5, 6.3, "倒排 / 行存：词 → 文档", fontsize=12, fontweight="bold",
        ha="center", color="#202124")
ax.text(7.5, 6.3, "doc values 列存：文档 → 字段值", fontsize=12, fontweight="bold",
        ha="center", color="#202124")

# 左：行存
cols = ["title", "category", "price", "stock"]
rows = [
    ["退款政策…", "售后", "89", "12"],
    ["退款流程…", "售后", "299", "3"],
    ["支付说明…", "支付", "45", "88"],
]
bx, by, cw, rh = 0.35, 3.4, 1.05, 0.62
for j, c in enumerate(cols):
    fc = RED_F if c == "price" else "#f8f9fa"
    ec = RED_E if c == "price" else "#9aa0a6"
    box(ax, bx + j * cw, by + 3 * rh, cw, rh, c, fc, ec, fs=9.5, bold=(c == "price"))
for i, row in enumerate(rows):
    for j, v in enumerate(row):
        fc = RED_F if j == 2 else "#ffffff"
        ec = RED_E if j == 2 else "#9aa0a6"
        box(ax, bx + j * cw, by + (2 - i) * rh, cw, rh, v, fc, ec, fs=9)
ax.text(5.0, 4.05, "…几千万行", fontsize=9.5, color="#5f6368", va="center")
box(ax, 0.35, 0.55, 4.3, 1.1,
    "聚合 price：按行组织，取一列\n等于把整份索引转置一遍", RED_F, RED_E, fs=10)

# 中间箭头
arrow(ax, 4.95, 3.1, 5.35, 3.1, None, color="#5f6368")
ax.text(5.15, 3.45, "同一份数据\n另存一份", fontsize=9, ha="center", color="#5f6368")

# 右：列存
bx2 = 5.6
box(ax, bx2, 4.55, 1.3, 0.62, "doc_id", "#f8f9fa", "#9aa0a6", fs=9.5)
box(ax, bx2 + 1.35, 4.55, 1.3, 0.62, "price", GREEN_F, GREEN_E, fs=9.5, bold=True)
doc_ids = ["1", "2", "3"]
prices = ["89", "299", "45"]
for i in range(3):
    box(ax, bx2, 3.93 - i * 0.62, 1.3, 0.62, doc_ids[i], "#ffffff", "#9aa0a6", fs=9)
    box(ax, bx2 + 1.35, 3.93 - i * 0.62, 1.3, 0.62, prices[i], GREEN_F, GREEN_E, fs=9)
ax.text(bx2 + 2.9, 3.55, "…只读 price\n这一列", fontsize=9.5, color="#1e8e3e", va="center")
box(ax, 5.6, 0.55, 4.0, 1.1,
    "聚合 / 排序只扫这一列\n（.dvd 文件，mmap 进 page cache）", GREEN_F, GREEN_E, fs=10)

plt.tight_layout()
plt.savefig(os.path.join(OUT, "01-doc-values.png"), dpi=150, bbox_inches="tight")
plt.close(fig)

print("done:", os.listdir(OUT))
