
支持的命令：

make setup
make doctor
make config
make config-upgrade
make check
make install
make setup-sandbox
make dev
make dev-daemon
make start
make start-daemon
make stop
make clean
说明：

make dev：本地开发模式，同时启动 FastAPI 后端和 Vue 前端热更新。
make start-daemon：生产部署模式，使用 server/docker-compose.prod.yml 启动 api + front + nginx。
make config：生成 .env 和 server/.env，已有配置时会中止。
make config-upgrade：按当前项目结构合并 .env.example / server/.env.example 的新增字段。
make install：安装 Python 后端依赖、前端依赖；如果以后添加 .pre-commit-config.yaml，也会安装 hooks.