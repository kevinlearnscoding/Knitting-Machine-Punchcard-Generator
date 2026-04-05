# 🧶 Knitting Machine Punchcard Generator
---
Generate punchcard die-cutting files from PCX and PNG image charts.

![Punch Card](https://img.shields.io/badge/Punch%20Card-Knitting%20Machine-green?labelColor=grey)
![SVG](https://img.shields.io/badge/SVG-Die%20Cutting-red?labelColor=grey)
![Python](https://img.shields.io/badge/Python-Programming-blue?logo=python&logoColor=yellow)


This uttility generates SVG files, usable in most diecutting machines, for punchcards for 12-stitch and 24-stitch punch card machines, from PCX and PNG images. A large library of PCX and PNG image charts are available from https://github.com/kevinlearnscoding/Machine-Knitters-Companion 

---

## ✨ Features

- 🎯 Generate SVG cut files for punchcards from PNG or PCX images
- 🧵 Supports 12-stitch and 24-stitch card widths
- 🔁 Layout modes: `auto`, `motif`, and `repeat`
- 📏 Vertical repeats for longer pattern runs
- 🧪 Batch processing from shell globs and stdin
- ⚙️ Threshold and inversion controls for image-to-punch mapping

## 🚀 Quick Start

Install python and Pillow dependency

```bash
python3 -m pip install Pillow
```
Determine what kind of punch card machine your using (12-stitch or 24-stich), how many repeats across the width of the card you want, and how many vertical repeats you want the card. Format your input as: 

```bash
python3 punchcard-generator.py design.png 24 motif 6
````

Output file:

- `design.punch.svg`

For a full beginner walkthrough, see the QuickStart guide: [QUICKSTART.md](QUICKSTART.md)

## 📦 Requirements

- Python 3.8+
- Pillow (`pip install Pillow`)

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
- `--stitches {12,24}` card width (default `24`)
- `--layout {auto,motif,repeat}` layout mode (default `auto`)
- `--repeat-height N` vertical repeats (default `1`)
- `--threshold 0-255` image threshold (default `255`)
- `--invert` invert punched and non-punched spaces on the card
- `--hole-ratio 0-1` hole size ratio (default `0.55`)

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
