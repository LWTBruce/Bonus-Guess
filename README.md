# Bonus Guess

《有（x）无奖竞猜》是一个用 Tkinter 写的物理/数学术语竞猜小游戏。游戏会从本地词库中抽取专有名词，玩家根据首字母、掩码或递进线索猜出中文答案，并在不同模式下获得分数、Rating、成就、称号和段位标识。

## 功能概览

- 普通玩法：自由、线索、限时、真随机。
- 段位玩法：自由段位和线索段位，物理/数学独立进度，共 15 段。
- 自定义玩法：可选择出题形式、词库、难度、词长、掩码、限时和挑战题数。
- 记录系统：保存历史答题、提示、分数、Rating、成就和段位进度。
- 本地词库：`words/` 保存题目，`clues/` 保存线索，支持物理和数学多级分类。

## 运行方式

建议使用 Python 3.10 或更新版本。

```powershell
python -m pip install -r requirements.txt
cd frontend
python bonus_guess.py
```

Windows 下也可以直接运行：

```powershell
frontend\run_game.bat
```

## 打包

项目带有 PyInstaller 配置，可在 Windows 上构建可执行文件：

```powershell
cd frontend
build_exe.bat
```

构建产物会生成到 `frontend/build/` 和 `frontend/dist/`，这两个目录不进入 Git。

## 目录结构

```text
backend/     词库生成、修复和迁移脚本
clues/       线索 JSON
docs/        游戏机制和线索写作规范
frontend/    Tkinter 前端和游戏逻辑
words/       物理、数学词库 CSV
record/      本地游玩记录，不进入 Git
profile/     本地玩家设置和每日轮转状态，不进入 Git
```

## 词库与线索

词库 CSV 需要包含中文名、难度、首字母、英文名和拼音等字段。线索文件按同名 JSON 放在 `clues/` 对应目录中。数学线索的写作要求见：

- `docs/clue_style_guide_math.md`
- `docs/game_mechanics.md`

新增词条时要避免和同一学科已有词条重复；线索模式需要同时提供 5 条完整线索和 5 条破碎线索，避免退回 fallback 线索。

## Git 说明

仓库只保存源码、文档、词库和线索。本地运行状态、玩家记录、构建产物和 Python 缓存已在 `.gitignore` 中排除。
