# -*- coding: utf-8 -*-
"""专栏二 03 篇配图：entity 结构；partition 裁剪"""
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

BLUE_F, BLUE_E = "#e8f0fe", "#4285f4"
RED_F, RED_E = "#fce8e6", "#ea4335"
GREEN_F, GREEN_E = "#e6f4ea", "#34a853"
YELLOW_F, YELLOW_E = "#fff8e1", "#f9ab00"
GRAY = "#5f6368"

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
os.makedirs(OUT, exist_ok=True)


def box(ax, x, y, w, h, text, fc, ec, fs=9.5, bold=False):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                       linewidth=1.6, facecolor=fc, edgecolor=ec)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            color="#202124", fontweight="bold" if bold else "normal", linespacing=1.6)


def arrow(ax, x1, y1, x2, y2, color=GRAY, lw=1.4, alpha=1.0):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, alpha=alpha,
                                mutation_scale=14, shrinkA=2, shrinkB=2))


# ---------- 图 1：一条 entity 长什么样 ----------
fig, ax = plt.subplots(figsize=(11, 4.6))
ax.set_xlim(0, 10.9)
ax.set_ylim(0, 4.1)
ax.axis("off")
ax.set_title("一条 entity 长什么样（RAG 知识库的 collection）", fontsize=13, pad=10)

xs = [0.15, 2.17, 3.89, 6.71, 8.33]
ws = [1.8, 1.5, 2.6, 1.4, 2.4]
texts = [
    "chunk_id\nVARCHAR 主键\n\ndoc-1024-3",
    "doc_id\nVARCHAR\n\ndoc-1024",
    "text\nVARCHAR\n\n退款流程：登录\n后进入订单页…",
    "source\nVARCHAR\n\nwiki",
    "embedding\nFLOAT_VECTOR\n\n[0.21, -0.05, …]\n× 1024 维",
]
ecs = [YELLOW_E, BLUE_E, BLUE_E, BLUE_E, GREEN_E]
fcs = [YELLOW_F, BLUE_F, BLUE_F, BLUE_F, GREEN_F]

for x, w, t, fc, ec in zip(xs, ws, texts, fcs, ecs):
    box(ax, x, 1.6, w, 1.7, t, fc, ec)

ax.text(xs[0] + ws[0] / 2, 3.62, "主键（业务 id）：幂等入库的抓手",
        ha="center", fontsize=9, color=GRAY)
ax.text(xs[4] + ws[4] / 2, 3.62, "检索的主角：相似度靠它算",
        ha="center", fontsize=9, color=GRAY)

# 标量配角注释
ax.plot([xs[1], xs[3] + ws[3]], [1.35, 1.35], color=GRAY, lw=1.0)
ax.plot([xs[1], xs[1]], [1.35, 1.5], color=GRAY, lw=1.0)
ax.plot([xs[3] + ws[3], xs[3] + ws[3]], [1.35, 1.5], color=GRAY, lw=1.0)
ax.text((xs[1] + xs[3] + ws[3]) / 2, 0.75,
        "标量字段是配角：过滤（filter）与展示（喂给大模型）",
        ha="center", fontsize=10, color=GRAY)

fig.savefig(os.path.join(OUT, "03-schema-entity.png"), dpi=150, bbox_inches="tight")
plt.close(fig)

# ---------- 图 2：partition 裁剪 ----------
rng = np.random.default_rng(7)

fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
px = [0.5, 2.3, 4.1, 5.9]
pw, py, ph = 1.6, 1.0, 2.4

for ax, mode in zip(axes, ["all", "one"]):
    for i, x in enumerate(px):
        hit = (mode == "one" and i == 1)
        fc = GREEN_F if hit else (BLUE_F if mode == "all" else "#f1f3f4")
        ec = GREEN_E if hit else (BLUE_E if mode == "all" else "#bdc1c6")
        ax.add_patch(FancyBboxPatch((x, py), pw, ph,
                                    boxstyle="round,pad=0.02,rounding_size=0.08",
                                    linewidth=1.6, facecolor=fc, edgecolor=ec))
        dots = rng.uniform([x + 0.18, py + 0.18], [x + pw - 0.18, py + ph - 0.18], (12, 2))
        ax.scatter(dots[:, 0], dots[:, 1], s=12,
                   color=GREEN_E if hit else ("#4285f4" if mode == "all" else "#c7cbd0"))
        ax.text(x + pw / 2, py - 0.32, f"租户{chr(97 + i)}", ha="center",
                fontsize=10, color=GRAY)
        if mode == "all":
            ax.add_patch(Rectangle((x, py), pw, ph, facecolor=RED_E, alpha=0.10,
                                   edgecolor=RED_E, lw=1.2, linestyle="--"))
    ax.set_xlim(0, 8)
    ax.set_ylim(0, 4.9)
    ax.axis("off")

axes[0].set_title("不带 partition：全 collection 比对", fontsize=12)
axes[1].set_title("指定 partition_names=['tenant_b']", fontsize=12)

axes[0].text(4.0, 4.35, "search（不指定 partition）", ha="center", fontsize=9.5,
             color="#202124",
             bbox=dict(boxstyle="round,pad=0.35", fc="#ffffff", ec=GRAY, lw=1.0))
for x in px:
    arrow(axes[0], 4.0, 4.15, x + pw / 2, 3.45, color=RED_E, lw=1.1, alpha=0.75)
axes[0].text(4.0, 0.25, "4 个分区全部进入比对：扫的向量多",
             ha="center", fontsize=10,
             bbox=dict(boxstyle="round,pad=0.45", fc=RED_F, ec=RED_E, lw=1.4))

axes[1].text(4.0, 4.35, "search（指定 partition）", ha="center", fontsize=9.5,
             color="#202124",
             bbox=dict(boxstyle="round,pad=0.35", fc="#ffffff", ec=GRAY, lw=1.0))
arrow(axes[1], 4.0, 4.15, px[1] + pw / 2, 3.45, color=GREEN_E, lw=1.6)
axes[1].text(4.0, 0.25, "只比对 1 个分区：既隔离又提速",
             ha="center", fontsize=10,
             bbox=dict(boxstyle="round,pad=0.45", fc=GREEN_F, ec=GREEN_E, lw=1.4))

fig.tight_layout()
fig.savefig(os.path.join(OUT, "03-partition-pruning.png"), dpi=150, bbox_inches="tight")
plt.close(fig)

print("done")
