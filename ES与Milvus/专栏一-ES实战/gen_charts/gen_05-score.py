# -*- coding: utf-8 -*-
"""第 05 篇配图：BM25 词频饱和曲线 + function_score 执行流程"""
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

# 配色常量
BLUE_FILL, BLUE_EDGE = "#e8f0fe", "#4285f4"
RED_FILL, RED_EDGE = "#fce8e6", "#ea4335"
GREEN_FILL, GREEN_EDGE = "#e6f4ea", "#34a853"
YELLOW_FILL, YELLOW_EDGE = "#fff8e1", "#f9ab00"

OUT = r"D:\Documents\ob_new\01 后端\my-doc\ES与Milvus\专栏一-ES实战\assets"

# ---------- 图 1：TF 饱和曲线 ----------
fig, ax = plt.subplots(figsize=(7, 4.2))
freq = np.arange(0, 21)
k1 = 1.2
bm25 = (k1 + 1) * freq / (freq + k1)          # BM25 的 TF 项（b=0 简化）
naive = freq * 0.5                              # 朴素线性计数（示意斜率）

ax.plot(freq, naive, color=RED_EDGE, lw=2, label="朴素方案：词频线性计分")
ax.plot(freq, bm25, color=GREEN_EDGE, lw=2.5, label="BM25：词频饱和")

# 标注饱和区
ax.axhline(y=k1 + 1, color=GREEN_EDGE, ls="--", lw=1, alpha=0.5)
ax.annotate("得分封顶：出现 100 次\n也不会比 10 次多多少",
            xy=(18, k1 + 1), xytext=(9.5, 3.1),
            arrowprops=dict(arrowstyle="->", color=GREEN_EDGE),
            fontsize=10, color=GREEN_EDGE)
ax.annotate("前几次命中涨分最快",
            xy=(2.3, (k1 + 1) * 2.3 / (2.3 + k1)), xytext=(3.2, 0.55),
            arrowprops=dict(arrowstyle="->", color=GREEN_EDGE),
            fontsize=10, color=GREEN_EDGE)
ax.annotate("堆词频会霸榜",
            xy=(14, 7.0), xytext=(13.2, 8.2),
            arrowprops=dict(arrowstyle="->", color=RED_EDGE),
            fontsize=10, color=RED_EDGE)

ax.set_xlabel("查询词在文档中出现的次数（词频）", fontsize=11)
ax.set_ylabel("该词贡献的得分", fontsize=11)
ax.set_xlim(0, 20)
ax.set_ylim(0, 10)
ax.legend(loc="upper left", fontsize=10, frameon=False)
ax.set_title("BM25 对词频的修正：边际递减", fontsize=13, pad=10)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
plt.tight_layout()
plt.savefig(f"{OUT}\\05-bm25-tf.png", dpi=150, bbox_inches="tight")
plt.close()

# ---------- 图 2：function_score 流程 ----------
fig, ax = plt.subplots(figsize=(8.6, 5.4))
ax.set_xlim(0, 10)
ax.set_ylim(0, 8)
ax.axis("off")


def box(x, y, w, h, text, fill, edge, fs=10):
    ax.add_patch(plt.Rectangle((x, y), w, h, fc=fill, ec=edge, lw=1.6,
                               joinstyle="round"))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, color="#202124")


def arrow(x1, y1, x2, y2, color="#5f6368"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.6))


# 第 1 层：query 算 BM25
box(1.5, 6.6, 7, 1.0, "function_score 内部的 query：bool + match，先算出 BM25 分", BLUE_FILL, BLUE_EDGE, 10.5)

# 第 2 层：两份文档各自得分
box(0.6, 4.4, 3.8, 1.0, "论坛帖子\n_score = 5.2", BLUE_FILL, BLUE_EDGE)
box(5.6, 4.4, 3.8, 1.0, "官方文档\n_score = 3.1", BLUE_FILL, BLUE_EDGE)
arrow(3.5, 6.6, 2.5, 5.4)
arrow(6.5, 6.6, 7.5, 5.4)

# 第 3 层：functions 过滤加权
box(1.5, 2.6, 7, 1.0, "functions：filter 命中 source = official 的文档，weight = 10", GREEN_FILL, GREEN_EDGE, 10.5)
arrow(2.5, 4.4, 3.5, 3.6)
arrow(7.5, 4.4, 6.5, 3.6)

# 第 4 层：最终分数
box(0.6, 0.5, 3.8, 1.0, "帖子：未命中，5.2\n（BM25 高也没用上加权）", BLUE_FILL, BLUE_EDGE, 9.5)
box(5.6, 0.5, 3.8, 1.0, "官方文档：3.1 × 10 = 31\nboost_mode = multiply，置顶", GREEN_FILL, GREEN_EDGE, 9.5)
arrow(3.5, 2.6, 2.5, 1.5)
arrow(6.5, 2.6, 7.5, 1.5)

ax.set_title("function_score：BM25 打完分，业务规则再接管一轮", fontsize=13, pad=12)
plt.tight_layout()
plt.savefig(f"{OUT}\\05-function-score.png", dpi=150, bbox_inches="tight")
plt.close()

print("done")
