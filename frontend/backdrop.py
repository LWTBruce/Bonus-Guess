try:
    from ._compat import alias_module
except ImportError:
    from _compat import alias_module


alias_module(__name__, "frontend.ui.backdrop")
