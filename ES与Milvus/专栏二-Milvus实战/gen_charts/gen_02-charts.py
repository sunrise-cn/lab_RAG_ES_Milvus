# -*- coding: utf-8 -*-
"""专栏二 02 篇配图：standalone 容器拓扑；架构速览"""
import os
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

BLUE_F, BLUE_E = "#e8f0fe", "#4285f4"
RED_F, RED_E = "#fce8e6", "#ea4335"
GREEN_F, GREEN_E = "#e6f4ea", "#34a853"
YELLOW_F, YELLOW_E = "#fff8e1", "#f9ab00"
GRAY = "#5f6368"

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
os.makedirs(OUT, exist_ok=True)


def box(ax, x, y, w, h, text, fc, ec, fs=10, bold=False, ls="-"):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                       linewidth=1.6, facecolor=fc, edgecolor=ec, linestyle=ls)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            color="#202124", fontweight="bold" if bold else "normal", linespacing=1.5)


def arrow(ax, x1, y1, x2, y2, label=None, lx=None, ly=None, ls="-",
          color=GRAY, ha="center"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.6, ls=ls,
                                mutation_scale=16, shrinkA=2, shrinkB=2))
    if label:
        ax.text(lx if lx is not None else (x1 + x2) / 2,
                ly if ly is not None else (y1 + y2) / 2 + 0.15,
                label, fontsize=9, color=GRAY, ha=ha)


# ---------- 图 1：standalone 容器拓扑 ----------
fig, ax = plt.subplots(figsize=(9.5, 6))
ax.set_xlim(0, 10)
ax.set_ylim(0, 6.6)
ax.axis("off")
ax.set_title("standalone 单机版：compose 里的四个容器", fontsize=13, pad=10)

# compose 边界
ax.add_patch(Rectangle((2.6, 0.1), 7.3, 6.2, fill=False,
                       edgecolor="#9aa0a6", lw=1.2, linestyle="--"))
ax.text(2.8, 6.02, "docker compose 内部网络", fontsize=9, color=GRAY, va="center")

# 容器
box(ax, 0.05, 2.5, 2.25, 1.4, "你的应用\npymilvus /\nJava SDK", BLUE_F, BLUE_E, ls="--")
box(ax, 5.6, 4.9, 2.8, 1.0, "attu 控制台\n:3000", GREEN_F, GREEN_E)
box(ax, 5.6, 2.3, 2.8, 1.8, "milvus-standalone\n服务本体\n\n:19530 SDK\n:9091 管理", BLUE_F, BLUE_E)
box(ax, 3.0, 0.4, 1.9, 1.1, "milvus-etcd\n元数据", BLUE_F, BLUE_E)
box(ax, 6.9, 0.4, 2.7, 1.1, "milvus-minio\n对象存储（数据真身）", BLUE_F, BLUE_E)

# 箭头
arrow(ax, 2.32, 3.2, 5.58, 3.2, "19530", ly=3.35)
arrow(ax, 7.0, 4.88, 7.0, 4.12, "MILVUS_URL = 服务名:19530", lx=7.15, ly=4.5, ha="left")
arrow(ax, 6.1, 2.28, 4.6, 1.52, "读写元数据", lx=4.6, ly=2.0)
arrow(ax, 7.7, 2.28, 8.1, 1.52, "存数据与索引", lx=8.6, ly=2.0)

fig.savefig(os.path.join(OUT, "02-standalone-topology.png"), dpi=150, bbox_inches="tight")
plt.close(fig)

# ---------- 图 2：架构速览 ----------
fig, ax = plt.subplots(figsize=(9.5, 7.8))
ax.set_xlim(-1.6, 11.6)
ax.set_ylim(0, 10.4)
ax.axis("off")
ax.set_title("Milvus 2.x 架构速览", fontsize=13, pad=10)

# 主链路
box(ax, 3.5, 9.4, 3.0, 0.8, "SDK 客户端", BLUE_F, BLUE_E)
box(ax, 3.5, 7.7, 3.0, 1.1, "proxy\n唯一入口", BLUE_F, BLUE_E, bold=True)

# coordinator 组
ax.add_patch(Rectangle((1.2, 5.6), 7.6, 1.3, fill=False,
                       edgecolor="#9aa0a6", lw=1.2, linestyle="--"))
ax.text(5.0, 7.15, "coordinator：只决策，不干活", fontsize=9, color=GRAY,
        ha="center", va="center")
box(ax, 1.4, 5.75, 2.1, 0.9, "root coord\nDDL、时间戳", BLUE_F, BLUE_E, fs=9)
box(ax, 3.95, 5.75, 2.1, 0.9, "data coord\n数据分片", BLUE_F, BLUE_E, fs=9)
box(ax, 6.5, 5.75, 2.1, 0.9, "query coord\n查询负载", BLUE_F, BLUE_E, fs=9)

# worker 组
ax.add_patch(Rectangle((1.2, 3.2), 7.6, 1.3, fill=False,
                       edgecolor="#9aa0a6", lw=1.2, linestyle="--"))
ax.text(5.0, 4.72, "worker 节点：干活，无状态", fontsize=9, color=GRAY,
        ha="center", va="center")
box(ax, 1.4, 3.35, 2.1, 0.9, "query node\n搜索", BLUE_F, BLUE_E, fs=9)
box(ax, 3.95, 3.35, 2.1, 0.9, "data node\n写入落盘", BLUE_F, BLUE_E, fs=9)
box(ax, 6.5, 3.35, 2.1, 0.9, "index node\n建 ANN 索引", BLUE_F, BLUE_E, fs=9)

box(ax, 1.2, 1.6, 7.6, 1.0, "对象存储（MinIO / S3）：向量与索引的真身", BLUE_F, BLUE_E)

# 侧边角色
box(ax, -1.4, 5.75, 2.1, 0.9, "etcd\n元数据", BLUE_F, BLUE_E, fs=9)
box(ax, 9.5, 7.7, 2.1, 1.1, "消息队列\nRocksMQ /\nPulsar / Kafka", BLUE_F, BLUE_E, fs=9)

# 主链路箭头
arrow(ax, 5.0, 9.38, 5.0, 8.82)
arrow(ax, 5.0, 7.68, 5.0, 7.02)
arrow(ax, 5.0, 5.58, 5.0, 4.55)
arrow(ax, 5.0, 3.18, 5.0, 2.62, "读数据与索引", lx=5.15, ly=2.9, ha="left")

# 侧边箭头
arrow(ax, 0.72, 6.2, 1.18, 6.2, "存取元数据", lx=0.9, ly=6.45, ls="--")
arrow(ax, 6.52, 8.25, 9.48, 8.25, "写入先进队列（对照 Kafka / redo log）",
      lx=8.0, ly=8.45)
arrow(ax, 10.55, 7.68, 6.1, 4.28, "消费、落盘", lx=9.0, ly=5.5, ls="--")

# 底部结论
box(ax, 1.2, 0.25, 7.6, 0.85,
    "一句话：计算无状态，数据在对象存储，写入先过消息队列（存算分离）",
    YELLOW_F, YELLOW_E, fs=10)

fig.savefig(os.path.join(OUT, "02-architecture.png"), dpi=150, bbox_inches="tight")
plt.close(fig)

print("done")
