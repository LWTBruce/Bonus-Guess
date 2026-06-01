try:
    from ._tool_compat import alias_tool
except ImportError:
    from _tool_compat import alias_tool


_module = alias_tool(__name__, "tools.word_pipeline.fix_pinyin_english_names")

if __name__ == "__main__":
    _module.main()
