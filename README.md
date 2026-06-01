# Bonus Guess

《有（x）无奖竞猜》是一个物理/数学术语竞猜小游戏。当前版本是 Tkinter 桌面原型，但已经按网页游戏的产品形态重构了账号、存档和管理员后台：玩家用昵称和密码登录，每个账号拥有独立记录；管理员可以查看全用户数据，并以只读旁观模式进入某个玩家的主页。

当前版本：`0.3.24`

## 主要功能

- 普通玩法：自由、限时、线索、字谜；自由、限时和字谜已支持入门到噩梦五档难度。
- 随机玩法：合并物理和数学词库，可按难度抽题，也可进入真随机全库抽查；噩梦难度会跨学科读取新增前沿词库。
- 段位玩法：限时段位、线索段位和字谜段位，物理/数学分别保存进度。
- 自定义玩法：可配置词库、难度、词长、限时、题数、提示、掩码、线索和字谜参数。
- 记录系统：保存每局答案、提示、用时、得分、Rating、成就、称号和段位标识。
- 账号系统：支持登录、注册、切换账号、退出登录、修改密码和昵称唯一校验。
- 管理员后台：管理员可查看账号列表，选择玩家进入旁观主页或直接查看历史记录，并可将账号设为管理员；管理员设置页可开启隐藏内容显示。
- 旁观模式：只读查看玩家主页、历史记录、成就和玩家档案，不能开始游戏或修改数据。
- 新手教程：新账号首次进入会在真实页面中按高光引导完成一局物理入门教学，并体验字词提示和词库提示；设置页可随时重温。
- 视觉设置：支持背景速度、密度、粒子透明度、字号、窗口大小和页面过场动画。

## 管理员账号

管理员权限保存在账号数据里。项目不会在全新本地环境里自动创建管理员；普通玩家自行下载后注册的新账号始终是普通账号。

开发者自己的本地数据里保留了老玩家管理员账号：

```text
昵称：Bruce
密码：test001
```

Bruce 在已有本地数据中会保持免登录会话。普通玩家注册时昵称不能与已有账号重复，大小写不同也会视为同一个昵称。

## 运行

建议使用 Python 3.10 或更新版本。

```powershell
python -m pip install -r requirements.txt
cd frontend
python bonus_guess.py
```

Windows 下也可以运行：

```powershell
frontend\run_game.bat
```

双击批处理会优先用 `pyw -3` 启动游戏，避免误调用旧版 Python。桌面快捷方式“有（×）无奖竞猜”会显式调用 `wscript.exe` 执行 `frontend/run_game_hidden.vbs`，图标来自 `frontend/assets/bonus_guess.ico`。

## 测试

```powershell
python -m unittest discover
```

做全仓库语法检查：

```powershell
Get-ChildItem -Recurse -Filter *.py | ForEach-Object { python -m py_compile $_.FullName }
```

## 打包

项目带有 PyInstaller 配置，可在 Windows 上构建可执行文件：

```powershell
cd frontend
build_exe.bat
```

构建产物会生成到 `frontend/build/` 和 `frontend/dist/`，不进入 Git。

## 目录结构

```text
backend/     词库生成、修复、迁移脚本
backend/app.py  桌面应用主入口，导出 BonusGuessApp 和 main
backend/app_modules/  应用流程 mixin，按账号、设置、模式、字谜、作答、数据视图拆分
backend/runtime/  账号、记录、词库、线索、段位、Rating 等运行时后端逻辑
backend/migrations/  record/profile 数据迁移脚本
clues/       线索 JSON
docs/        游戏机制和线索写作规范
frontend/    启动器、打包文件和旧导入兼容层
frontend/ui/  Tkinter 视觉组件、背景、Markdown 渲染和通用控件
frontend/assets/  窗口、打包和桌面快捷方式使用的图标资产
frontend/launch_game.pyw  无控制台启动入口，启动异常会写入 profile/launch.log
frontend/run_game_hidden.vbs  桌面快捷方式使用的无窗口启动器
tools/word_pipeline/  词库生成、修复、难度补全和线索生成工具
tests/       账号系统回归测试
words/       物理、数学词库 CSV
record/      旧版根记录目录；启动 owner 账号时会迁入对应的 profile 用户目录，不再作为运行期数据源
profile/     本地账号、会话和用户数据，不进入 Git
```

账号数据位于 `profile/`：

```text
profile/accounts.json
profile/session.json
profile/users/<account_id>/record/
profile/users/<account_id>/profile/
```

## 数据说明

- `accounts.json` 保存账号索引、昵称、密码哈希和管理员标记。
- `session.json` 保存本机当前免登录账号。
- 每个用户的 `record/` 保存历史记录、成就和段位进度。
- 每个用户的 `profile/` 保存玩家设置和每日抽题轮转状态。
- `tutorial_completed` 保存在玩家设置中；新账号默认为未完成，老账号默认视为已完成。
- 旧版根目录 `record/` 会在 owner/Bruce 账号启动时合并迁入 `profile/users/bruce/record/`；迁移后历史记录、成就和段位进度都从 profile 用户目录读取，不再单独兼容根目录 `record/`。

## 词库与线索

词库 CSV 放在 `words/`，线索 JSON 放在 `clues/`。0.3.0 新增了物理连续介质力学、宇宙学、量子信息、物理噩梦前沿理论，以及数学简单/普通/困难补充词表和数学噩梦词库；0.3.1 清理了新增词表中的机械前缀和非缩写英文混名；0.3.2 重写数学新增词表为真实专有名词，并将基础难度接入 1-12；0.3.3 更新了管理员权限和段位进度开放逻辑；0.3.4 调整 Rating、总积分和随机抽题权重；0.3.5 新增词条解释段落写作规范；0.3.6 重排代码目录；0.3.7-0.3.11 分批补齐并重写数学、物理词条解释；0.3.12 为解释补充来源链接；0.3.13 修正首字母反作弊的拼音误判；0.3.14 让结算页词语可点击查看解释；0.3.15 调整字谜选词为先抽半数词表、再按词表等量抽候选词；0.3.16 修正结算页词条点击区域；0.3.17 优化词条解释弹窗排版和 Markdown 预览；0.3.18 改进词条解释里的 TeX 公式渲染和行高；0.3.19 优化答题页提示按钮、右栏说明换行和提示文本布局；0.3.20 修正段落与提示 Markdown 的 TeX 命令解析和公式背景；0.3.21 固定普通答题页提示区位置，确保点击提示后文本可见；0.3.22 收紧公式行距并给普通提示框加入滚动条；0.3.23 优化词库、线索、首字母索引和记录缓存以减少作答卡顿；0.3.24 修正三角格和六边格字谜的直线共边取向。新增或维护词条时，建议同步检查：

- 中文名、难度、首字母、英文名和拼音字段是否完整。
- 同一难度下是否有重复词条。
- 中文名是否只保留必要缩写或符号，避免 `Goldstone玻色子`、`Hybrid Monte Carlo` 这类未翻译混名。
- 线索模式是否提供 5 条完整线索和 5 条破碎线索。
- 数学线索规范：`docs/clue_style_guide_math.md`。
- 总玩法规则：`docs/game_mechanics.md`。

## Git 说明

仓库只保存源码、文档、词库、线索和测试。本地账号、玩家记录、构建产物、缓存和环境文件由 `.gitignore` 排除。
