# 安装 IK 中文分词插件（实验 05「分词器对决」的前置步骤，其余实验不需要）
# 在 lab/ 目录下运行：bash install-ik.sh
# 注意：插件装在容器层不在数据卷里，docker compose down 之后容器重建就没了，重新跑一遍本脚本即可
# 注意：IK 插件包已从 GitHub Releases 迁移到 infinilabs 官方分发站（GitHub 上的旧 URL 已 404），
#       必须使用下面的 get.infini.cloud 地址，版本号与 ES 镜像 8.11.4 对齐
docker compose exec es01 bin/elasticsearch-plugin install --batch https://get.infini.cloud/elasticsearch/analysis-ik/8.11.4
docker compose restart es01
