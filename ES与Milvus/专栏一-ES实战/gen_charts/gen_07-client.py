# -*- coding: utf-8 -*-
"""第 07 篇配图：Java 客户端三代演进时间线 + bulk 与逐条写入对比"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

BLUE_FILL, BLUE_EDGE = "#e8f0fe", "#4285f4"
RED_FILL, RED_EDGE = "#fce8e6", "#ea4335"
GREEN_FILL, GREEN_EDGE = "#e6f4ea", "#34a853"
YELLOW_FILL, YELLOW_EDGE = "#fff8e1", "#f9ab00"

OUT = r"D:\Documents\ob_new\01 后端\my-doc\ES与Milvus\专栏一-ES实战\assets"

# ---------- 图 1：三代客户端时间线 ----------
fig, ax = plt.subplots(figsize=(9, 4.6))
ax.set_xlim(0, 10.6)
ax.set_ylim(0, 4.6)
ax.axis("off")

# 版本刻度：位置 -> 标签
ticks = [(0.5, "5.0"), (1.5, "5.5"), (3.0, "6.x"), (4.3, "7.0"),
         (5.6, "7.15"), (5.95, "7.16"), (8.0, "8.x")]
baseline = 0.55
ax.plot([0.3, 10.2], [baseline, baseline], color="#9aa0a6", lw=1.2)
for x, label in ticks:
    ax.plot([x, x], [baseline - 0.08, baseline + 0.08], color="#9aa0a6", lw=1.2)
    ax.text(x, baseline - 0.32, label, ha="center", va="top", fontsize=9, color="#5f6368")

# 三条横杠（左端对齐各自引入版本，右端到终点或移除点）
bars = [
    (3.7, 0.5, 4.3, "TransportClient（9300 二进制协议）", RED_FILL, RED_EDGE),
    (2.5, 1.5, 10.2, "RestHighLevelClient（HTTP REST）", YELLOW_FILL, YELLOW_EDGE),
    (1.3, 5.95, 10.2, "Java API Client（co.elastic.clients）", GREEN_FILL, GREEN_EDGE),
]
for y, x0, x1, label, fill, edge in bars:
    ax.add_patch(mpatches.FancyBboxPatch(
        (x0, y), x1 - x0, 0.52, boxstyle="round,pad=0.02",
        fc=fill, ec=edge, lw=1.6))
    ax.text(x0 + 0.15, y + 0.26, label, ha="left", va="center", fontsize=10, color="#202124")

# RHLC 废弃后的段：虚线框覆盖，表示"还能用但不再演进"
ax.add_patch(mpatches.FancyBboxPatch(
    (5.6, 2.5), 10.2 - 5.6, 0.52, boxstyle="round,pad=0.02",
    fc="none", ec=YELLOW_EDGE, lw=1.4, linestyle=(0, (4, 3))))
ax.text(7.6, 3.2, "7.15 官方废弃", ha="center", fontsize=9.5, color=YELLOW_EDGE)

# 关键事件标注
ax.annotate("7.0 整体移除", xy=(4.3, 3.96), xytext=(4.6, 4.35),
            arrowprops=dict(arrowstyle="->", color=RED_EDGE), fontsize=9.5, color=RED_EDGE)
ax.annotate("8.x 官方主推", xy=(8.0, 1.82), xytext=(8.6, 2.15),
            arrowprops=dict(arrowstyle="->", color=GREEN_EDGE), fontsize=9.5, color=GREEN_EDGE)

ax.set_title("ES Java 客户端三代演进：一部推翻重来史", fontsize=13, pad=10)
plt.tight_layout()
plt.savefig(f"{OUT}\\07-client-timeline.png", dpi=150, bbox_inches="tight")
plt.close()

# ---------- 图 2：逐条写入 vs bulk ----------
fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.4))

for axx in axes:
    axx.set_xlim(0, 10)
    axx.set_ylim(0, 8)
    axx.axis("off")


def sbox(axx, x, y, w, h, text, fill, edge, fs=10, bold=True):
    axx.add_patch(mpatches.FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.06", fc=fill, ec=edge, lw=1.6))
    axx.text(x + w / 2, y + h / 2, text, ha="center", va="center",
             fontsize=fs, fontweight="bold" if bold else "normal")


# 左图：逐条写入
ax = axes[0]
sbox(ax, 0.3, 3.0, 2.0, 2.0, "Java\n服务", BLUE_FILL, BLUE_EDGE, 11)
sbox(ax, 7.7, 3.0, 2.0, 2.0, "ES\n集群", BLUE_FILL, BLUE_EDGE, 11)
ys = [4.8, 4.3, 3.7, 3.2]
for y in ys:
    ax.annotate("", xy=(7.6, y), xytext=(2.4, 4.0),
                arrowprops=dict(arrowstyle="-|>", color=RED_EDGE, lw=1.4))
ax.text(5.0, 6.6, "第 1 条…第 N 条：每次一条", ha="center", fontsize=10, color=RED_EDGE)
ax.text(5.0, 1.3, "N 篇文档 = N 次网络往返\n每次都交一遍固定过路费",
        ha="center", fontsize=10, color=RED_EDGE)
ax.set_title("逐条写入", fontsize=12)

# 右图：bulk
ax = axes[1]
sbox(ax, 0.3, 3.0, 2.0, 2.0, "Java\n服务", BLUE_FILL, BLUE_EDGE, 11)
sbox(ax, 7.7, 3.0, 2.0, 2.0, "ES\n集群", GREEN_FILL, GREEN_EDGE, 11)
ax.annotate("", xy=(7.6, 4.0), xytext=(2.4, 4.0),
            arrowprops=dict(arrowstyle="-|>", color=GREEN_EDGE, lw=4))
ax.text(5.0, 4.5, "一次 bulk 请求（5~15 MB）", ha="center", fontsize=10, color=GREEN_EDGE)
ax.text(5.0, 1.3, "1 次网络往返\n协调节点再按分片归并，同分片一批处理",
        ha="center", fontsize=10, color="#202124")
ax.set_title("bulk 批量写入", fontsize=12)

fig.suptitle("同样是写 1000 条：1000 次往返 vs 1 次", fontsize=13, y=0.99)
plt.tight_layout()
plt.savefig(f"{OUT}\\07-bulk.png", dpi=150, bbox_inches="tight")
plt.close()

print("done")
