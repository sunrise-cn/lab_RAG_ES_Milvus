# 实验 11「写入吞吐调优」材料构建：生成 30 万条文档到 JSONL 数据文件
# 为什么落文件而不是边写边现生成：8 个组合灌的是同一份、解析成本完全一致的数据，
# 测量里只剩"写入方式"这一个变量（控制变量优先）。
# 运行：python scripts/exp11-gen.py（先激活 lab/.venv）
# 产出：lab/data/exp11-docs.jsonl（300000 行，约 20MB）

import json
from pathlib import Path

TOTAL = 300_000
OUT = Path(__file__).resolve().parent.parent / "data" / "exp11-docs.jsonl"


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for i in range(TOTAL):
            doc = {"no": i, "text": f"第{i}条写入吞吐实验记录"}
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")
            if (i + 1) % 100_000 == 0:
                print(f"  已生成 {i + 1} 条")
    print(f"数据文件就绪：{OUT}")
    print(f"共 {TOTAL} 条，{OUT.stat().st_size / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    main()
