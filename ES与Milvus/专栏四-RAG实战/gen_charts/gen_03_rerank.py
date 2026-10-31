# -*- coding: utf-8 -*-
"""专栏四第 03 篇《Rerank 精排》配图：双塔 vs cross-encoder / 召回精排漏斗"""
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


# ---------- 图 1：双塔 vs cross-encoder ----------
fig, axes = plt.subplots(1, 2, figsize=(11.5, 6.2))

ax = axes[0]
ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
ax.set_title("双塔（bi-encoder）：召回", fontsize=12.5, fontweight="bold",
             color="#4285f4", pad=10)
box(ax, 0.7, 8.4, 3.4, 1.1, "query 文本", BLUE_F, BLUE_E)
box(ax, 5.9, 8.4, 3.4, 1.1, "文档文本", BLUE_F, BLUE_E)
box(ax, 0.7, 6.5, 3.4, 1.1, "编码成 q 向量\n（在线，一次）", "#ffffff", BLUE_E, fs=9.5)
box(ax, 5.9, 6.5, 3.4, 1.1, "编码成 d 向量\n（离线，预计算）", "#ffffff", BLUE_E, fs=9.5)
arrow(ax, 2.4, 8.4, 2.4, 7.6)
arrow(ax, 7.6, 8.4, 7.6, 7.6)
box(ax, 3.0, 4.6, 4.0, 1.0, "余弦相似度", BLUE_F, BLUE_E)
arrow(ax, 2.4, 6.5, 3.8, 5.6)
arrow(ax, 7.6, 6.5, 6.2, 5.6)
box(ax, 0.7, 1.6, 8.6, 2.2,
    "两段文本互不相见，全部交互\n= 最后一次点积\n快：在线只编码 query + ANN 查找",
    YELL_F, YELL_E, fs=10)
arrow(ax, 5.0, 4.6, 5.0, 3.8)

ax = axes[1]
ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
ax.set_title("cross-encoder：精排", fontsize=12.5, fontweight="bold",
             color="#34a853", pad=10)
box(ax, 0.7, 8.4, 3.4, 1.1, "query 文本", BLUE_F, BLUE_E)
box(ax, 5.9, 8.4, 3.4, 1.1, "文档文本", BLUE_F, BLUE_E)
box(ax, 1.2, 6.3, 7.6, 1.0, "拼成一个序列：[CLS] query [SEP] 文档", BLUE_F, BLUE_E, fs=9.5)
arrow(ax, 2.4, 8.4, 3.0, 7.3)
arrow(ax, 7.6, 8.4, 7.0, 7.3)
box(ax, 1.2, 4.5, 7.6, 1.2, "transformer\n注意力层：query 每个词都能看到文档每个词",
    GREEN_F, GREEN_E, fs=9.5)
arrow(ax, 5.0, 6.3, 5.0, 5.7)
box(ax, 2.7, 2.8, 4.6, 1.0, "相关性分数", GREEN_F, GREEN_E, fs=11)
arrow(ax, 5.0, 4.5, 5.0, 3.8)
box(ax, 0.7, 0.6, 8.6, 1.6,
    "每对 (query, 文档) 都要完整跑一次模型\n无法预计算，做不了召回，只能精排",
    YELL_F, YELL_E, fs=10)
arrow(ax, 5.0, 2.8, 5.0, 2.2)

plt.tight_layout()
plt.savefig(OUT + "03-bi-vs-cross.png", dpi=150, bbox_inches="tight")
plt.close()

# ---------- 图 2：召回精排漏斗 ----------
fig, ax = plt.subplots(figsize=(10, 7.2))
ax.set_xlim(0, 12); ax.set_ylim(0, 11); ax.axis("off")

layers = [
    ("知识库：100 万 chunk", 8.6, BLUE_F, BLUE_E, "检索的原料"),
    ("双塔召回\nBM25 top 10 + 向量 top 10", 6.9, BLUE_F, BLUE_E,
     "快、全：毫秒级\n在线只算一次 query"),
    ("RRF 合并 top 20", 5.2, YELL_F, YELL_E, "只用排名，不用分数"),
    ("cross-encoder 精排", 3.5, GREEN_F, GREEN_E, "准：几十~几百 ms\n每对都跑一次模型"),
    ("top 5 塞给 LLM", 1.9, GREEN_F, GREEN_E, "少而精，省预算防噪声"),
]
widths = [8.0, 6.6, 5.0, 4.0, 3.2]
heights = [0.9, 1.3, 0.8, 1.1, 0.8]
for (text, y, fc, ec, note), w, h in zip(layers, widths, heights):
    x = 0.7 + (8.0 - w) / 2  # 居中对齐在 0.7~8.7
    box(ax, x, y, w, h, text, fc, ec, fs=10.5)
    ax.text(9.0, y + h / 2, note, ha="left", va="center", fontsize=9.5,
            color="#5f6368")
for i in range(len(layers) - 1):
    y_top = layers[i][1]
    y_next = layers[i + 1][1] + heights[i + 1]
    arrow(ax, 4.7, y_top, 4.7, y_next)
plt.savefig(OUT + "03-funnel.png", dpi=150, bbox_inches="tight")
plt.close()
print("done")
