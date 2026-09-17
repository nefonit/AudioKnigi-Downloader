# Safe shutdown — 4.12.12

Observed on Windows 11 with Python 3.14.7 after otherwise successful downloads:
`_tkinter.TclError: can't delete Tcl command` during `Tk.destroy()`.

The session file had already been written with `running: false`, confirming this was a final Tcl bookkeeping race rather than an application crash during work.

The fix makes close handling idempotent and suppresses only the exact duplicate-command TclError while the application/root is already tearing down. Normal runtime Tcl errors are not hidden.
