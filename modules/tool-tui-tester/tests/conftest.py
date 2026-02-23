"""Conftest: mock amplifier_core before any test imports touch the package __init__."""

import sys
import types

# amplifier_core is a peer dependency not installed in the test venv.
# Stub it out so that `amplifier_module_tool_tui_tester.__init__` can import
# `amplifier_core.interfaces.Tool` and `amplifier_core.models.ToolResult`
# without error.

_core = types.ModuleType("amplifier_core")
_interfaces = types.ModuleType("amplifier_core.interfaces")
_models = types.ModuleType("amplifier_core.models")


class _FakeTool:
    """Minimal stand-in for amplifier_core.interfaces.Tool."""

    pass


class _FakeToolResult:
    """Minimal stand-in for amplifier_core.models.ToolResult."""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


_interfaces.Tool = _FakeTool  # type: ignore[attr-defined]
_models.ToolResult = _FakeToolResult  # type: ignore[attr-defined]
_core.interfaces = _interfaces  # type: ignore[attr-defined]
_core.models = _models  # type: ignore[attr-defined]

sys.modules["amplifier_core"] = _core
sys.modules["amplifier_core.interfaces"] = _interfaces
sys.modules["amplifier_core.models"] = _models
