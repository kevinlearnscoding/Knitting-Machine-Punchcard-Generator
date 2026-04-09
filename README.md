# 🧶 Knitting Machine Punchcard Generator
---
Generate punchcard die-cutting files from PCX and PNG image charts.

![Punch Card](https://img.shields.io/badge/Punch%20Card-Knitting%20Machine-green?labelColor=grey)
![SVG](https://img.shields.io/badge/SVG-Die%20Cutting-red?labelColor=grey)
![Python](https://img.shields.io/badge/Python-Programming-blue?logo=python&logoColor=yellow)


This utility generates SVG files, usable in most diecutting machines, for punchcards for 12-stitch and 24-stitch punch card machines, from knitting charts in PCX and PNG image file formats. A large library of PCX and PNG image charts are available from https://github.com/kevinlearnscoding/Machine-Knitters-Companion

---

## ✨ Features

- 🎯 Generate SVG cut files for punchcards from stitch charts in PNG or PCX image format
- 🧵 Supports 12-stitch and 24-stitch card widths
- 🔁 Layout modes: `motif` (center the chart on the card), `repeat` (repeat the chart across the chart), and `auto` (default; detects chart width in factors of 12/24 and chooses wether motif or repeat is best)
- 🪡 Double-bed jacquard conversion mode (`--chart-mode dbj`)
- 🖨️ Printable punching templates (`--template`) in Letter or A4
- 📄 Template output as PDF pages
- 🔢 Optional row numbering on punchcards/templats specific to Brother/Knitking/Toyota or Silver Reed/KnitMaster/Singer/Studio/Empisal/etc output (`--machine` / `--template-machine`)
- 📏 Vertical repeats for longer pattern runs
- 🧪 Batch processing from shell globs and stdin
- ⚙️ Threshold and inversion controls for image-to-punch mapping

## 🚀 Quick Start

Install dependencies:

```bash
python3 -m pip install Pillow && python3 -m pip install cairosvg
```

Optional: install as a terminal command:

```bash
cp punchcard-generator.py /usr/local/bin/punchcard
```

Generate your first punchcard (installed command):

```bash
punchcard knittingchart.pcx 24 repeat 4
```

Or run as a script:

```bash
python3 punchcard-generator.py design.png 24 motif 6
```

Meaning of arguments:

- `design.png` input image
- `24` card width in stitches
- `motif` layout mode
- `6` vertical repeats

Output file:

- `design.punch.svg`

For a full beginner walkthrough, see the QuickStart guide: [QUICKSTART.md](QUICKSTART.md)

## 📦 Requirements

- Python 3.8+
- Pillow (`pip install Pillow`)
- CairoSVG (optional, only for template PDF output: `pip install cairosvg`)

## 🛠️ Usage

### Basic

```bash
python3 punchcard-generator.py INPUT
```

### Positional shorthand

```bash
python3 punchcard-generator.py INPUT [STITCHES] [LAYOUT] [REPEAT_HEIGHT]
```

Examples:

```bash
python3 punchcard-generator.py motif.pcx 24 motif 6
python3 punchcard-generator.py tile.png 12 repeat 4
python3 punchcard-generator.py design.png 24 auto 1
```

Free-order shorthand tokens are also supported in the same command, including:

- stitches: `12`, `24`
- layout: `auto`, `motif`, `repeat`
- chart mode: `normal`, `dbj`
- DBJ start color: `background`, `foreground`
- output mode: `svg`, `text`, `both`
- template tokens: `template`, `letter`, `a4`
- machine tokens: `brother`, `silverreed`

### Batch examples

Shell glob batch:

```bash
python3 punchcard-generator.py *.pcx 24 motif 2 -d /path/to/output/dir
```

stdin batch:

```bash
find . -name "*.pcx" | python3 punchcard-generator.py --stitches 24 --layout motif --repeat-height 2
```

## 🧭 Common Options

- `-o OUTPUT_PATH` output directory
- `-d RECREATE_DIRECTORIES` recreate input directory structure in destination
- `--format {svg,text,both}` output file type (default `svg`)
- `--stitches {12,24}` card width (default `24`)
- `--layout {auto,motif,repeat}` layout mode (default `auto`)
- `--repeat-height N` vertical repeats (default `1`)
- `--chart-mode {normal,dbj}` chart conversion mode (default `normal`)
- `--dbj-start-color {background,foreground}` first knitted row color in DBJ mode (default `background`)
- `--threshold 0-255` image threshold (default `255`)
- `--invert` invert punched and non-punched spaces on the card
- `--hole-ratio 0-1` hole size ratio (default `0.55`)
- `--template [letter|a4]` generate printable hand-punch template pages; default paper is `letter`
- `--machine` / `--template-machine {brother,silverreed}` enable machine-specific shifted row numbering

## 🖨️ Printable Template Mode

Template mode creates line-drawing pages with:

- filled black circles for punched holes
- light alignment grid
- optional row numbers (enabled only when `--machine` / `--template-machine` is set)
- PDF output files

Output naming:

- single page: `name.template.pdf`
- multiple pages: `name.template-p1.pdf`, `name.template-p2.pdf`, ...

Use Letter (default):

```bash
python3 punchcard-generator.py design.png --template
```

Explicit A4 template pages:

```bash
python3 punchcard-generator.py design.png --template a4
```

Template output is PDF-only (requires CairoSVG).

Template with machine-specific row numbering:

```bash
python3 punchcard-generator.py design.png --template --template-machine brother
python3 punchcard-generator.py design.png --template a4 --template-machine silverreed
```

Numbering behavior:

- numbering is hidden unless `--machine` or `--template-machine` is provided
- numbering is calculated from bottom to top (bottom row is row position 1)
- machine shift is then applied to the displayed labels:
	- `brother`: 7-row shift
	- `silverreed`: 5-row shift

Standard punchcard SVG output can also include this numbering when machine type is provided:

```bash
python3 punchcard-generator.py design.png --machine brother
python3 punchcard-generator.py design.png --machine silverreed
python3 punchcard-generator.py design.png brother
python3 punchcard-generator.py design.png silverreed
```

Paper behavior:

- `--template` (Letter flow):
	- if it fits one Letter page, output single Letter page
	- if it does not fit Letter but fits one Legal page, interactive runs prompt for single Legal vs multiple Letter
	- if it does not fit one Legal page, output multiple Letter pages
	- non-interactive runs default to multiple Letter pages in the Legal-eligible branch
- `--template a4`:
	- if it fits one A4 page, output single A4 page
	- otherwise output multiple A4 pages

## 🧵 Double-Bed Jacquard (DBJ)

When using DBJ, the chart needs to be converted from a standard chart. 

With `--chart-mode dbj`, this tool extends the chart to compensate for the two passes of the carriage between color changes:

- process rows bottom-up
- output two punch rows for each source row
- alternate pair ordering by row parity
- flip result back to top-down order

Example:

```bash
python3 punchcard-generator.py design.png --chart-mode dbj --dbj-start-color background
```

If your setup starts with foreground first:

```bash
python3 punchcard-generator.py design.png --chart-mode dbj --dbj-start-color foreground
```

## 🧠 Layout Tips

- `motif`: centers a design within the card width
- `repeat`: tiles design across width (design width must divide by card width)
- `auto`: picks `motif` or `repeat` based on width compatibility

## 🤝 Contributing

Ideas, bug reports, and PRs are welcome.

If you tweak behavior, updating both docs keeps things smooth for users:

- `README.md`
- `QUICKSTART.md`

## 🙌 Thanks

Built for makers, tinkerers, and knitters who love automation.
