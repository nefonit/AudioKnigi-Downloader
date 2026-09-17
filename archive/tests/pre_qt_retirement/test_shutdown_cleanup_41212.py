from __future__ import annotations

import tkinter as tk

import pytest

from audioknigi.ui_kit import install_destroy_cleanup


class _FakeRoot:
    def __init__(self, *, closing=False):
        self.master = None
        self._audioknigi_closing = closing


class _FakeWidget:
    def __init__(self, root, *, message="can't delete Tcl command"):
        self.master = root
        self._tclCommands = ["fake-command"]
        self.message = message

    def destroy(self):
        raise tk.TclError(self.message)


def test_shutdown_duplicate_tcl_command_is_suppressed_only_during_teardown():
    root = _FakeRoot(closing=True)
    widget = _FakeWidget(root)
    calls = []
    assert install_destroy_cleanup(widget, lambda: calls.append("cleanup")) is True

    assert widget.destroy() is None
    assert calls == ["cleanup"]
    assert widget._tclCommands is None


def test_duplicate_tcl_command_still_surfaces_during_normal_runtime():
    root = _FakeRoot(closing=False)
    widget = _FakeWidget(root)
    assert install_destroy_cleanup(widget, lambda: None) is True

    with pytest.raises(tk.TclError, match="can't delete Tcl command"):
        widget.destroy()


def test_other_tcl_errors_are_not_hidden_during_shutdown():
    root = _FakeRoot(closing=True)
    widget = _FakeWidget(root, message="invalid command name .broken")
    assert install_destroy_cleanup(widget, lambda: None) is True

    with pytest.raises(tk.TclError, match="invalid command name"):
        widget.destroy()


def test_real_tk_root_shutdown_tolerates_already_deleted_widget_command():
    root = tk.Tk()
    root.withdraw()
    frame = tk.Frame(root)
    frame.pack()
    assert install_destroy_cleanup(frame, lambda: None) is True
    # Reproduce the Python 3.14/Tk shutdown symptom: Python bookkeeping still
    # references a command that Tcl no longer owns.
    frame._tclCommands = ["audioknigi-command-already-gone"]
    root._audioknigi_closing = True
    root.destroy()
