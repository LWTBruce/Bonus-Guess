# Bonus Guess

《有（×）无奖竞猜》是一个物理/数学术语竞猜小游戏。玩家根据首字母、递进线索或字谜网格猜出中文专有名词；游戏会保存独立账号、历史记录、Rating、成就、段位、称号和个性化设置。

当前版本：`0.4.12`

## 当前重点

- 自由、限时、线索、字谜四种普通玩法都支持入门、简单、普通、困难、噩梦五档难度。
- 随机和真·随机会跨物理与数学词库抽题；线索随机现在与自由模式使用同一套完整范围。
- 限时段位、线索段位、字谜段位分别保存物理/数学进度；线索段位已补齐到 20 个 Class。
- 词条解释、来源链接、完整线索和破碎线索按 `docs/` 中的规范维护。
- 登录玩家可提交漏洞反馈和结算页词条删改反馈；管理员后台按状态与日期集中查看。
- 背景音乐、按钮音效、主页音乐、字号、窗口、背景粒子和称号佩戴都随账号保存。

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

双击批处理会优先用 `pyw -3` 启动游戏，避免误调用旧版 Python。桌面快捷方式使用 `frontend/run_game_hidden.vbs` 无控制台启动，图标来自 `frontend/assets/bonus_guess.ico`。启动异常会写入 `profile/launch.log`。

## 测试

运行完整单元测试：

```powershell
python -m unittest discover
```

做全仓库语法检查：

```powershell
Get-ChildItem -Recurse -Filter *.py | ForEach-Object { python -m py_compile $_.FullName }
```

常用局部测试示例：

```powershell
python -m unittest tests.test_rank_system tests.test_term_library_expansion tests.test_nightmare_mode
python -m unittest tests.test_answer_page_ui tests.test_rating_and_random_weights
```

## 打包

项目带有 PyInstaller 配置，可在 Windows 上构建可执行文件：

```powershell
cd frontend
build_exe.bat
```

构建产物会生成到 `frontend/build/` 和 `frontend/dist/`，不进入 Git。

## 主要目录

```text
backend/                 桌面应用主入口、运行时逻辑和数据迁移
backend/app_modules/     Tkinter 应用流程 mixin
backend/runtime/         账号、记录、词库、线索、段位、Rating、音频和反馈逻辑
clues/                   线索 JSON
docs/                    游戏规则、词库、解释和线索写作规范
frontend/                启动器、兼容导入、打包脚本和 UI 组件
frontend/assets/         图标、背景音乐和按钮音效素材
tests/                   单元测试
tools/                   检查、测量和词库维护工具
words/                   物理、数学、人名词库 CSV/Markdown
record/                  旧版根记录目录，仅迁移兼容
profile/                 本地账号、会话、记录和设置，不进入 Git
```

## 本地数据

账号与玩家数据位于 `profile/`：

```text
profile/accounts.json
profile/session.json
profile/admin/bug_feedback.json
profile/users/<account_id>/record/
profile/users/<account_id>/profile/
```

- `accounts.json` 保存账号索引、昵称、密码哈希和管理员标记。
- `session.json` 保存本机当前免登录账号。
- `admin/bug_feedback.json` 保存漏洞反馈、管理员建议处理记录和结算页词条删改反馈。
- 每个用户的 `record/` 保存历史记录、成就和段位进度。
- 每个用户的 `profile/` 保存玩家设置和每日抽题轮转状态。
- `tutorial_completed` 保存在玩家设置中；新账号默认为未完成，老账号默认视为已完成。
- 旧版根目录 `record/` 会在 owner/Bruce 账号启动时合并迁入 `profile/users/bruce/record/`；迁移后不再作为运行期数据源。

## 管理员账号

管理员权限保存在账号数据里。项目不会在全新本地环境里自动创建管理员；普通玩家自行下载后注册的新账号始终是普通账号。

开发者自己的本地数据里保留了老玩家管理员账号：

```text
昵称：Bruce
密码：test001
```

Bruce 在已有本地数据中会保持免登录会话。普通玩家注册时昵称不能与已有账号重复，大小写不同也视为同一昵称。

## 玩法与规则文档

玩家可见规则集中在：

- `docs/game_mechanics.md`：抽题、判题、掩码、提示、计分、线索、字谜、段位、Rating、反馈和音效规则。
- `docs/clue_style_guide_math.md`：数学线索写作规范。
- `docs/term_explanation_writing_guide.md`：词条解释段落写作规范。
- `docs/word_generation_guide.md`：补词和难度控制参考。
- `docs/(first_read)word_modify_guide.md`：补词、改词、删词时的操作顺序。

词库 CSV 放在 `words/`，线索 JSON 放在 `clues/`。新增或维护词条时，至少同步检查：

- 中文名、难度、首字母、英文名和拼音字段是否完整。
- 同一难度下是否有重复词条。
- 中文名是否只保留必要缩写或符号，避免未翻译混名。
- 是否写好了约 200 字解释文段和来源链接。
- 线索模式是否提供 5 条完整线索和 5 条破碎线索。
- 数学线索是否符合“方向、外延、公式、内涵、英文译名”的五条递进结构。

## 版本记录

完整变更见 `CHANGELOG.txt`。近期主线：

- `0.4.12`：重新整理玩家规则文档和 README。
- `0.4.11`：线索模式开放噩梦难度，随机线索扩大到完整范围，线索段位补齐到 20 级。
- `0.4.10`：结算页新增词条删改反馈入口，管理员后台按日期查看词条意见。
- `0.4.9`：线索模式全面整顿。
- `0.4.8`：高中数学入门词表补充常用词，并同步解释、来源和线索。

## Git 说明

仓库只保存源码、文档、词库、线索、素材和测试。本地账号、玩家记录、构建产物、缓存和环境文件由 `.gitignore` 排除。
