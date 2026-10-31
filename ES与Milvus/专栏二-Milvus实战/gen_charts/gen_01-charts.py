# -*- coding: utf-8 -*-
"""专栏二 01 篇配图：文本→向量→相似度；暴力扫描 vs ANN"""
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

BLUE_F, BLUE_E = "#e8f0fe", "#4285f4"
RED_F, RED_E = "#fce8e6", "#ea4335"
GREEN_F, GREEN_E = "#e6f4ea", "#34a853"
YELLOW_F, YELLOW_E = "#fff8e1", "#f9ab00"
GRAY = "#5f6368"

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
os.makedirs(OUT, exist_ok=True)


def box(ax, x, y, w, h, text, fc, ec, fs=10, bold=False):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                       linewidth=1.6, facecolor=fc, edgecolor=ec)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, color="#202124",
            fontweight="bold" if bold else "normal", linespacing=1.5)


def arrow(ax, x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=GRAY, lw=1.6,
                                mutation_scale=16, shrinkA=2, shrinkB=2))


# ---------- 图 1：文本 → 向量 → 余弦相似度 ----------
fig, ax = plt.subplots(figsize=(11, 5))
ax.set_xlim(0, 10.6)
ax.set_ylim(-0.45, 3.45)
ax.axis("off")
ax.set_title("文本 → 向量 → 余弦相似度", fontsize=14, pad=12)

rows = [
    (2.5, "用户查询\n「怎么退货」", "v1 = [0.21, -0.05, …, 0.44]",
     "作为查询基准", YELLOW_F, YELLOW_E),
    (1.25, "文档 A\n「退款流程指引」", "v2 = [0.19, -0.03, …, 0.46]",
     "cos(v1, v2) ≈ 0.87\n语义相近 → 命中", GREEN_F, GREEN_E),
    (0.0, "文档 B\n「服务器扩容方案」", "v3 = [-0.10, 0.42, …, -0.07]",
     "cos(v1, v3) ≈ 0.08\n语义无关 → 落选", RED_F, RED_E),
]

# 列头
for cx, t in [(1.2, "文本"), (5.55, "向量化"), (7.15, "向量"), (9.35, "与查询的相似度")]:
    ax.text(cx, 3.22, t, ha="center", va="center", fontsize=10, color=GRAY)

for y, txt, vec, score, sf, se in rows:
    box(ax, 0.1, y - 0.42, 2.2, 0.84, txt, BLUE_F, BLUE_E, fs=10)
    arrow(ax, 2.32, y, 3.9, y)
    arrow(ax, 5.15, y, 6.15, y)
    box(ax, 6.2, y - 0.34, 2.1, 0.68, vec, BLUE_F, BLUE_E, fs=9)
    arrow(ax, 8.32, y, 8.75, y)
    box(ax, 8.8, y - 0.42, 1.7, 0.84, score, sf, se, fs=9)

box(ax, 3.95, -0.1, 1.2, 3.1,
    "embedding\n模型\n\n（同一个\n模型）\n\n文本 →\n定长向量", GREEN_F, GREEN_E, fs=10)

fig.savefig(os.path.join(OUT, "01-embedding.png"), dpi=150, bbox_inches="tight")
plt.close(fig)

# ---------- 图 2：暴力扫描 vs ANN ----------
rng = np.random.default_rng(42)
pts = np.vstack([
    rng.normal([0.3, 0.3], 0.13, (45, 2)),
    rng.normal([0.72, 0.35], 0.11, (35, 2)),
    rng.normal([0.5, 0.75], 0.12, (30, 2)),
])
pts = pts[(pts[:, 0] > 0.02) & (pts[:, 0] < 0.98) & (pts[:, 1] > 0.02) & (pts[:, 1] < 0.98)]
q = np.array([0.52, 0.58])
near = np.linalg.norm(pts - q, axis=1) < 0.19

fig, axes = plt.subplots(1, 2, figsize=(11, 4.9))

ax = axes[0]
for p in pts:
    ax.plot([q[0], p[0]], [q[1], p[1]], color=RED_E, lw=0.5, alpha=0.22, zorder=1)
ax.scatter(pts[:, 0], pts[:, 1], s=14, color="#9aa0a6", zorder=2)
ax.scatter(*q, marker="*", s=320, color=RED_E, zorder=3)
ax.set_title("暴力扫描（FLAT）：逐一比对全部", fontsize=12)
ax.text(0.5, -0.05, "O(n)：100 万次点积 · 召回 100% · 百毫秒级",
        transform=ax.transAxes, ha="center", va="top", fontsize=10,
        bbox=dict(boxstyle="round,pad=0.5", fc=RED_F, ec=RED_E, lw=1.4))

ax = axes[1]
ax.add_patch(Circle(q, 0.19, facecolor=GREEN_E, alpha=0.08,
                    edgecolor=GREEN_E, lw=1.4, linestyle="--"))
for p in pts[near]:
    ax.plot([q[0], p[0]], [q[1], p[1]], color=GREEN_E, lw=1.0, alpha=0.6, zorder=1)
ax.scatter(pts[~near][:, 0], pts[~near][:, 1], s=14, color="#d0d4d9", zorder=2)
ax.scatter(pts[near][:, 0], pts[near][:, 1], s=20, color=GREEN_E, zorder=3)
ax.scatter(*q, marker="*", s=320, color=RED_E, zorder=4)
ax.set_title("ANN（IVF / HNSW）：先粗定位，再局部精搜", fontsize=12)
ax.text(0.5, -0.05, "只比对邻近区域 · 召回约 95%+ · 亚毫秒级",
        transform=ax.transAxes, ha="center", va="top", fontsize=10,
        bbox=dict(boxstyle="round,pad=0.5", fc=GREEN_F, ec=GREEN_E, lw=1.4))

for ax in axes:
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_edgecolor("#dadce0")

fig.tight_layout()
fig.savefig(os.path.join(OUT, "01-bruteforce-vs-ann.png"), dpi=150, bbox_inches="tight")
plt.close(fig)

print("done")
