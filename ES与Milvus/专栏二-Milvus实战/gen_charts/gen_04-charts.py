# -*- coding: utf-8 -*-
"""专栏二 04 篇配图：入库流水线；三种度量方式"""
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Arc

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

BLUE_F, BLUE_E = "#e8f0fe", "#4285f4"
RED_F, RED_E = "#fce8e6", "#ea4335"
GREEN_F, GREEN_E = "#e6f4ea", "#34a853"
YELLOW_F, YELLOW_E = "#fff8e1", "#f9ab00"
GRAY = "#5f6368"

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
os.makedirs(OUT, exist_ok=True)


def box(ax, x, y, w, h, text, fc, ec, fs=10):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                       linewidth=1.6, facecolor=fc, edgecolor=ec)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            color="#202124", linespacing=1.6)


def arrow(ax, x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=GRAY, lw=1.6,
                                mutation_scale=16, shrinkA=2, shrinkB=2))


# ---------- 图 1：入库流水线 ----------
fig, ax = plt.subplots(figsize=(11, 3.9))
ax.set_xlim(0, 10.7)
ax.set_ylim(0, 3.6)
ax.axis("off")
ax.set_title("入库流水线", fontsize=13, pad=10)

stages = [
    ("原始文档\nmd / pdf / wiki", BLUE_F, BLUE_E),
    ("切分 chunking\n切片 + chunk_id", BLUE_F, BLUE_E),
    ("embedding 模型\n批量推理", GREEN_F, GREEN_E),
    ("批量 insert\n千条一批", BLUE_F, BLUE_E),
    ("Milvus\ncollection", BLUE_F, BLUE_E),
]
xs = [0.15, 2.30, 4.45, 6.60, 8.75]
w, y, h = 1.7, 1.75, 1.25
for (t, fc, ec), x in zip(stages, xs):
    box(ax, x, y, w, h, t, fc, ec)

for i in range(4):
    arrow(ax, xs[i] + w + 0.04, y + h / 2, xs[i + 1] - 0.04, y + h / 2)

ax.text(xs[1] + w + 0.28, y + h / 2 + 0.22, "一批 1000 条",
        ha="center", fontsize=9, color=GRAY)
ax.text(xs[2] + w + 0.28, y + h / 2 + 0.22, "向量 + 标量",
        ha="center", fontsize=9, color=GRAY)
ax.text(xs[1] + w / 2, y - 0.28, "切法本身是专栏四第 1 篇的主题",
        ha="center", fontsize=9, color=GRAY)

box(ax, 0.15, 0.25, 10.3, 0.85,
    "模型、维度、归一化，三样贯穿全程——任何一个中途换了，检索质量静悄悄烂掉（换模型 = 全量重灌）",
    YELLOW_F, YELLOW_E, fs=10)

fig.savefig(os.path.join(OUT, "04-pipeline.png"), dpi=150, bbox_inches="tight")
plt.close(fig)

# ---------- 图 2：三种度量方式 ----------
q = np.array([0.94, 0.33])            # 查询向量（模长约 1）
a = 1.5 * np.array([0.75, 0.55])      # 文档向量（模长约 1.4，刻意不归一化）
proj = (np.dot(a, q) / np.dot(q, q)) * q  # a 在 q 方向上的投影

fig, axes = plt.subplots(1, 3, figsize=(11, 4.1))

for ax in axes:
    ax.set_xlim(-0.12, 1.55)
    ax.set_ylim(-0.12, 1.32)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.scatter(0, 0, s=18, color="#202124")
    ax.annotate("", xy=q, xytext=(0, 0),
                arrowprops=dict(arrowstyle="-|>", color=BLUE_E, lw=2.2,
                                mutation_scale=16))
    ax.annotate("", xy=a, xytext=(0, 0),
                arrowprops=dict(arrowstyle="-|>", color=GREEN_E, lw=2.2,
                                mutation_scale=16))
    ax.text(q[0] + 0.04, q[1] - 0.03, "q", fontsize=12, color=BLUE_E)
    ax.text(a[0] + 0.04, a[1], "a", fontsize=12, color=GREEN_E)
    for s in ax.spines.values():
        s.set_edgecolor("#dadce0")

ax = axes[0]
ax.set_title("L2 欧氏距离：越小越近", fontsize=11.5)
ax.plot([q[0], a[0]], [q[1], a[1]], color=RED_E, lw=1.6, linestyle="--")
ax.text((q[0] + a[0]) / 2 + 0.09, (q[1] + a[1]) / 2, "d", fontsize=12,
        color=RED_E, fontweight="bold")
ax.text(0.5, -0.09, "端点直线距离，方向和模长一起看",
        transform=ax.transAxes, ha="center", fontsize=9.5, color=GRAY)

ax = axes[1]
ax.set_title("IP 内积：越大越近", fontsize=11.5)
ax.plot([a[0], proj[0]], [a[1], proj[1]], color=GRAY, lw=1.0, linestyle=":")
ax.plot([0, proj[0]], [0, proj[1]], color=RED_E, lw=2.6, alpha=0.85)
ax.text(proj[0] / 2 - 0.06, proj[1] / 2 - 0.02, "a 在 q 上的投影",
        fontsize=9.5, color=RED_E, ha="right")
ax.text(0.5, -0.09, "投影长度 × |q|，受模长影响",
        transform=ax.transAxes, ha="center", fontsize=9.5, color=GRAY)

ax = axes[2]
ax.set_title("COSINE 余弦：越大越近", fontsize=11.5)
ang_q = np.degrees(np.arctan2(q[1], q[0]))
ang_a = np.degrees(np.arctan2(a[1], a[0]))
ax.add_patch(Arc((0, 0), 0.9, 0.9, theta1=ang_q, theta2=ang_a,
                 color=RED_E, lw=1.8))
ax.text(0.52, 0.28, "θ", fontsize=13, color=RED_E)
ax.text(0.5, -0.09, "只看夹角，与模长无关",
        transform=ax.transAxes, ha="center", fontsize=9.5, color=GRAY)

fig.tight_layout(rect=(0, 0.06, 1, 1))
fig.text(0.5, 0.015, "归一化后（模长 = 1）：三者的排序完全一致",
         ha="center", fontsize=11,
         bbox=dict(boxstyle="round,pad=0.45", fc=YELLOW_F, ec=YELLOW_E, lw=1.4))

fig.savefig(os.path.join(OUT, "04-metrics.png"), dpi=150, bbox_inches="tight")
plt.close(fig)

print("done")
