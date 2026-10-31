# -*- coding: utf-8 -*-
"""专栏四第 04 篇《检索效果评估》配图：指标在链路中的位置 / 评估闭环"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

BLUE_F, BLUE_E = "#e8f0fe", "#4285f4"
RED_F, RED_E = "#fce8e6", "#ea4335"
GREEN_F, GREEN_E = "#e6f4ea", "#34a853"
YELL_F, YELL_E = "#fff8e1", "#f9ab00"

OUT = "D:/Documents/ob_new/01 后端/my-doc/ES与Milvus/专栏四-RAG实战/assets/"


def box(ax, x, y, w, h, text, fc, ec, fs=10, weight="normal", dashed=False):
    ax.add_patch(mpatches.FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.02",
        linewidth=1.4, facecolor=fc, edgecolor=ec,
        linestyle="--" if dashed else "-"))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, fontweight=weight)


def arrow(ax, x1, y1, x2, y2, color="#5f6368", dashed=False):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.6,
                                linestyle="--" if dashed else "-"))


# ---------- 图 1：各指标在链路中的位置 ----------
fig, ax = plt.subplots(figsize=(12.5, 5.8))
ax.set_xlim(0, 17); ax.set_ylim(0, 10); ax.axis("off")

chain = [
    (0.3, 1.8, "query"),
    (2.7, 2.6, "两路检索\nBM25 + 向量"),
    (6.0, 2.2, "RRF 合并\ntop 20"),
    (8.9, 2.2, "rerank\ntop 5"),
    (11.8, 2.2, "LLM\n生成"),
    (14.7, 1.6, "答案"),
]
y0, h0 = 4.0, 1.4
for x, w, t in chain:
    box(ax, x, y0, w, h0, t, BLUE_F, BLUE_E, fs=10)
for i in range(len(chain) - 1):
    x1 = chain[i][0] + chain[i][1]
    x2 = chain[i + 1][0]
    arrow(ax, x1, y0 + h0 / 2, x2, y0 + h0 / 2)

metrics = [
    (5.0, 3.6, "recall@k / hit rate\n候选里有没有正确答案", 7.1),
    (9.0, 3.2, "MRR / context precision\n排序排得好不好", 10.0),
    (13.4, 3.4, "faithfulness / answer relevancy\n答案是否可信、是否切题", 15.5),
]
for mx, mw, mt, anchor_x in metrics:
    box(ax, mx, 7.4, mw, 1.6, mt, YELL_F, YELL_E, fs=9.5)
    arrow(ax, mx + mw / 2, 7.4, anchor_x, y0 + h0, YELL_E, dashed=True)

ax.text(8.5, 2.6, "检索层指标定位层级，端到端指标看最终效果",
        ha="center", fontsize=10.5, color="#5f6368")
plt.savefig(OUT + "04-metrics-layers.png", dpi=150, bbox_inches="tight")
plt.close()

# ---------- 图 2：评估闭环 ----------
fig, ax = plt.subplots(figsize=(11.5, 6.6))
ax.set_xlim(0, 17); ax.set_ylim(0, 10); ax.axis("off")

box(ax, 0.5, 6.0, 2.8, 1.8, "改动\nchunk / 权重 / 模型", BLUE_F, BLUE_E)
box(ax, 4.3, 6.0, 2.8, 1.8, "跑评测集\n50~200 条", BLUE_F, BLUE_E)
box(ax, 8.1, 6.0, 3.4, 1.8, "指标对比\nrecall@5 / MRR / 忠实度", YELL_F, YELL_E,
    fs=9.5)
box(ax, 12.9, 7.4, 2.8, 1.4, "合入上线", GREEN_F, GREEN_E, fs=11)
box(ax, 6.0, 3.0, 2.8, 1.4, "回滚 / 再调", RED_F, RED_E, fs=11)
box(ax, 12.9, 2.2, 2.8, 1.4, "线上运行", BLUE_F, BLUE_E, fs=11)

arrow(ax, 3.3, 6.9, 4.3, 6.9)
arrow(ax, 7.1, 6.9, 8.1, 6.9)
arrow(ax, 11.5, 7.3, 12.9, 7.9, "#34a853")
ax.text(11.9, 7.8, "变好", fontsize=10, color="#34a853")
arrow(ax, 9.0, 6.0, 7.9, 4.4, "#ea4335")
ax.text(8.9, 5.1, "变差", fontsize=10, color="#ea4335")
arrow(ax, 6.0, 3.7, 1.9, 6.0, "#ea4335", dashed=True)
ax.text(3.2, 4.4, "回去重新改", fontsize=9.5, color="#ea4335", ha="center")
arrow(ax, 14.3, 7.4, 14.3, 3.6)
arrow(ax, 12.9, 2.9, 5.7, 6.0, "#5f6368", dashed=True)
ax.text(10.6, 4.7, "badcase 脱敏后回流\n评测集持续生长",
        fontsize=9.5, color="#5f6368", ha="center")
plt.savefig(OUT + "04-eval-loop.png", dpi=150, bbox_inches="tight")
plt.close()
print("done")
