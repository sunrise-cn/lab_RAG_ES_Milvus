# -*- coding: utf-8 -*-
"""专栏四第 02 篇《BM25 与混合检索》配图：词频曲线对比 / RRF 合并流程"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

BLUE_F, BLUE_E = "#e8f0fe", "#4285f4"
RED_F, RED_E = "#fce8e6", "#ea4335"
GREEN_F, GREEN_E = "#e6f4ea", "#34a853"
YELL_F, YELL_E = "#fff8e1", "#f9ab00"

OUT = "D:/Documents/ob_new/01 后端/my-doc/ES与Milvus/专栏四-RAG实战/assets/"


def box(ax, x, y, w, h, text, fc, ec, fs=10, weight="normal"):
    ax.add_patch(mpatches.FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.02",
        linewidth=1.4, facecolor=fc, edgecolor=ec))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, fontweight=weight)


def arrow(ax, x1, y1, x2, y2, color="#5f6368"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.6))


# ---------- 图 1：TF-IDF vs BM25 词频曲线 ----------
fig, ax = plt.subplots(figsize=(8.2, 5))
f = np.linspace(0, 15, 300)
k1 = 1.2
bm25 = f * (k1 + 1) / (f + k1)          # BM25 的 TF 项，渐近 k1+1
tf = f                                   # 线性 TF
ax.plot(f, tf / tf.max(), color="#ea4335", lw=2.2, label="TF-IDF：线性增长")
ax.plot(f, bm25 / (k1 + 1), color="#34a853", lw=2.2,
        label="BM25：饱和增长（k1=1.2）")

ax.set_xlabel("词频 f（词在文档中出现的次数）", fontsize=11)
ax.set_ylabel("TF 项贡献（归一化）", fontsize=11)
ax.set_xlim(0, 15); ax.set_ylim(0, 1.05)
ax.spines[["top", "right"]].set_visible(False)
ax.legend(loc="lower right", fontsize=10, frameon=False)

ax.annotate("f = k1 = 1.2 时\n贡献已过半", xy=(1.2, 0.5), xytext=(4.2, 0.42),
            fontsize=10, color="#34a853",
            arrowprops=dict(arrowstyle="->", color="#34a853"))
ax.annotate("第 10 次出现\n几乎不再加分", xy=(10, bm25[199] / (k1 + 1)),
            xytext=(10.3, 0.55), fontsize=10, color="#34a853",
            arrowprops=dict(arrowstyle="->", color="#34a853"))
ax.annotate("线性 TF 把高频\n系统性高估", xy=(11.5, 11.5 / 15), xytext=(7.0, 0.86),
            fontsize=10, color="#ea4335",
            arrowprops=dict(arrowstyle="->", color="#ea4335"))
ax.set_title("同样的词频，两种打分直觉", fontsize=12.5, pad=10)
plt.tight_layout()
plt.savefig(OUT + "02-tf-bm25.png", dpi=150, bbox_inches="tight")
plt.close()

# ---------- 图 2：混合检索两路合并 ----------
fig, ax = plt.subplots(figsize=(12.5, 6.8))
ax.set_xlim(0, 17); ax.set_ylim(0, 10.6); ax.axis("off")

box(ax, 0.3, 4.4, 2.0, 1.8, "用户 query", BLUE_F, BLUE_E, fs=11)

box(ax, 3.4, 7.3, 2.6, 1.8, "BM25 检索\n（ES）", BLUE_F, BLUE_E, fs=11)
box(ax, 3.4, 1.5, 2.6, 1.8, "向量检索\n（Milvus）", BLUE_F, BLUE_E, fs=11)

box(ax, 6.9, 6.1, 2.3, 3.6, "排名榜\n\n1. D3\n2. D7\n3. D1\n4. D5\n5. D2",
    "#ffffff", BLUE_E, fs=10)
box(ax, 6.9, 0.3, 2.3, 3.6, "排名榜\n\n1. D7\n2. D2\n3. D3\n4. D9\n5. D4",
    "#ffffff", BLUE_E, fs=10)

box(ax, 10.2, 3.4, 3.0, 3.6,
    "RRF 合并\n\n$score(d)=\\sum\\dfrac{1}{60+rank}$\n\n只用排名\n不用分数",
    YELL_F, YELL_E, fs=11)

box(ax, 14.3, 3.7, 2.3, 3.0, "最终榜单\n\n1. D7\n2. D3\n3. D2",
    GREEN_F, GREEN_E, fs=11)

arrow(ax, 2.3, 5.3, 3.4, 8.0)
arrow(ax, 2.3, 5.3, 3.4, 2.4)
arrow(ax, 6.0, 8.2, 6.9, 8.0)
arrow(ax, 6.0, 2.4, 6.9, 2.2)
arrow(ax, 9.2, 7.4, 10.2, 6.0)
arrow(ax, 9.2, 3.0, 10.2, 4.4)
arrow(ax, 13.2, 5.2, 14.3, 5.2)

ax.text(15.45, 7.6, "两路都靠前的 D7 胜出\n（单路第 1 不再垄断）",
        ha="center", fontsize=9.5, color="#5f6368")
plt.tight_layout()
plt.savefig(OUT + "02-hybrid-rrf.png", dpi=150, bbox_inches="tight")
plt.close()
print("done")
