# 👋 QuickStart Guide

Welcome! This guide gets you from zero to your first punchcard SVG in a few minutes. 🧶

## 1) Install dependency

Run:

```bash
python3 -m pip install Pillow
```

## 2) Install as a terminal (optional)

To install the script as a system command:
```bash
cp punchcard-generator.py /usr/local/bin/punchcard
```

## 3) Navigate to your project file

```bash
cd path/to/your/knitting/charts
```
## 3) Generate your first punchcard

If you installed the punchcard command:
```bash
punchcard knittingchart.pcx 24 repeat 4
```
**or**

If you're running as a standalone script:
```bash
python3 punchcard-generator.py design.png 24 motif 6
```

What this means:

- `design.png` = your source image
- `24` = 24-stitch card width
- `motif` = center the design on the card
- `6` = repeat vertically 6 times

Output:

- `design.punch.svg`

## 4) Try these common commands

### Use defaults (simple)

```bash
python3 punchcard-generator.py design.png
```

### Repeat mode for tileable patterns

```bash
python3 punchcard-generator.py tile.png 24 repeat 3
```

### Batch process all PCX files in current folder

```bash
python3 punchcard-generator.py *.pcx 24 motif 2 -d ./output
```

### Batch process recursively with find

```bash
find . -name "*.pcx" | python3 punchcard-generator.py --stitches 24 --layout motif --repeat-height 2
```

## 5) Useful options

- `-o ./output` save generated files in a specific folder
- `-d ./output` preserve subfolder structure in output folder
- `--threshold 220` change punch sensitivity
- `--invert` invert pixel-to-punch behavior
- `--chart-mode dbj` convert a normal chart to double-bed jacquard format
- `--dbj-start-color foreground` set first knitted row color for DBJ
- `--template` generate printable template pages (defaults to Letter)
- `--template a4` generate printable template pages sized for A4
- `--template-machine brother|silverreed` enable machine-specific shifted row numbering

## 6) Printable template output (manual punching)

Letter template (default):

```bash
python3 punchcard-generator.py design.png --template
```

A4 template:

```bash
python3 punchcard-generator.py design.png --template a4
```

Template output is PDF-only (requires CairoSVG):

```bash
python3 punchcard-generator.py design.png --template
```

Template with row numbering for Brother:

```bash
python3 punchcard-generator.py design.png --template --template-machine brother
```

Template with row numbering for Silverreed:

```bash
python3 punchcard-generator.py design.png --template a4 --template-machine silverreed
```

Numbering notes:

- row numbers are omitted unless `--template-machine` is set
- numbering is bottom-up (row position 1 is at the bottom)
- shift values:
	- Brother = 7
	- Silverreed = 5

Add the same numbering to regular punchcard SVG output:

```bash
python3 punchcard-generator.py design.png --template-machine brother
python3 punchcard-generator.py design.png --template-machine silverreed
```

Letter behavior for long cards:

- if it fits on one Letter page, output one Letter page
- if it does not fit Letter but fits one Legal page, interactive runs ask whether you want one Legal page or multiple Letter pages
- if it does not fit one Legal page, it automatically splits to multiple Letter pages

A4 behavior for long cards:

- if it does not fit one A4 page, it automatically splits to multiple A4 pages

## 7) Double-bed jacquard (DBJ)

DBJ requires a converted chart (the row sequence is not a direct 1:1 from a normal chart).

Use built-in conversion:

```bash
python3 punchcard-generator.py design.png --chart-mode dbj
```

Set first knitted row color if needed:

```bash
python3 punchcard-generator.py design.png --chart-mode dbj --dbj-start-color foreground
```

## Troubleshooting 🔧

### "Unsupported file format"

Only `.png` and `.pcx` are accepted.

### "Motif width is wider than card width"


Check your image width: 1 pixel = 1 stitch

### "Repeat source width must evenly divide card width"

For 24-stitch cards, image widths like 1, 2, 3, 4, 6, 8, 12, 24 work best.

### "PDF template output requires CairoSVG"

Install the optional dependency:

```bash
python3 -m pip install cairosvg
```

## Next step 🌟

After you confirm output looks right, open the `.punch.svg` in your diecutting software and cut


