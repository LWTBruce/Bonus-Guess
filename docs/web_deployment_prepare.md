# 网页部署准备

本文记录未来把《有（×）无奖竞猜》放到网页上运行时需要提供的最小参数。本版本只做配置和资源路径准备，不实现浏览器前端、HTTP API 或联机对抗房间。

## 参数

可以通过环境变量提供，也可以把同名字段写入 JSON，并用 `BONUS_GUESS_WEB_CONFIG` 指向该文件。

| 环境变量 | JSON 字段 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `BONUS_GUESS_HOST` | `host` | `127.0.0.1` | 未来网页服务监听地址。 |
| `BONUS_GUESS_PORT` | `port` | `8765` | 未来网页服务监听端口。 |
| `BONUS_GUESS_PUBLIC_BASE_URL` | `public_base_url` | 空 | 网页外部访问地址。 |
| `BONUS_GUESS_RESOURCE_DIR` | `resource_dir` | 当前项目或打包资源目录 | `words/`、`clues/`、`docs/` 等只读资源所在目录。 |
| `BONUS_GUESS_DATA_DIR` | `data_dir` | 当前项目或 exe 所在目录 | `profile/`、`record/` 等本地数据所在目录。 |
| `BONUS_GUESS_ENABLE_ONLINE` | `enable_online` | `false` | 联机对抗预留开关；当前版本保持关闭。 |

示例见 `deploy/web_runtime.example.json`。

## 未来接口边界

- Python 后端继续负责词库读取、线索读取、判题、计分、Rating、成就和账号数据。
- 网页前端只通过后端接口获取题面、提交答案、读取结算、查看记录和设置。
- 联机对抗会在后端增加房间、匹配、同步状态和结算广播；当前配置只预留开关，不改变单人模式。
