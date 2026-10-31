# -*- coding: utf-8 -*-
"""第 06 篇配图：terms 分桶 + 嵌套指标；分片各自聚合再归并的误差来源"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

BLUE_FILL, BLUE_EDGE = "#e8f0fe", "#4285f4"
RED_FILL, RED_EDGE = "#fce8e6", "#ea4335"
GREEN_FILL, GREEN_EDGE = "#e6f4ea", "#34a853"
YELLOW_FILL, YELLOW_EDGE = "#fff8e1", "#f9ab00"

OUT = r"D:\Documents\ob_new\01 后端\my-doc\ES与Milvus\专栏一-ES实战\assets"

# ---------- 图 1：terms 分桶 + 桶内嵌套指标 ----------
fig, ax = plt.subplots(figsize=(8.6, 5.2))
ax.set_xlim(0, 10)
ax.set_ylim(0, 8)
ax.axis("off")


def box(x, y, w, h, text, fill, edge, fs=10, ls="-", bold=False):
    ax.add_patch(mpatches.FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.05",
        fc=fill, ec=edge, lw=1.6, linestyle=ls))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, color="#202124",
            fontweight="bold" if bold else "normal")


def arrow(x1, y1, x2, y2, color="#5f6368"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.8))


# 左侧：文档集合（8 个小方块，颜色代表分类）
box(0.3, 5.6, 2.2, 1.6, "文档集合\n（混着所有分类）", BLUE_FILL, BLUE_EDGE, 9.5, bold=True)
cats = ["支付", "退款", "账单", "支付", "退款", "账单", "支付", "退款"]
for i, c in enumerate(cats):
    row, col = divmod(i, 2)
    ax.add_patch(plt.Rectangle((0.55 + col * 0.9, 4.3 - row * 0.75), 0.7, 0.5,
                               fc=BLUE_FILL, ec=BLUE_EDGE, lw=1.2))
    ax.text(0.9 + col * 0.9, 4.55 - row * 0.75, c, ha="center", va="center", fontsize=7.5)

# 中间：terms 聚合
box(3.3, 3.2, 2.2, 1.6, "terms 聚合\nfield: category.keyword", BLUE_FILL, BLUE_EDGE, 9, bold=True)
arrow(2.6, 4.0, 3.2, 4.0)

# 右侧：三个桶，桶内嵌套指标
buckets = [
    ("桶：支付  doc_count = 3", "嵌套指标：avg(likes) = 18.2"),
    ("桶：退款  doc_count = 3", "嵌套指标：avg(likes) = 9.4"),
    ("桶：账单  doc_count = 2", "嵌套指标：avg(likes) = 12.5"),
]
for i, (btitle, metric) in enumerate(buckets):
    y = 6.0 - i * 2.4
    box(6.3, y, 3.3, 1.7, "", BLUE_FILL, BLUE_EDGE)
    ax.text(7.95, y + 1.28, btitle, ha="center", va="center", fontsize=9.5, fontweight="bold")
    box(6.55, y + 0.18, 2.8, 0.7, metric, GREEN_FILL, GREEN_EDGE, 8.5)
    arrow(5.6, 4.0, 6.25, y + 0.85)

ax.set_title("桶聚合 + 嵌套聚合：先分桶，桶里再算指标", fontsize=13, pad=10)
plt.tight_layout()
plt.savefig(f"{OUT}\\06-bucket-agg.png", dpi=150, bbox_inches="tight")
plt.close()

# ---------- 图 2：分片各自 top-N 归并丢桶 ----------
fig, ax = plt.subplots(figsize=(8.6, 6.4))
ax.set_xlim(0, 10)
ax.set_ylim(0, 9.6)
ax.axis("off")

# 上排：两个分片
shard_data = [
    (0.5, "分片 0", [("退款", 20), ("账单", 12), ("物流", 6)], ("苹果", 3)),
    (5.4, "分片 1", [("退款", 15), ("账单", 9), ("会员", 5)], ("苹果", 5)),
]
for x0, name, tops, lost in shard_data:
    box(x0, 6.2, 4.0, 3.0, "", BLUE_FILL, BLUE_EDGE)
    ax.text(x0 + 2.0, 8.85, name, ha="center", va="center", fontsize=11, fontweight="bold")
    ax.text(x0 + 2.0, 8.3, "本地聚合，只上报 top 3", ha="center", va="center", fontsize=8.5, color="#5f6368")
    for j, (t, c) in enumerate(tops):
        y = 7.85 - j * 0.5
        ax.text(x0 + 0.35, y, f"{t}：{c} 次", ha="left", va="center", fontsize=9.5)
    ax.text(x0 + 0.35, 7.85 - 3 * 0.5, f"{lost[0]}：{lost[1]} 次（本地第 4，没报上去）",
            ha="left", va="center", fontsize=9.5, color=RED_EDGE)

# 中间：协调节点
box(2.5, 3.9, 5.0, 1.3, "协调节点：归并两个分片上报的结果", YELLOW_FILL, YELLOW_EDGE, 10, bold=True)
arrow(2.5, 6.1, 4.0, 5.3)
arrow(7.5, 6.1, 6.0, 5.3)

# 下排：归并结果
box(1.5, 1.6, 7.0, 1.8, "", GREEN_FILL, GREEN_EDGE)
ax.text(5.0, 3.05, "归并后的全局 top 3", ha="center", va="center", fontsize=10.5, fontweight="bold")
ax.text(5.0, 2.5, "退款：35 次    账单：21 次    物流：6 次", ha="center", va="center", fontsize=10)
ax.text(5.0, 1.98, "苹果：全局 8 次（3 + 5），却没进任何分片的 top 3 —— 丢了",
        ha="center", va="center", fontsize=10, color=RED_EDGE, fontweight="bold")
arrow(5.0, 3.8, 5.0, 3.45)

ax.text(5.0, 0.8, "doc_count_error_upper_bound 标出的，就是这种「本地排不上号」导致的漏记上限",
        ha="center", va="center", fontsize=9.5, color="#5f6368")

ax.set_title("terms 聚合的误差从哪来：每个分片只看得到局部", fontsize=13, pad=10)
plt.tight_layout()
plt.savefig(f"{OUT}\\06-shard-agg-error.png", dpi=150, bbox_inches="tight")
plt.close()

print("done")
