from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from audioknigi.brand import AUTHOR_NAME, COPYRIGHT_YEAR, DISPLAY_NAME
from audioknigi.metadata import APP_VERSION


def _version_tuple(version: str) -> tuple[int, int, int, int]:
    numbers = [int(part) for part in re.findall(r"\d+", str(version))[:4]]
    values = (numbers + [0, 0, 0, 0])[:4]
    return values[0], values[1], values[2], values[3]


def render_version_info() -> str:
    filevers = _version_tuple(APP_VERSION)
    copyright_text = f"© {COPYRIGHT_YEAR} {AUTHOR_NAME}"
    comments = f"Автор и разработчик: {AUTHOR_NAME}"
    return f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={filevers!r},
    prodvers={filevers!r},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        u'040904B0',
        [
          StringStruct(u'CompanyName', u'{AUTHOR_NAME}'),
          StringStruct(u'FileDescription', u'{DISPLAY_NAME}'),
          StringStruct(u'FileVersion', u'{APP_VERSION}'),
          StringStruct(u'InternalName', u'AudioKnigiDownloader_Qt'),
          StringStruct(u'LegalCopyright', u'{copyright_text}'),
          StringStruct(u'OriginalFilename', u'AudioKnigiDownloader_Qt.exe'),
          StringStruct(u'ProductName', u'{DISPLAY_NAME}'),
          StringStruct(u'ProductVersion', u'{APP_VERSION}'),
          StringStruct(u'Comments', u'{comments}')
        ]
      )
    ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""


def write_version_info(path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_version_info(), encoding="utf-8")
    return target


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    target = args[0] if args else "build/windows_version_info.txt"
    print(write_version_info(target))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
