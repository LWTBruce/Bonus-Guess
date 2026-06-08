# 词汇改动说明

本文说明在接收到“增加、改动或删除某个/某些词”的命令时，应当遵循的操作顺序。

## 增加词语

1. 参考 `docs\word_generation_guide.md`，先在 `words` 中补充词语，并保持编号按顺序排列。
2. 参考 `docs\term_explanation_writing_guide.md`，再在 `clues` 中为新增词语写一到两段描述。
3. 参考对应学科的线索撰写要求，在 `clues` 中继续写完整线索和破碎线索。
4. 跑一遍 `backend` 里的脚本，将新增词语添加到程序里。
5. 最后更新小版本号。

## 改动词语

如果只是翻译、名称等表述变化，不改变词语的实际含义：

1. 参考 `docs\word_generation_guide.md`，先在 `words` 中改动好词语。
2. 再在对应的 `clues` 中同步改动。
3. 跑一遍 `backend` 里的脚本，将词语改动到程序里。
4. 最后更新小版本号。

如果词语的含义也有改动：

1. 参考 `docs\word_generation_guide.md`，先在 `words` 中改动好词语。
2. 参考 `docs\term_explanation_writing_guide.md`，再在 `clues` 中改动一到两段描述。
3. 参考对应学科的线索撰写要求，在 `clues` 中继续改动完整线索和破碎线索。
4. 跑一遍 `backend` 里的脚本，将词语改动到程序里。
5. 最后更新小版本号。

## 删除词语

1. 先删掉 `words` 中的这个词，并保持编号按顺序排列。
2. 再删掉 `clues` 中的这个词。
3. 跑一遍 `backend` 里的脚本，将词语从程序里删去。
4. 最后更新小版本号。
