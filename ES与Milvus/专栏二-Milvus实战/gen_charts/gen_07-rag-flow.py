# -*- coding: utf-8 -*-
"""第 07 篇配图：一次 RAG 检索请求中各角色的协作（客户端在链路中的位置）"""
import os
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

BLUE_FILL, BLUE_EDGE = "#e8f0fe", "#4285f4"
RED_FILL, RED_EDGE = "#fce8e6", "#ea4335"
GREEN_FILL, GREEN_EDGE = "#e6f4ea", "#34a853"
YELLOW_FILL, YELLOW_EDGE = "#fff8e1", "#f9ab00"

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
os.makedirs(OUT_DIR, exist_ok=True)


def box(ax, x, y, w, h, text, fc, ec, fontsize=11, bold=False):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06",
                       fc=fc, ec=ec, linewidth=1.9)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fontsize, zorder=5,
            fontweight="bold" if bold else "normal")


def arrow(ax, p1, p2, color="#5f6368", style="-|>", lw=1.7, ls="-"):
    a = FancyArrowPatch(p1, p2, arrowstyle=style, mutation_scale=15,
                        linewidth=lw, color=color, linestyle=ls,
                        shrinkA=2, shrinkB=2)
    ax.add_patch(a)


def label(ax, x, y, text, color="#333"):
    ax.text(x, y, text, ha="center", va="center", fontsize=9.5, color=color,
            zorder=6, bbox=dict(boxstyle="round,pad=0.22", fc="white", ec="none",
                                alpha=0.9))


def draw():
    fig, ax = plt.subplots(figsize=(10.8, 5.6))
    ax.set_xlim(0, 13.2)
    ax.set_ylim(0, 6.6)
    ax.axis("off")

    # 角色框
    box(ax, 0.25, 2.85, 1.7, 1.15, "用户", BLUE_FILL, BLUE_EDGE, fontsize=12)
    box(ax, 2.9, 2.6, 2.6, 1.65, "业务服务\n(Spring 应用)", BLUE_FILL, BLUE_EDGE,
        fontsize=12, bold=True)
    box(ax, 7.2, 5.15, 2.7, 1.1, "embedding 服务", YELLOW_FILL, YELLOW_EDGE)
    box(ax, 7.2, 2.85, 2.7, 1.15, "Milvus\nsearch / insert", GREEN_FILL,
        GREEN_EDGE, fontsize=12, bold=True)
    box(ax, 7.2, 0.55, 2.7, 1.1, "LLM", YELLOW_FILL, YELLOW_EDGE)

    ax.text(8.55, 2.55, "这一篇的主角：客户端的两个动作",
            ha="center", fontsize=9.5, color="#1e7e34")

    # 用户 <-> 业务服务
    arrow(ax, (1.95, 3.55), (2.85, 3.55))
    label(ax, 2.4, 3.85, "1 提问")
    arrow(ax, (2.85, 3.25), (1.95, 3.25))
    label(ax, 2.4, 2.95, "8 回答")

    # 业务服务 <-> embedding 服务
    arrow(ax, (5.5, 4.25), (7.15, 5.5))
    label(ax, 6.3, 5.25, "2 向量化")
    arrow(ax, (7.15, 5.15), (5.5, 3.95), color="#9aa0a6", ls="--")
    label(ax, 6.3, 4.15, "3 返回向量")

    # 业务服务 <-> Milvus
    arrow(ax, (5.5, 3.42), (7.15, 3.42))
    label(ax, 6.3, 3.7, "4 search + filter")
    arrow(ax, (7.15, 3.08), (5.5, 3.08), color="#9aa0a6", ls="--")
    label(ax, 6.3, 2.8, "5 top-k 结果")

    # 业务服务 <-> LLM
    arrow(ax, (5.5, 2.6), (7.15, 1.35))
    label(ax, 6.3, 1.65, "6 拼上下文")
    arrow(ax, (7.15, 1.65), (5.5, 2.9), color="#9aa0a6", ls="--")
    label(ax, 6.25, 2.3, "7 生成")

    # 提示：embedding 和 LLM 都是外部依赖
    ax.text(11.0, 5.7, "外部强依赖：\n超时 / 重试 / 兜底\n按调用三方服务对待",
            ha="center", va="center", fontsize=9.5, color="#5f4b00",
            bbox=dict(boxstyle="round,pad=0.4", fc=YELLOW_FILL, ec=YELLOW_EDGE))
    ax.text(11.15, 1.1, "线程安全，\n单例复用，\ngRPC 长连接",
            ha="center", va="center", fontsize=9.5, color="#1e7e34",
            bbox=dict(boxstyle="round,pad=0.4", fc=GREEN_FILL, ec=GREEN_EDGE))

    fig.savefig(os.path.join(OUT_DIR, "07-rag-flow.png"), dpi=150,
                bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    draw()
    print("done")
