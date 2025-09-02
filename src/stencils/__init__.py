#########################################################################################
#                                                                                       #
# MIT License                                                                           #
#                                                                                       #
# Copyright (c) 2025 Ioannis D. (devcoons)                                              #
#                                                                                       #
# Permission is hereby granted, free of charge, to any person obtaining a copy          #
# of this software and associated documentation files (the "Software"), to deal         #
# in the Software without restriction, including without limitation the rights          #
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell             #
# copies of the Software, and to permit persons to whom the Software is                 #
# furnished to do so, subject to the following conditions:                              #
#                                                                                       #
# The above copyright notice and this permission notice shall be included in all        #
# copies or substantial portions of the Software.                                       #
#                                                                                       #
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR            #
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,              #
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE           #
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER                #
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,         #
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE         #
# SOFTWARE.                                                                             #
#                                                                                       #
#########################################################################################

__version__ = '0.1.2'
__name__ = "stencils"
__all__ = ["load", "TemplateConflictError", "TemplateParseError", "__version__",]

#########################################################################################
# IMPORTS                                                                               #
#########################################################################################

from pathlib import Path
from typing import Union, Iterable, Dict
import re

#########################################################################################
#########################################################################################

_START = re.compile(r"^=+\s*TEMPLATE\s*:(?P<key>[^\s=]+)\s*=+\s*$")
_END   = re.compile(r"^=+\s*/TEMPLATE\s*=+\s*$")

#########################################################################################

class TemplateConflictError(Exception): ...
class TemplateParseError(Exception): ...

#########################################################################################

class DropMissing(dict):
    """Mapping that returns '' for any missing key when used with format_map()."""
    def __missing__(self, key):
        return ""

def render(template: str, data: dict) -> str:
    """Render a template, defaulting any missing placeholder to ''."""
    return template.format_map(DropMissing(data))

#########################################################################################
#########################################################################################

def _iter_blocks_in_file(path: Path):
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception as e:
        raise TemplateParseError(f"Failed to read {path}: {e}") from e

    cur_key = None
    buf = []
    for i, line in enumerate(lines, start=1):
        if cur_key is None:
            m = _START.match(line)
            if m:
                cur_key = m.group("key").strip()
                buf = []
            elif _END.match(line):
                raise TemplateParseError(f"{path}:{i}: unexpected TEMPLATE end")
        else:
            if _END.match(line):
                yield cur_key, ("\n".join(buf)).rstrip() + "\n"
                cur_key, buf = None, []
            else:
                buf.append(line)

    if cur_key is not None:
        raise TemplateParseError(f"{path}: unclosed TEMPLATE block '{cur_key}'")

#########################################################################################

def _expand_targets(targets: Iterable[Union[str, Path]]) -> list[Path]:
    paths = []
    for t in targets:
        p = Path(t)
        if any(ch in str(p) for ch in "*?[]"):
            paths.extend(Path().glob(str(p)))
        elif p.is_dir():
            paths.extend(p.glob("*.tmpl"))
        else:
            paths.append(p)
    return [p for p in paths if p.exists()]

#########################################################################################

def load(targets: Union[str, Path, Iterable[Union[str, Path]]]) -> Dict[str, str]:

    if isinstance(targets, (str, Path)):
        targets = [targets]

    result: Dict[str, str] = {}
    provenance: Dict[str, Path] = {}

    for path in _expand_targets(targets):
        if path.is_dir():
            continue
        for key, text in _iter_blocks_in_file(path):
            if key in result:
                if result[key] != text:
                    raise TemplateConflictError(
                        f"Key '{key}' conflict: {provenance[key]} vs {path}"
                    )
                continue
            result[key] = text
            provenance[key] = path

    if not result:
        raise TemplateParseError("No templates found")
    return result

