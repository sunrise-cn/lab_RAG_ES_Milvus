# -*- coding: utf-8 -*-
"""第 05 篇配图：索引三角权衡图 + ef 调参曲线图"""
import os
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

BLUE_FILL, BLUE_EDGE = "#e8f0fe", "#4285f4"
RED_FILL, RED_EDGE = "#fce8e6", "#ea4335"
GREEN_FILL, GREEN_EDGE = "#e6f4ea", "#34a853"
YELLOW_FILL, YELLOW_EDGE = "#fff8e1", "#f9ab00"

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
os.makedirs(OUT_DIR, exist_ok=True)


def bary(w_top, w_bl, w_br):
    """三角形重心坐标 -> 平面坐标。顶点：上(召回率高)、左下(延迟低)、右下(内存省)"""
    top = np.array([0.5, 0.97])
    bl = np.array([0.04, 0.08])
    br = np.array([0.96, 0.08])
    return w_top * top + w_bl * bl + w_br * br


def draw_triangle():
    fig, ax = plt.subplots(figsize=(8.4, 6.6))
    top = bary(1, 0, 0)
    bl = bary(0, 1, 0)
    br = bary(0, 0, 1)
    tri = plt.Polygon([top, bl, br], closed=True, fill=False,
                      edgecolor=BLUE_EDGE, linewidth=2)
    ax.add_patch(tri)

    # 三个顶点标签（黄框：这是权衡的三个目标），与索引标签一起在下方绘制并做重叠检查
    labels = [("召回率高", top, (0, 10)), ("延迟低", bl, (-8, -2)), ("内存省", br, (8, -2))]

    # 四个索引在三角中的位置 (召回权重, 延迟权重, 内存权重)
    points = [
        ("FLAT\n100% 召回 / 全库扫描", (0.46, 0.08, 0.46), RED_FILL, RED_EDGE),
        ("IVF_FLAT\n构建快 / 各项居中", (0.30, 0.36, 0.34), BLUE_FILL, BLUE_EDGE),
        ("HNSW\n召回高 / 延迟低 / 吃内存", (0.46, 0.44, 0.10), GREEN_FILL, GREEN_EDGE),
        ("DiskANN\n向量在盘上 / 延迟毫秒级", (0.30, 0.16, 0.54), BLUE_FILL, BLUE_EDGE),
    ]
    offsets = {"FLAT": (6, 44), "IVF_FLAT": (-34, 26),
               "HNSW": (-6, 32), "DiskANN": (16, -54)}
    anns = []
    for text, (wt, wl, wm), fc, ec in points:
        pos = bary(wt, wl, wm)
        ax.scatter([pos[0]], [pos[1]], s=340, c=fc, edgecolors=ec,
                   linewidths=2.2, zorder=5)
        ann = ax.annotate(text, xy=pos, xytext=offsets[text.split("\n")[0]],
                          textcoords="offset points",
                          ha="center", va="center", fontsize=10.5, zorder=6,
                          bbox=dict(boxstyle="round,pad=0.35", fc="white",
                                    ec=ec, alpha=0.95))
        anns.append((text.split("\n")[0], ann))
    # 顶点标签也参与重叠检查
    for text, pos, (dx, dy) in labels:
        _a = ax.annotate(text, xy=pos, xytext=(dx, dy), textcoords="offset points",
                         ha="center", va="center", fontsize=13, fontweight="bold",
                         color="#5f4b00",
                         bbox=dict(boxstyle="round,pad=0.45", fc=YELLOW_FILL,
                                   ec=YELLOW_EDGE))
        anns.append((text, _a))

    # 程序化自查：标注框两两是否重叠
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    boxes = [(name, a.get_window_extent(renderer)) for name, a in anns]
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            if boxes[i][1].overlaps(boxes[j][1]):
                print("OVERLAP:", boxes[i][0], "<->", boxes[j][0])

    ax.text(0.5, 0.015, "没有索引同时占满三个顶点：选索引 = 在三角里选位置",
            ha="center", va="center", fontsize=11, color="#5f6368")

    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.04, 1.12)
    ax.axis("off")
    fig.savefig(os.path.join(OUT_DIR, "05-triangle.png"), dpi=150,
                bbox_inches="tight")
    plt.close(fig)


def draw_ef_curve():
    fig, ax1 = plt.subplots(figsize=(8.2, 5.2))

    ef = np.array([8, 16, 32, 64, 128, 256, 512])
    recall = np.array([0.72, 0.83, 0.905, 0.955, 0.978, 0.988, 0.994])
    latency = np.array([1.1, 1.3, 1.8, 2.7, 4.5, 8.1, 14.8])

    ax1.set_xscale("log", base=2)
    ax1.set_xticks(ef)
    ax1.set_xticklabels([str(v) for v in ef])

    l1, = ax1.plot(ef, recall, "o-", color=GREEN_EDGE, linewidth=2,
                   markersize=6, label="recall@10")
    ax1.set_xlabel("ef（搜索时候选队列长度）")
    ax1.set_ylabel("召回率", color=GREEN_EDGE)
    ax1.tick_params(axis="y", labelcolor=GREEN_EDGE)
    ax1.set_ylim(0.65, 1.02)
    ax1.grid(True, alpha=0.25, linewidth=0.7)

    ax2 = ax1.twinx()
    l2, = ax2.plot(ef, latency, "s-", color=RED_EDGE, linewidth=2,
                   markersize=6, label="P99 延迟")
    ax2.set_ylabel("延迟 (ms)", color=RED_EDGE)
    ax2.tick_params(axis="y", labelcolor=RED_EDGE)
    ax2.set_ylim(0, 16)

    # 拐点标注
    ax1.annotate("拐点：再调大 ef，召回涨得慢，\n延迟还在直线涨 —— 工作点选这附近",
                 xy=(64, 0.955), xytext=(90, 0.78),
                 arrowprops=dict(arrowstyle="->", color=YELLOW_EDGE, lw=1.8),
                 fontsize=10.5,
                 bbox=dict(boxstyle="round,pad=0.4", fc=YELLOW_FILL, ec=YELLOW_EDGE))

    ax1.legend(handles=[l1, l2], loc="center right", fontsize=10, framealpha=0.95)
    ax1.set_title("固定测试集上扫 ef：用延迟买召回，买到拐点为止", fontsize=12.5)

    fig.savefig(os.path.join(OUT_DIR, "05-ef-curve.png"), dpi=150,
                bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    draw_triangle()
    draw_ef_curve()
    print("done:", os.listdir(OUT_DIR))
