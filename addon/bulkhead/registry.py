"""Registration order matters: operators exist before the UI references them."""
from . import ops, ui

_MODULES = (ops, ui)


def register():
    for module in _MODULES:
        module.register()


def unregister():
    for module in reversed(_MODULES):
        module.unregister()
