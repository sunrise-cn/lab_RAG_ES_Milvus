# -*- coding: utf-8 -*-
"""第 06 篇 存算分离架构 配图：组件地图、growing/sealed 状态流转"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

BLUE_F, BLUE_E = "#e8f0fe", "#4285f4"
RED_F, RED_E = "#fce8e6", "#ea4335"
GREEN_F, GREEN_E = "#e6f4ea", "#34a853"
YELLOW_F, YELLOW_E = "#fff8e1", "#f9ab00"
GRAY = "#5f6368"

OUT = r"D:\Documents\ob_new\01 后端\my-doc\ES与Milvus\专栏三-运行机制\assets"


def box(ax, x, y, w, h, text, fc, ec, fs=9.5, lw=1.4, zorder=3, tc="black"):
    ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, facecolor=fc,
                           edgecolor=ec, lw=lw, zorder=zorder))
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, color=tc, zorder=zorder + 1)


def arrow(ax, x1, y1, x2, y2, color, lw=1.6, style="-", zorder=2, ms=13):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color=color, lw=lw, linestyle=style,
                                mutation_scale=ms, shrinkA=0, shrinkB=0), zorder=zorder)


def alabel(ax, x, y, text, color, fs=8.5, ha="center"):
    ax.text(x, y, text, ha=ha, va="center", fontsize=fs, color=color, zorder=6,
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                      edgecolor="none", alpha=0.85))


# ---------------------------------------------------------------- 图 1：组件地图
def fig_arch():
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.set_xlim(0, 12.8)
    ax.set_ylim(0, 9.2)
    ax.axis("off")
    ax.set_title("Milvus 2.x 存算分离：组件地图", fontsize=13, pad=12)

    # 客户端 / proxy
    box(ax, 1.1, 8.3, 1.6, 0.75, "客户端", BLUE_F, BLUE_E)
    box(ax, 3.4, 8.3, 1.5, 0.9, "Proxy\n接入网关", BLUE_F, BLUE_E)
    arrow(ax, 1.9, 8.3, 2.65, 8.3, GRAY, lw=1.6)

    # 协调层
    ax.add_patch(FancyBboxPatch((4.9, 6.55), 7.3, 1.15,
                                boxstyle="round,pad=0.05",
                                facecolor="#f1f3f4", edgecolor=GRAY, lw=1.0, zorder=1))
    ax.text(8.55, 7.9, "协调层 Coordinator（控制平面：管状态，不管数据流）",
            ha="center", fontsize=9.5, color=GRAY)
    for x, t in [(5.9, "Root\n元数据/DDL"), (7.8, "Data\nsegment/flush"),
                 (9.7, "Query\n负载均衡"), (11.5, "Index\n建索引")]:
        box(ax, x, 7.0, 1.7, 0.8, t, BLUE_F, BLUE_E, fs=8.5)

    # 工作节点
    box(ax, 5.4, 4.6, 2.1, 0.95, "Query Node\n检索算力", BLUE_F, BLUE_E)
    box(ax, 8.6, 4.6, 2.0, 0.95, "Data Node\n攒盘落盘", BLUE_F, BLUE_E)
    box(ax, 11.2, 4.6, 2.0, 0.95, "Index Node\n建索引算力", BLUE_F, BLUE_E)

    # 存储层
    box(ax, 2.4, 1.5, 3.1, 0.95, "Log Broker\n（Kafka/Pulsar）", GREEN_F, GREEN_E)
    ax.text(2.4, 0.75, "写入第一落点，消息即数据", ha="center", fontsize=8.5, color=GREEN_E)
    box(ax, 8.6, 1.5, 4.6, 0.95, "对象存储（S3/MinIO）：一切的真相", YELLOW_F, YELLOW_E)

    # 写入路径（蓝实线）
    arrow(ax, 3.4, 7.85, 2.55, 2.0, BLUE_E, lw=2.0)
    alabel(ax, 2.75, 6.4, "① insert：先落日志，\nack 后即返回", BLUE_E, ha="center")
    arrow(ax, 3.4, 2.0, 7.6, 4.1, BLUE_E, lw=2.0)
    alabel(ax, 4.6, 2.75, "② 消费增量\n攒 growing segment", BLUE_E)
    arrow(ax, 8.6, 4.1, 8.7, 2.0, BLUE_E, lw=2.0)
    alabel(ax, 9.6, 3.2, "③ seal 后 flush\n成 sealed segment", BLUE_E)

    # 查询路径（绿实线）
    arrow(ax, 3.75, 7.85, 5.1, 5.1, GREEN_E, lw=2.0)
    alabel(ax, 4.6, 6.3, "search 请求", GREEN_E)

    # 查询节点取数据（绿虚线）
    arrow(ax, 4.7, 4.1, 3.0, 2.0, GREEN_E, lw=1.5, style="--")
    alabel(ax, 3.3, 3.6, "订阅增量\n（growing 可查）", GREEN_E)
    arrow(ax, 6.1, 4.1, 7.8, 2.0, GREEN_E, lw=1.5, style="--")
    alabel(ax, 6.8, 2.9, "本地缓存，\n未命中穿透", GREEN_E)

    # 索引构建（灰虚线）
    arrow(ax, 10.1, 2.0, 10.9, 4.1, GRAY, lw=1.3, style="--")
    arrow(ax, 11.5, 4.1, 9.5, 2.0, GRAY, lw=1.3, style="--")
    alabel(ax, 12.0, 2.5, "读 sealed，\n索引写回", GRAY)

    # 控制面调度（灰点线）
    arrow(ax, 7.8, 6.55, 8.3, 5.1, GRAY, lw=1.0, style=":")
    arrow(ax, 11.5, 6.55, 11.3, 5.1, GRAY, lw=1.0, style=":")
    arrow(ax, 9.7, 6.55, 6.3, 5.1, GRAY, lw=1.0, style=":")
    alabel(ax, 9.0, 6.15, "调度", GRAY, fs=8)

    fig.savefig(OUT + r"\06-architecture.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------- 图 2：growing / sealed
def fig_segment():
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.set_xlim(0, 12.6)
    ax.set_ylim(0, 6.0)
    ax.axis("off")
    ax.set_title("一段数据的一生：growing → sealed，以及查询节点的双视角", fontsize=12.5, pad=10)

    # 写入主链
    box(ax, 0.9, 4.4, 1.5, 0.8, "写入", BLUE_F, BLUE_E, fs=10)
    box(ax, 3.0, 4.4, 2.0, 0.9, "Log Broker", GREEN_F, GREEN_E, fs=10)
    box(ax, 5.9, 4.4, 2.3, 0.95, "growing segment\n（内存中，可查，\n持续增长）", BLUE_F, BLUE_E, fs=9)
    box(ax, 9.0, 4.4, 2.3, 0.95, "sealed segment\n（不可变文件，\n躺在对象存储）", YELLOW_F, YELLOW_E, fs=9)
    box(ax, 11.8, 4.4, 1.5, 0.8, "索引文件", GREEN_F, GREEN_E, fs=9)

    arrow(ax, 1.65, 4.4, 2.0, 4.4, GRAY, lw=1.6)
    arrow(ax, 4.0, 4.4, 4.75, 4.4, GRAY, lw=1.6)
    alabel(ax, 4.4, 5.15, "data node\n消费攒批", GRAY)
    arrow(ax, 7.05, 4.4, 7.85, 4.4, GRAY, lw=1.6)
    alabel(ax, 7.45, 5.15, "seal\n（达到大小上限）", GRAY)
    arrow(ax, 10.15, 4.4, 11.05, 4.4, GRAY, lw=1.6)
    alabel(ax, 10.6, 5.15, "index node\n建索引", GRAY)
    ax.text(9.0, 3.35, "不可变：删除/更新靠标记 + 后台 compaction 物理清理",
            ha="center", fontsize=8.5, color=GRAY)

    # 查询节点双视角
    box(ax, 5.9, 1.5, 2.8, 1.0, "Query Node\n（检索算力，无状态）", BLUE_F, BLUE_E, fs=9.5)
    arrow(ax, 2.8, 3.95, 4.8, 2.05, GREEN_E, lw=1.6, style="--")
    alabel(ax, 2.6, 2.9, "订阅增量：\ngrowing 直接可查", GREEN_E)
    arrow(ax, 8.6, 3.95, 6.9, 2.05, GREEN_E, lw=1.6, style="--")
    alabel(ax, 9.1, 2.9, "本地缓存，\n未命中穿透对象存储", GREEN_E)

    ax.text(6.3, 0.45,
            "一致性级别 = 查询前把“订阅进度”追到哪：Strong 追平最新，Eventually 不等",
            ha="center", fontsize=10,
            bbox=dict(boxstyle="round,pad=0.45", facecolor=YELLOW_F, edgecolor=YELLOW_E, lw=1.4))

    fig.savefig(OUT + r"\06-segment.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


fig_arch()
fig_segment()
print("done")
