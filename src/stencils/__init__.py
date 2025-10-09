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

__version__ = '0.1.8'
__name__ = "stencils"
__all__ = ["load", "TemplateConflictError", "TemplateParseError", "__version__",]

#########################################################################################
# IMPORTS                                                                               #
#########################################################################################

from pathlib import Path
import string
from typing import Union, Iterable, Dict, Mapping, Literal, Any
import re

#########################################################################################
#########################################################################################

_START = re.compile(r"^\s*=+\s*TEMPLATE\s*:(?P<key>[^\s=]+)\s*=+\s*$")
_END   = re.compile(r"^\s*=+\s*/TEMPLATE\s*=+\s*$")
_FOREIGN_SYS_PLACEHOLDER = re.compile(r"\$\{([^{}]*)\}")

#########################################################################################

class TemplateConflictError(Exception): ...
class TemplateParseError(Exception): ...

#########################################################################################

class _DefaultingDict(dict):
    def __init__(self, base: Mapping[str, Any], factory):
        super().__init__(base)
        self._factory = factory
    def __missing__(self, key: str):
        return self._factory(key)

#########################################################################################

def _protect_foreign_placeholders(s: str) -> str:
    def repl(m: re.Match[str]) -> str:
        inner = m.group(1)
        return "${{" + inner + "}}"
    return _FOREIGN_SYS_PLACEHOLDER.sub(repl, s)

#########################################################################################

def _safe_format(template: str, mapping: Mapping[str, Any], *, on_missing: Literal['empty', 'keep', 'error'], on_error: Literal['empty', 'keep', 'error']) -> str:
    fmt = string.Formatter()
    out: list[str] = []
    for literal, field_name, format_spec, conversion in fmt.parse(template):
        out.append(literal)
        if field_name is None:
            continue
        placeholder = "{"+field_name
        if conversion:
            placeholder += "!" + conversion
        if format_spec:
            placeholder += ":" + format_spec
        placeholder += "}"
        try:
            obj, _ = fmt.get_field(field_name, (), mapping)
            if conversion:
                obj = fmt.convert_field(obj, conversion)
            rendered = fmt.format_field(obj, format_spec)
            out.append(rendered)
        except KeyError:
            if on_missing == 'error':
                raise
            elif on_missing == 'keep':
                out.append(placeholder)
            else: 
                out.append('')
        except Exception:
            if on_error == 'error':
                raise
            elif on_error == 'keep':
                out.append(placeholder)
            else: 
                out.append('')
    return "".join(out)

#########################################################################################

def render(template: str, data: Mapping[str, Any] | None = None, *, on_missing: Literal['empty', 'keep', 'error'] = 'empty', on_error: Literal['empty', 'keep', 'error'] = 'keep',  protect_foreign: bool = True) -> str:
    """Render a template, defaulting any missing placeholder to ''."""
    data = {} if data is None else data
    if protect_foreign:
        template = _protect_foreign_placeholders(template)
        
    return _safe_format(template, data, on_missing=on_missing, on_error=on_error)

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
            result[f":{key}"] = text
            provenance[key] = path

    if not result:
        raise TemplateParseError("No templates found")
    return result

