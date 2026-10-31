# -*- coding: utf-8 -*-
"""专栏四第 01 篇《文档切分》配图：chunk 大小三态 / 递归切分流程 / overlap"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

BLUE_F, BLUE_E = "#e8f0fe", "#4285f4"
RED_F, RED_E = "#fce8e6", "#ea4335"
GREEN_F, GREEN_E = "#e6f4ea", "#34a853"
YELL_F, YELL_E = "#fff8e1", "#f9ab00"

OUT = "D:/Documents/ob_new/01 后端/my-doc/ES与Milvus/专栏四-RAG实战/assets/"


def box(ax, x, y, w, h, text, fc, ec, fs=10, weight="normal", tc="#202124"):
    ax.add_patch(mpatches.FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.02",
        linewidth=1.4, facecolor=fc, edgecolor=ec))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, fontweight=weight, color=tc)


def arrow(ax, x1, y1, x2, y2, color="#5f6368"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.6))


# ---------- 图 1：chunk 大小三态 ----------
fig, axes = plt.subplots(1, 3, figsize=(12.5, 5.6))
titles = ["切太大：语义稀释", "合适：语义单一且完整", "切太小：上下文碎"]
colors = [(RED_F, RED_E), (GREEN_F, GREEN_E), (RED_F, RED_E)]
chunks = [
    ["退款政策", "配送时效", "发票开具"],
    ["退款时效\n（单主题）"],
    ["详见附录三"],
]
chunk_h = [2.6, 1.7, 0.6]
verdicts = [
    "向量 = 三个主题的“平均位置”\n和谁都不像，检索排不上",
    "主题集中，向量定位准\n检索命中，内容能直接用",
    "语义约等于零\n就算命中，LLM 也答不了",
]
for i, ax in enumerate(axes):
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
    fc, ec = colors[i]
    ax.set_title(titles[i], fontsize=13, fontweight="bold", color=ec, pad=10)
    box(ax, 1, 5.4, 8, chunk_h[i], "", fc, ec)
    cy = 5.4 + chunk_h[i] / 2
    if len(chunks[i]) == 1:
        ax.text(5, cy, chunks[i][0], ha="center", va="center", fontsize=11)
    else:
        for j, t in enumerate(chunks[i]):
            ax.text(5, cy + 0.75 - j * 0.75, t, ha="center", va="center", fontsize=10)
    ax.text(5, 4.6, f"约 {['1500+ 字', '500 字', '20 字'][i]}",
            ha="center", va="center", fontsize=10, color="#5f6368")
    arrow(ax, 5, 4.2, 5, 3.4)
    box(ax, 0.8, 1.2, 8.4, 2.1, verdicts[i], "#ffffff", ec, fs=10.5)
plt.tight_layout()
plt.savefig(OUT + "01-chunk-size.png", dpi=150, bbox_inches="tight")
plt.close()

# ---------- 图 2：递归切分降级流程 ----------
fig, ax = plt.subplots(figsize=(9.5, 8.2))
ax.set_xlim(0, 10); ax.set_ylim(0, 11.8); ax.axis("off")

steps = [
    ("整篇文档", BLUE_F, BLUE_E),
    ("按 \\n\\n（段落）切", BLUE_F, BLUE_E),
    ("按 \\n（行）切", BLUE_F, BLUE_E),
    ("按 。（句子）切", BLUE_F, BLUE_E),
    ("按字符硬切\n（最后手段）", RED_F, RED_E),
]
ys = [10.6, 8.9, 7.0, 5.1, 3.0]
for (t, fc, ec), y in zip(steps, ys):
    box(ax, 1.0, y, 3.6, 1.0, t, fc, ec, fs=10.5)
# 判断标签与箭头
checks = ["块 ≤ max ？", "块 ≤ max ？", "块 ≤ max ？", "还超长？"]
for i, y in enumerate(ys[:-1]):
    mid = (y + ys[i + 1] + 1.0) / 2
    arrow(ax, 2.8, y, 2.8, ys[i + 1] + 1.0)
    ax.text(3.0, mid, "否", fontsize=10, color="#ea4335", va="center")
    box(ax, 5.0, mid - 0.45, 2.2, 0.9, checks[i], YELL_F, YELL_E, fs=10)
    arrow(ax, 2.8, y, 5.0, mid)
    # 是 -> 输出
    arrow(ax, 7.2, mid, 7.9, 4.9, "#34a853")
    ax.text(7.3, mid + 0.18, "是", fontsize=10, color="#34a853", va="center")
# 输出框
box(ax, 7.9, 4.1, 1.6, 1.6, "输出\nchunk", GREEN_F, GREEN_E, fs=10.5)
ax.text(2.8, 0.9, "分隔符优先级：段落 > 行 > 句子 > 字符 —— 结构能用就用结构，硬切永远排最后",
        ha="center", fontsize=10.5, color="#5f6368")
plt.savefig(OUT + "01-recursive.png", dpi=150, bbox_inches="tight")
plt.close()

# ---------- 图 3：overlap ----------
fig, axes = plt.subplots(2, 1, figsize=(11, 5.2))
ax = axes[0]
ax.set_xlim(0, 14); ax.set_ylim(0, 4); ax.axis("off")
ax.set_title("无 overlap：关键句被边界切断", fontsize=12, fontweight="bold",
             color="#ea4335")
box(ax, 0.5, 1.0, 6.3, 1.8, "chunk A\n……超过 7 天可", "#ffffff", "#ea4335", fs=10.5)
box(ax, 7.2, 1.0, 6.3, 1.8, "chunk B\n申请退款，到账 80%……", "#ffffff", "#ea4335", fs=10.5)
ax.text(7.0, 3.4, "边界", ha="center", fontsize=10, color="#ea4335")
ax.text(7.0, 0.45, "A 不知道“7 天”限制什么，B 不知道“退款”指哪件事",
        ha="center", fontsize=10, color="#5f6368")

ax = axes[1]
ax.set_xlim(0, 14); ax.set_ylim(0, 4); ax.axis("off")
ax.set_title("有 overlap：关键句在两个 chunk 里各存一份完整副本", fontsize=12,
             fontweight="bold", color="#34a853")
box(ax, 0.5, 1.0, 7.0, 1.8, "chunk A\n……其他内容\n超过 7 天可申请退款", "#ffffff", "#34a853", fs=10.5)
box(ax, 6.0, 1.0, 7.5, 1.8, "chunk B\n超过 7 天可申请退款\n其他内容……", "#ffffff", "#34a853", fs=10.5)
# 重叠高亮
ax.add_patch(mpatches.FancyBboxPatch((6.05, 1.05), 1.4, 1.7,
             boxstyle="round,pad=0.02", linewidth=0, facecolor="#34a853", alpha=0.15))
ax.text(6.75, 3.4, "重叠区", ha="center", fontsize=10, color="#34a853")
ax.text(7.0, 0.45, "代价：存储膨胀、重复召回需要去重 —— 是给“切不准”买的保险",
        ha="center", fontsize=10, color="#5f6368")
plt.tight_layout()
plt.savefig(OUT + "01-overlap.png", dpi=150, bbox_inches="tight")
plt.close()
print("done")
