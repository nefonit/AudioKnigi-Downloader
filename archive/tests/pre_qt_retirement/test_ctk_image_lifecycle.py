"""Regression for stale CTkLabel/Tk PhotoImage handles."""
import audioknigi.actions as actions_module
from audioknigi.actions import ActionsMixin


class _RawLabel:
    def __init__(self, owner):
        self.owner = owner
    def configure(self, **kwargs):
        if kwargs.get("image", object()) == "":
            self.owner.native_image_valid = True


class _FakeCTkLabel:
    """Mimics the relevant CTkLabel ordering: text touches Tk before image."""
    def __init__(self):
        self.native_image_valid = False  # simulates deleted pyimage6
        self._label = _RawLabel(self)
        self.image = "stale"
        self.text = ""
        self.calls = []
    def configure(self, **kwargs):
        self.calls.append(dict(kwargs))
        # CTkLabel.configure processes text before image internally.
        if "text" in kwargs:
            if not self.native_image_valid:
                raise RuntimeError('image "pyimage6" doesn\'t exist')
            self.text = kwargs["text"]
        if "image" in kwargs:
            self.image = kwargs["image"]
            self.native_image_valid = True


class _Dummy(ActionsMixin):
    pass


original = actions_module.HAS_CUSTOMTKINTER
try:
    actions_module.HAS_CUSTOMTKINTER = True
    label = _FakeCTkLabel()
    _Dummy()._configure_image_label(label, None, "Обложка\nне загружена")
    assert label.text == "Обложка\nне загружена"
    assert label.calls[0] == {"image": None}, label.calls
    assert label.calls[1] == {"text": "Обложка\nне загружена"}, label.calls
finally:
    actions_module.HAS_CUSTOMTKINTER = original

print("CTK IMAGE LIFECYCLE REGRESSION: OK")
