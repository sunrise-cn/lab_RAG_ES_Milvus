"""实验 12 画图：recall-QPS 曲线。

读 lab/data/exp12-results.json，画到 lab/out/12-recall-qps.png。
"""
import json
from pathlib import Path

import matplotlib.pyplot as plt

LAB = Path(__file__).resolve().parent.parent

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False


def main():
    with open(LAB / "data" / "exp12-results.json", encoding="utf-8") as f:
        results = json.load(f)

    fig, ax = plt.subplots(figsize=(7, 4.5))

    flat = results["flat"]
    ax.scatter([flat["recall"]], [flat["qps"]], marker="s", s=60,
               color="#ea4335", zorder=3)
    ax.annotate("FLAT：召回 100%，QPS 垫底",
                (flat["recall"], flat["qps"]),
                textcoords="offset points", xytext=(-6, 10),
                ha="right", fontsize=9)

    for key, color, label in [
        ("hnsw", "#4285f4", "HNSW（标注值 = ef）"),
        ("ivf", "#34a853", "IVF_FLAT（标注值 = nprobe）"),
    ]:
        items = sorted(results[key].items(), key=lambda kv: kv[1]["qps"])
        xs = [v["recall"] for _, v in items]
        ys = [v["qps"] for _, v in items]
        ax.plot(xs, ys, "o-", color=color, label=label)
        for k, v in items:
            ax.annotate(k, (v["recall"], v["qps"]),
                        textcoords="offset points", xytext=(4, 5),
                        fontsize=8, color=color)

    ax.set_xlabel("recall@10（越高越准）")
    ax.set_ylabel("QPS（越高越快）")
    ax.set_title("召回率-QPS 曲线：右上角是天堂，但到不了")
    ax.legend()
    ax.grid(alpha=0.3)

    out = LAB / "out" / "12-recall-qps.png"
    out.parent.mkdir(exist_ok=True)
    fig.savefig(out, dpi=150, bbox_inches="tight")
    print(f"图已存 {out}")


if __name__ == "__main__":
    main()
