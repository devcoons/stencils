# Stencils — Lightweight Template Loader for Python

[![PyPI - Version](https://img.shields.io/pypi/v/stencils?style=for-the-badge)](https://pypi.org/project/stencils)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/stencils?style=for-the-badge)
![GitHub License](https://img.shields.io/github/license/devcoons/stencils?style=for-the-badge)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/stencils?style=for-the-badge&color=%23F0F)
![PyPI - Downloads](https://img.shields.io/pypi/dm/stencils?style=for-the-badge)


## Overview

**Stencils** is a minimal, zero-dependency Python library for managing text templates embedded in files.  
It’s ideal for projects that need small, human-readable, and reusable template snippets (e.g., config fragments, codegen templates, or documentation blocks).

The library parses `.tmpl` (or any text) files containing *named template blocks*, resolves duplicates, and provides a clean dictionary-like interface for use in your code.

## Installation

```
pip install stencils
```

## Template Format

A single file can contain multiple named template blocks.  
Each block must start with a line of the form:

```
===== TEMPLATE:<name> =====
```

and must end with:

```
===== /TEMPLATE =====
```

Example:

```
===== TEMPLATE:greeting =====
Hello {name}!
Welcome to {place}.
===== /TEMPLATE =====

===== TEMPLATE:farewell =====
Goodbye {name}, see you soon!
===== /TEMPLATE =====
```

---

## Usage

### Loading Templates

```python
from stencils import load, render

templates = load("templates/example.tmpl")

print(templates["greeting"])
# Output:
# Hello {name}!
# Welcome to {place}.
```

You can also load multiple files, directories, or patterns:

```python
templates = load(["./templates", "common/*.tmpl"])
```

> Each `.tmpl` file is scanned for `TEMPLATE:` blocks.  
> Duplicate keys across files will raise `TemplateConflictError` unless the templates are **identical**.


### Rendering Templates

You can render any loaded template with a dictionary of values:

```python
text = render(templates["greeting"], {"name": "Alice", "place": "Wonderland"})
print(text)
```

Output:

```
Hello Alice!
Welcome to Wonderland.
```

Missing placeholders default to empty strings, so this is safe:

```python
render(templates["farewell"], {})
# -> "Goodbye , see you soon!"
```

### Controlling Missing or Invalid Placeholders

You can control how **missing** and **invalid** placeholders are handled via `on_missing` and `on_error` options.

```python
render(template, data, on_missing="empty", on_error="keep")
```

**Available options:**

| Parameter | Option | Description | Example Output |
|:-----------|:--------|:-------------|:---------------|
| `on_missing` | `"empty"` *(default)* | Replace missing keys with an empty string. | `"Hello , welcome!"` |
| | `"keep"` | Keep the original placeholder text `{key}` if it’s missing. | `"Hello {name}, welcome!"` |
| | `"error"` | Raise a `KeyError` for missing placeholders. | *Raises* `KeyError: 'name'` |
| `on_error` | `"keep"` *(default)* | Keep the original placeholder if formatting fails (e.g., bad spec). | `"Value: {price:.2f}"` |
| | `"empty"` | Replace invalid placeholders with an empty string. | `"Value: "` |
| | `"error"` | Raise the formatting exception immediately. | *Raises* `ValueError` or similar |


### Foreign Placeholders (`${...}`)

Some templates may include foreign placeholders (like shell or CI variables) using `${...}` syntax.  
These are **not interpreted** by Stencils and are automatically **escaped** so they remain intact.

```python
tpl = "User: {name}, shell: ${uname -u}, gha: ${{ matrix.os }}"

render(tpl, {"name": "Io"})
# -> "User: Io, shell: ${uname -u}, gha: ${{ matrix.os }}"
```

You can disable this behavior with `protect_foreign=False` if you want raw handling.


## Errors

| Exception | Description |
|------------|--------------|
| `TemplateConflictError` | Raised when a template key appears in multiple files with **different** content. |
| `TemplateParseError` | Raised on malformed templates (e.g., unclosed or nested blocks, missing start/end). |


## API Reference

### `load(targets)`
Load one or more template sources (files, directories, or globs).

**Args:**
- `targets`: Path, string, or iterable of paths/globs.

**Returns:**  
A `dict[str, str]` mapping template names to their contents.  
Each template is also available under an alias prefixed with a colon (`:{name}`).


### `render(template, data)`
Render a template using Python’s `str.format_map`, defaulting missing keys to empty strings.

**Args:**
- `template`: Template string.  
- `data`: Dict of substitutions.

**Returns:** Rendered string.


## Example Project Structure

```
myproject/
 ├── templates/
 │    ├── main.tmpl
 │    └── footer.tmpl
 └── app.py
```

```python
# app.py
from stencils import load, render

templates = load("templates")

output = render(templates["main"], {"title": "Hello World"})
print(output)
```

## 🧾 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

© 2025 Ioannis D. (devcoons)
