try:
    from ._tool_compat import alias_tool
except ImportError:
    from _tool_compat import alias_tool


_module = alias_tool(__name__, "tools.word_pipeline.add_intro_mode_terms")

if __name__ == "__main__":
    _module.main()
