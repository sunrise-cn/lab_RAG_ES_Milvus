# -*- coding: utf-8 -*-
"""第 04 篇配图：IK 两种粒度 / 分词不一致导致 miss"""
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

def arrow(ax, x1, y1, x2, y2, color, lw=1.6, ls="-", rad=0.0):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=14,
                        color=color, lw=lw, linestyle=ls, connectionstyle=f"arc3,rad={rad}")
    ax.add_patch(a)

# ============================================================
# 图 1：ik_max_word vs ik_smart
# ============================================================
fig, ax = plt.subplots(figsize=(11, 6.8))
ax.set_xlim(0, 12)
ax.set_ylim(0, 10.0)
ax.axis("off")

box(ax, 3.5, 8.9, 5.0, 0.85, "同一句话：中华人民共和国", BLUE_F, BLUE_E, fs=11.5, bold=True)

# 左：ik_max_word
arrow(ax, 5.0, 8.85, 2.9, 7.9, BLUE_E, lw=1.8)
box(ax, 0.4, 6.9, 4.7, 0.9, "ik_max_word（最细粒度）", BLUE_F, BLUE_E, fs=10.5)
terms_max = ["中华人民共和国", "中华人民", "中华", "华人", "人民", "共和国", "共和", "国"]
for i, t in enumerate(terms_max):
    cx = 0.7 + (i % 4) * 1.15
    cy = 5.7 - (i // 4) * 0.75
    box(ax, cx, cy, 1.05, 0.55, t, BLUE_F, BLUE_E, fs=8.5)

# 右：ik_smart
arrow(ax, 7.0, 8.85, 9.1, 7.9, BLUE_E, lw=1.8)
box(ax, 6.9, 6.9, 4.7, 0.9, "ik_smart（最粗粒度）", BLUE_F, BLUE_E, fs=10.5)
box(ax, 7.4, 5.35, 3.7, 0.7, "中华人民共和国", BLUE_F, BLUE_E, fs=9.5, lw=1.8)

# smart 的词必在 max_word 集合里
arrow(ax, 7.35, 5.7, 5.35, 5.75, GREEN_E, lw=1.4, ls="--")
ax.text(6.15, 4.7, "smart 切出的词\n一定在 max_word 的\n词集合里", ha="center", fontsize=9,
        color=GREEN_E)

box(ax, 0.4, 1.9, 11.2, 1.5,
    "由此推出组合的安全方向：\n索引 ik_max_word（词全存，搜索侧无论切成什么粒度都能命中）+ 搜索 ik_smart（词少，干扰少）\n"
    "反过来（索引 smart + 搜索 max_word）：细粒度的词在词典里不存在，查不到",
    YELLOW_F, YELLOW_E, fs=9.5)

fig.savefig(r"D:\Documents\ob_new\01 后端\my-doc\ES与Milvus\专栏一-ES实战\assets\04-ik-granularity.png",
            dpi=150, bbox_inches="tight")
plt.close(fig)

# ============================================================
# 图 2：索引分词与搜索分词不一致
# ============================================================
fig, ax = plt.subplots(figsize=(11, 6.6))
ax.set_xlim(0, 12)
ax.set_ylim(0, 9.6)
ax.axis("off")

# 文档写入
box(ax, 0.4, 8.2, 4.6, 1.0, '写入：content = "苹果手机电池不耐用"', BLUE_F, BLUE_E, fs=9.5)
# 查询
box(ax, 7.0, 8.2, 4.6, 1.0, '搜索：match "手机电池"\n（误配 analyzer: standard）', RED_F, RED_E, fs=9.5)

# 索引侧词典
arrow(ax, 2.7, 8.15, 2.7, 7.35, BLUE_E, lw=1.8)
box(ax, 0.4, 4.3, 4.6, 3.0,
    "索引侧词典（ik_max_word）\n\n苹果   手机   电池\n耐用   不耐用   …", BLUE_F, BLUE_E, fs=10)

# 搜索侧切词
arrow(ax, 9.3, 8.15, 9.3, 7.35, RED_E, lw=1.8)
box(ax, 7.0, 4.3, 4.6, 3.0,
    "搜索侧切出的词（standard）\n\n手   机   电   池\n（四个单字）", RED_F, RED_E, fs=10)

# 交集为空
box(ax, 0.4, 2.6, 11.2, 1.0,
    "拿「手 / 机 / 电 / 池」去词典里找：一个都找不到 → 0 条命中", RED_F, RED_E, fs=10, lw=1.8)

# 修复
box(ax, 0.4, 0.8, 11.2, 1.3,
    "修复：两端用同一套分词（查询不手写 analyzer，从 mapping 一处拿配置）\n"
    "搜索侧也走 IK：切出「手机」「电池」→ 在词典里，命中",
    GREEN_F, GREEN_E, fs=9.5)

fig.savefig(r"D:\Documents\ob_new\01 后端\my-doc\ES与Milvus\专栏一-ES实战\assets\04-analyzer-mismatch.png",
            dpi=150, bbox_inches="tight")
plt.close(fig)
print("done")
