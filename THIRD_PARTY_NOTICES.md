# Third-party notices

The Knigavuhe integration design was informed by the user-supplied `knigavuhe_downloader` project. Its MIT license is reproduced below.

## knigavuhe_downloader

MIT License

Copyright (c) 2025 Band1kut

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Release/runtime components

The Windows standalone build also includes or relies on third-party runtime
components.  Their upstream license terms remain controlling; this notice is a
summary, not a replacement for those licenses.

- **PySide6 / Qt for Python** — distributed by The Qt Company under the
  applicable Qt for Python open-source/commercial licensing terms (including
  LGPLv3/GPLv3 options for open-source use). Release packaging must preserve
  the notices and license material required by the selected terms.
- **Playwright for Python** — Apache License 2.0.
- **Requests** — Apache License 2.0.
- **Pillow** — HPND-style Pillow license.
- **Mutagen** — GPL-2.0-or-later.
- **PyInstaller / PyInstaller bootloader** — PyInstaller is distributed under
  GPL-2.0 with its project-specific exception for bundled applications (and
  Apache-2.0 for designated files). Generated executables must still comply
  with the licenses of all bundled dependencies.
- **FFmpeg / FFprobe** — the Windows release build bundles the actual media-tool
  binaries found by `build_qt_ci.ps1`. FFmpeg licensing depends on how those
  binaries were configured (LGPL/GPL and enabled codecs). Release engineering
  must ship the license/source-offer material required by the exact binary
  being bundled; do not assume a single license from the executable name alone.

`THIRD_PARTY_NOTICES.md` records attribution, while the release process remains
responsible for carrying the complete upstream license files required by the
actual dependency/binary set.

## Project licensing status

No top-level project license is declared in this source tree. Before public
distribution of a standalone executable, the project owner should choose and
document an application license and review the obligations of the exact
dependency/binary set being shipped (notably Mutagen and the selected Qt/FFmpeg
terms). This file is release-engineering guidance, not legal advice.
