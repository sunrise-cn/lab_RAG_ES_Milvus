# -*- coding: utf-8 -*-
"""专栏四第 05 篇《工程化落地》配图：upsert 残留 vs 先删后插 / 双写一致性架构"""
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


# ---------- 图 1：upsert 残留 vs 先删后插 ----------
fig, axes = plt.subplots(2, 1, figsize=(11.5, 6.4))

ax = axes[0]
ax.set_xlim(0, 15); ax.set_ylim(0, 6); ax.axis("off")
ax.set_title("upsert：覆盖得了写的，删不掉没写的", fontsize=12,
             fontweight="bold", color="#ea4335")
ax.text(7.5, 4.9, "文档 8000 字改成 3000 字：chunk 从 20 个变 8 个，upsert 只写了主键 1~8",
        ha="center", fontsize=10, color="#5f6368")
for i in range(20):
    x = 0.5 + i * 0.7
    is_new = i < 8
    fc = GREEN_F if is_new else RED_F
    ec = GREEN_E if is_new else RED_E
    ax.add_patch(mpatches.FancyBboxPatch((x, 2.6), 0.62, 1.1,
                 boxstyle="round,pad=0.01", linewidth=1.2,
                 facecolor=fc, edgecolor=ec))
    ax.text(x + 0.31, 3.15, str(i + 1), ha="center", va="center", fontsize=8)
ax.annotate("新内容", xy=(3.0, 3.7), xytext=(2.2, 4.35), fontsize=10,
            color="#34a853", arrowprops=dict(arrowstyle="->", color="#34a853"))
ax.annotate("旧 chunk 残留：\n讲已不存在的内容\n照样被检索出来", xy=(11.5, 2.6),
            xytext=(10.2, 0.7), fontsize=9.5, color="#ea4335",
            arrowprops=dict(arrowstyle="->", color="#ea4335"))

ax = axes[1]
ax.set_xlim(0, 15); ax.set_ylim(0, 6); ax.axis("off")
ax.set_title("先删后插：按 doc_id 清干净，结果天然幂等", fontsize=12,
             fontweight="bold", color="#34a853")
box(ax, 0.5, 2.4, 3.2, 1.5, "DELETE\ndoc_id = x\n（20 个全删）", RED_F, RED_E,
    fs=10)
arrow(ax, 3.7, 3.15, 4.6, 3.15)
for i in range(8):
    x = 4.7 + i * 0.7
    ax.add_patch(mpatches.FancyBboxPatch((x, 2.6), 0.62, 1.1,
                 boxstyle="round,pad=0.01", linewidth=1.2,
                 facecolor=GREEN_F, edgecolor=GREEN_E))
    ax.text(x + 0.31, 3.15, str(i + 1), ha="center", va="center", fontsize=8)
ax.text(7.5, 4.7, "插入新的 8 个", ha="center", fontsize=10, color="#34a853")
ax.text(7.5, 1.3, "该文档的 chunk 集合 = 最新版，重试多少次结果都一样（幂等）",
        ha="center", fontsize=10, color="#5f6368")
plt.tight_layout()
plt.savefig(OUT + "05-upsert-vs-delete.png", dpi=150, bbox_inches="tight")
plt.close()

# ---------- 图 2：双写一致性架构 ----------
fig, ax = plt.subplots(figsize=(11.5, 7.2))
ax.set_xlim(0, 16); ax.set_ylim(0, 12); ax.axis("off")

box(ax, 5.5, 10.0, 5.0, 1.6, "文档库（source of truth）\n文档变更：doc_id + 新版本",
    BLUE_F, BLUE_E, fs=10.5)
box(ax, 5.5, 7.6, 5.0, 1.5, "同步程序\n按 doc_id 先删后插（幂等）", BLUE_F, BLUE_E,
    fs=10.5)
box(ax, 1.0, 5.0, 4.2, 1.5, "ES\nchunk 正文 + BM25", BLUE_F, BLUE_E, fs=10.5)
box(ax, 10.8, 5.0, 4.2, 1.5, "Milvus\n向量", BLUE_F, BLUE_E, fs=10.5)
box(ax, 5.8, 5.0, 4.4, 1.5, "重试队列\n失败不回滚，稍后重放", RED_F, RED_E, fs=10)
box(ax, 5.0, 1.8, 6.0, 1.5, "对账任务（定时，如每天）\n版本对不上就重新同步该 doc_id",
    YELL_F, YELL_E, fs=10, dashed=True)

arrow(ax, 8.0, 10.0, 8.0, 9.1)
arrow(ax, 6.6, 7.6, 4.0, 6.5)
arrow(ax, 9.4, 7.6, 12.0, 6.5)
arrow(ax, 5.2, 5.9, 5.8, 5.9, "#ea4335", dashed=True)
arrow(ax, 10.8, 5.9, 10.2, 5.9, "#ea4335", dashed=True)
ax.text(4.6, 6.1, "写失败", fontsize=9, color="#ea4335")
arrow(ax, 8.0, 6.5, 8.0, 7.6, "#ea4335", dashed=True)
ax.text(8.3, 7.0, "重放（幂等，安全）", fontsize=9, color="#ea4335")
arrow(ax, 5.6, 3.3, 3.0, 5.0, "#f9ab00", dashed=True)
arrow(ax, 10.4, 3.3, 13.0, 5.0, "#f9ab00", dashed=True)
ax.text(1.0, 0.6, "检索场景的宽容：不一致 = 用户看到旧文档，不是资损 —— "
        "最终一致 + 异步补偿就够，不上分布式事务",
        fontsize=10, color="#5f6368")
plt.savefig(OUT + "05-dual-write.png", dpi=150, bbox_inches="tight")
plt.close()
print("done")
