# StarType23

![StarType23 screenshot](src/media/powershell_screenshot.png)

A CLI tool that walks a directory, counts files by extension, and renders a
colourful file-type distribution chart in the terminal.

## Features

- Scans recursively and groups files by extension (count and disk size).
- Renders a stacked proportion bar + a table with coloured mini bars.
- Two modes: by **count** (`startype23`) or by **size** (`startype23 --size`).
- Built-in lookup table of ~500 extensions with file-type category and
  one-line description (`--explain .py`).
- Column visibility toggles: `--filetype`, `--count`, `--percentage`,
  `--distribution`.
- Skips `.git`, `.venv`, `node_modules`, `__pycache__`, and similar by
  default.
- Flat-design pastel colour palette (no neon).
- Custom colour palette support via ``--colors`` (inline hex codes or file).

## Installation

```bash
uv tool install startype23
# or via pip:
pip install startype23
```

After installation, both `startype23` and `st23` are available globally.

## Usage

```
startype23 (or st23)                    scan current directory
startype23 --size                       scan by disk size
startype23 --path /some/dir             scan a specific directory
startype23 --include-hidden             include dotfiles
startype23 --explain .py                look up an extension
startype23 --explain py                 leading dot is optional
startype23 --exclude build              skip extra directories
startype23 --count --percentage         show only selected columns
startype23 --colors FF0000 --colors 00FF00   custom colours
startype23 --colors "#FF0000,#00FF00"       comma-separated in one string
startype23 --colors /path/to/colors.txt     load from file
startype23 --filter ".py,.md"              show only certain file types
startype23 --interactive                   build flags in a REPL
```

| Flag                       | Description                                   |
|----------------------------|-----------------------------------------------|
| `--path`                   | Directory to scan (default: `.`)              |
| `--exclude` / `-x`         | Extra directory names to skip (repeatable)    |
| `--include-hidden`         | Include dotfiles in the scan                  |
| `--no-include-hidden`      | Exclude dotfiles (default)                    |
| `--explain` / `-e`         | Look up an extension and show its description |
| `--size` / `-s`            | Size distribution instead of count            |
| `--filetype` / `-ft`       | Show the File Type column                     |
| `--count` / `-c`           | Show the Count column                         |
| `--percentage` / `-p`      | Show the Percentage column                    |
| `--distribution` / `-d`    | Show the Distribution bar column              |
| `--colors`                 | Hex colour codes, one per flag, comma/space/semicolon/colon separated, or path to a colour file |
| `--borderless`             | Render tables without outer borders              |
| `--filter`                 | Show only matching extensions (comma, period, colon, semicolon, newline separated) |
| `--interactive`            | Launch interactive REPL mode for building flags  |

When no column flags are given, all columns show.  When one or more are
given, only those (plus Extension) are shown.

Custom colours can be provided inline or via a text file. The ``#`` prefix is
optional. If fewer colours are given than file types found, the tool falls
back to the built-in palette and prints a warning.  A default colour file at
``$HOME/.config/startype23/colors.txt`` is loaded automatically if no
``--colors`` flag is given.

### Interactive mode

``--interactive`` opens a REPL where flags are toggled one at a time, then
``run`` executes the scan.  Type ``help`` within the REPL for available
commands.

## Tools used to build this project

- **Python 3.10+** -- language runtime.
- **uv** -- package and project manager (install, build, publish).
- **click** -- CLI framework (arguments, options, help).
- **rich** -- terminal styling (tables, colours, text formatting).
- **hatchling** -- build backend (PEP 517).
- **Wikipedia's List of filename extensions** -- source for the ~500-entry
  extension lookup table.

