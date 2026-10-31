# 实验 05「分词器对决」材料构建
# 建索引 exp05_products，title 是 multi-field：
#   title          —— standard（默认）
#   title.standard —— standard
#   title.ik_max   —— ik_max_word
#   title.ik_smart —— ik_smart
# bulk 灌约 20 条中文商品标题
# 运行前置：IK 插件已装（lab/install-ik.sh），运行：python exp05-gen.py

from elasticsearch import Elasticsearch, helpers

ES = Elasticsearch("http://localhost:9200")
INDEX = "exp05_products"

TITLES = [
    "苹果手机保护壳",
    "苹果手机壳",
    "苹果笔记本电脑电源适配器",
    "苹果原装数据线",
    "中华人民共和国民法典精装版",
    "中华人民共和国民法典注释本",
    "一次性医用外科口罩50只装",
    "医用外科缝合线",
    "75%医用消毒酒精",
    "华为无线蓝牙耳机",
    "华为 FreeBuds 蓝牙耳机",
    "便携蓝牙音箱",
    "小米智能手环8",
    "小米充电宝20000毫安",
    "中华牌绘图铅笔",
    "人民教育出版社初中语文课本",
    "不锈钢保温杯500ml",
    "儿童护眼台灯",
    "机械键盘红轴104键",
    "运动水壶耐高温",
]


def check_ik_installed():
    """IK 没装的话，后面建索引会报一个含糊的错，先提前拦住。"""
    try:
        ES.indices.analyze(analyzer="ik_max_word", text="测试")
    except Exception:
        raise SystemExit("ik_max_word 不可用：IK 插件未安装。先在 lab/ 下运行 bash install-ik.sh")


def gen_actions():
    for i, title in enumerate(TITLES, start=1):
        yield {"_index": INDEX, "_id": i, "_source": {"title": title}}


def main():
    check_ik_installed()

    if ES.indices.exists(index=INDEX):
        ES.indices.delete(index=INDEX)
        print(f"已删除旧索引 {INDEX}")

    ES.indices.create(
        index=INDEX,
        mappings={
            "properties": {
                "title": {
                    "type": "text",
                    "analyzer": "standard",
                    "fields": {
                        "standard": {"type": "text", "analyzer": "standard"},
                        "ik_max": {"type": "text", "analyzer": "ik_max_word"},
                        "ik_smart": {"type": "text", "analyzer": "ik_smart"},
                    },
                }
            }
        },
    )
    print(f"已创建索引 {INDEX}（title: standard + title.ik_max + title.ik_smart）")

    ok, _ = helpers.bulk(ES, gen_actions())
    print(f"bulk 写入 {ok} 条")

    ES.indices.refresh(index=INDEX)
    print(f"count = {ES.count(index=INDEX)['count']}")
    print("材料构建完成")


if __name__ == "__main__":
    main()
