try:
    from ._tool_compat import alias_tool
except ImportError:
    from _tool_compat import alias_tool


_module = alias_tool(__name__, "backend.migrations.migrate_records_001_score_fields")

if __name__ == "__main__":
    _module.main()
