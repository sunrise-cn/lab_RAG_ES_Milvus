# -*- coding: utf-8 -*-
"""专栏三 02 写入路径与近实时 配图（2 张）"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import os

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

BLUE_F, BLUE_E = "#e8f0fe", "#4285f4"
RED_F, RED_E = "#fce8e6", "#ea4335"
GREEN_F, GREEN_E = "#e6f4ea", "#34a853"
YELL_F, YELL_E = "#fff8e1", "#f9ab00"
GRAY_F, GRAY_E = "#f1f3f4", "#9aa0a6"

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
os.makedirs(OUT, exist_ok=True)


def box(ax, x, y, w, h, text, fc, ec, fs=9, bold=False, ls="-", tc=None):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05",
                                fc=fc, ec=ec, lw=1.5, linestyle=ls))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, fontweight="bold" if bold else "normal",
            color=tc or "#202124")


def zone(ax, x, y, w, h, label, fc="#fafafa"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04",
                                fc=fc, ec="#bdc1c6", lw=1.0, linestyle="--"))
    ax.text(x + 0.12, y + h - 0.28, label, fontsize=8.5, color="#5f6368",
            fontweight="bold")


# ============ 图 1：写入路径三态 ============
fig, ax = plt.subplots(figsize=(10.4, 7.6))
ax.set_xlim(0, 12)
ax.set_ylim(0, 10.6)
ax.axis("off")

titles = ["① 写入成功后（refresh 前）", "② refresh 后（近实时的“近”）", "③ flush 后（真正落盘）"]
pxs = [0.35, 4.45, 8.55]
PW = 3.15

for i, (px, t) in enumerate(zip(pxs, titles)):
    ax.text(px + PW / 2, 9.75, t, fontsize=11, fontweight="bold", ha="center")

# 状态间箭头
for x, lab1, lab2 in [(4.0, "refresh", "默认每 1 秒"),
                      (8.1, "flush", "默认 30 分钟或 translog 满")]:
    ax.add_patch(FancyArrowPatch((x - 0.32, 9.75), (x + 0.32, 9.75),
                                 arrowstyle="-|>", mutation_scale=16, color="#ea4335", lw=2.0))
ax.text(4.0, 10.25, "refresh", fontsize=10, color="#ea4335", ha="center", fontweight="bold")
ax.text(8.1, 10.25, "flush", fontsize=10, color="#ea4335", ha="center", fontweight="bold")

# ---- 状态 1 ----
px = pxs[0]
zone(ax, px, 8.2, PW, 1.35, "indexing buffer（内存）")
box(ax, px + 0.2, 8.32, PW - 0.4, 0.85, "退款政策 v2\n已解析分词，不可查", RED_F, RED_E, fs=8.5)

zone(ax, px, 5.1, PW, 2.8, "文件系统缓存（page cache，可查）")
box(ax, px + 0.2, 6.55, 1.25, 0.6, "旧段 1", BLUE_F, BLUE_E, fs=8.5)
box(ax, px + 1.65, 6.55, 1.25, 0.6, "旧段 2", BLUE_F, BLUE_E, fs=8.5)
box(ax, px + 0.2, 5.35, PW - 0.4, 0.75, "这里没有 v2 的任何痕迹",
    GRAY_F, GRAY_E, fs=8.5, tc="#5f6368")

zone(ax, px, 0.35, PW, 4.35, "磁盘")
box(ax, px + 0.2, 3.15, 1.25, 0.6, "旧段 1", BLUE_F, BLUE_E, fs=8.5)
box(ax, px + 1.65, 3.15, 1.25, 0.6, "旧段 2", BLUE_F, BLUE_E, fs=8.5)
ax.text(px + 0.2, 2.85, "（已 fsync）", fontsize=8, color="#5f6368")
box(ax, px + 0.2, 1.1, PW - 0.4, 1.35,
    "translog\n已记下这次写入\n（默认每请求 fsync）", GREEN_F, GREEN_E, fs=8.5)

# ---- 状态 2 ----
px = pxs[1]
zone(ax, px, 8.2, PW, 1.35, "indexing buffer（内存）")
box(ax, px + 0.2, 8.32, PW - 0.4, 0.85, "已清空\n（继续攒下一批）", GRAY_F, GRAY_E, fs=8.5, tc="#5f6368")

zone(ax, px, 5.1, PW, 2.8, "文件系统缓存（page cache，可查）")
box(ax, px + 0.2, 6.55, 1.25, 0.6, "旧段 1", BLUE_F, BLUE_E, fs=8.5)
box(ax, px + 1.65, 6.55, 1.25, 0.6, "旧段 2", BLUE_F, BLUE_E, fs=8.5)
box(ax, px + 0.2, 5.35, PW - 0.4, 0.75, "新段：v2 可查（未 fsync）", GREEN_F, GREEN_E, fs=8.5, bold=True)

zone(ax, px, 0.35, PW, 4.35, "磁盘")
box(ax, px + 0.2, 3.15, 1.25, 0.6, "旧段 1", BLUE_F, BLUE_E, fs=8.5)
box(ax, px + 1.65, 3.15, 1.25, 0.6, "旧段 2", BLUE_F, BLUE_E, fs=8.5)
box(ax, px + 0.2, 1.1, PW - 0.4, 1.35,
    "translog\n继续累积\n（持久性仍由它保着）", GREEN_F, GREEN_E, fs=8.5)

# ---- 状态 3 ----
px = pxs[2]
zone(ax, px, 8.2, PW, 1.35, "indexing buffer（内存）")
box(ax, px + 0.2, 8.32, PW - 0.4, 0.85, "空", GRAY_F, GRAY_E, fs=8.5, tc="#5f6368")

zone(ax, px, 5.1, PW, 2.8, "文件系统缓存（page cache，可查）")
box(ax, px + 0.2, 6.55, 1.25, 0.6, "旧段 1", BLUE_F, BLUE_E, fs=8.5)
box(ax, px + 1.65, 6.55, 1.25, 0.6, "旧段 2", BLUE_F, BLUE_E, fs=8.5)
box(ax, px + 0.2, 5.35, PW - 0.4, 0.75, "新段：v2 可查", GREEN_F, GREEN_E, fs=8.5)

zone(ax, px, 0.35, PW, 4.35, "磁盘")
box(ax, px + 0.2, 3.15, 1.25, 0.6, "旧段 1", BLUE_F, BLUE_E, fs=8.5)
box(ax, px + 1.65, 3.15, 1.25, 0.6, "旧段 2", BLUE_F, BLUE_E, fs=8.5)
box(ax, px + 0.2, 2.2, PW - 0.4, 0.55, "所有 segment fsync 完成", GREEN_F, GREEN_E, fs=8.5, bold=True)
box(ax, px + 0.2, 1.1, PW - 0.4, 0.85,
    "translog 清空\n（接力棒交给磁盘）", YELL_F, YELL_E, fs=8.5)

ax.text(6.0, 0.02, "对照 MySQL：buffer ≈ 脏页攒批，translog ≈ redo log，flush ≈ 后台刷脏",
        fontsize=10, ha="center", color="#5f6368")

plt.tight_layout()
plt.savefig(os.path.join(OUT, "02-write-path.png"), dpi=150, bbox_inches="tight")
plt.close(fig)

# ============ 图 2：不可变 segment 上的更新与删除 ============
fig, ax = plt.subplots(figsize=(9.8, 6.6))
ax.set_xlim(0, 10)
ax.set_ylim(0, 7.6)
ax.axis("off")

box(ax, 3.5, 6.3, 3.0, 0.95, "update 请求\n_id = 42 的文档", YELL_F, YELL_E, fs=11, bold=True)

# 两条路径箭头
ax.add_patch(FancyArrowPatch((4.3, 6.25), (2.7, 5.5), arrowstyle="-|>",
                             mutation_scale=15, color="#5f6368", lw=1.6))
ax.add_patch(FancyArrowPatch((5.7, 6.25), (7.3, 5.5), arrowstyle="-|>",
                             mutation_scale=15, color="#5f6368", lw=1.6))
ax.text(2.35, 5.98, "旧版本\n打删除标记", fontsize=9, ha="center", color="#5f6368")
ax.text(7.65, 5.98, "新版本\n当新文档写入", fontsize=9, ha="center", color="#5f6368")

box(ax, 0.4, 3.7, 4.0, 1.65,
    "旧 segment：doc 7\n_id=42, 退款政策 v1\n.del 位图标记 → 不真删\n查询命中后被过滤",
    RED_F, RED_E, fs=9.5)
box(ax, 5.6, 3.7, 4.0, 1.65,
    "新 segment（下次 refresh 生成）\ndoc 101（全新的内部 doc id）\n_id=42, 退款政策 v2",
    GREEN_F, GREEN_E, fs=9.5)

ax.text(5.0, 3.3, "两个版本短暂共存，查询按 _seq_no 取最新", fontsize=9.5,
        ha="center", color="#5f6368")

ax.add_patch(FancyArrowPatch((2.4, 3.6), (3.6, 2.6), arrowstyle="-|>",
                             mutation_scale=15, color="#5f6368", lw=1.6))
ax.add_patch(FancyArrowPatch((7.6, 3.6), (6.4, 2.6), arrowstyle="-|>",
                             mutation_scale=15, color="#5f6368", lw=1.6))

box(ax, 2.2, 1.2, 5.6, 1.3,
    "merge：旧段重写成新段，v1 不进新段\n→ 物理删除，空间回收",
    GREEN_F, GREEN_E, fs=10, bold=True)

ax.text(5.0, 0.5, "对照：MySQL 原地 UPDATE + undo log / purge；ES 追加式，靠 merge 回收",
        fontsize=9.5, ha="center", color="#5f6368")

plt.tight_layout()
plt.savefig(os.path.join(OUT, "02-segment-immutable.png"), dpi=150, bbox_inches="tight")
plt.close(fig)

print("done")
