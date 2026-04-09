# 👋 QuickStart Guide

Welcome! This guide gets you from zero to your first punchcard SVG in a few minutes. 🧶

## 1) Install dependencies

Run:

```bash
python3 -m pip install Pillow && python3 -m pip install cairosvg
```

## 2) Install as a terminal command (optional)

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
punchcard knittingchart.pcx brother 24 repeat 4
```
**or**

If you're running as a standalone script:
```bash
python3 punchcard-generator.py design.png 24 motif 6
```

What this means:

- `design.png` = your source image
- 'brother' = brother/knitking numbering (different from silverreed/singer)
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
- `--invert` invert the punchcard, punched becomes solid and solid becomes punched
- `--chart-mode dbj` convert a normal chart to double-bed jacquard format (2-color designs only)
- `--dbj-start-color foreground` set first knitted row color for DBJ
- `--blank` generate a blank 24-stitch card
- `--omit-indexing` blank mode only; remove tiny indexing holes

### Create a blank punch card

Default blank 24-stitch card (rows auto-fit to one Letter page):

```bash
python3 punchcard-generator.py --blank
```

Specify row count:

```bash
python3 punchcard-generator.py --blank 60
```

Omit tiny indexing holes:

```bash
python3 punchcard-generator.py --blank --omit-indexing
```

## 6) Printable template output (manual punching)

US Letter sized printable PDF template (default):

```bash
python3 punchcard-generator.py design.png --template
```

A4 sized printable PDF template:

```bash
python3 punchcard-generator.py design.png --template a4
```

Template with row numbering for Brother/Knitking:

```bash
python3 punchcard-generator.py design.png --template --template-machine brother
```

Template with row numbering for Silverreed/KnitMaster/Empisal/Singer/Studio/etc:

```bash
python3 punchcard-generator.py design.png --template a4 --template-machine silverreed
```

Numbering notes:

- row numbers are omitted unless machine type is set to 'brother' or 'silverreed'
- numbering is bottom-up (row position 1 is at the bottom)
- numbers are shifted upwards to compensate for the punchcard reader: 5 rows for Brother, 3 rows for Silverreed

Add machine-specific numbering to regular punchcard SVG output:

```bash
python3 punchcard-generator.py design.png brother
python3 punchcard-generator.py design.png silverreed
```

Add the right-side arrow marker in SVG output, with optional text:

```bash
python3 punchcard-generator.py design.png --arrow
python3 punchcard-generator.py design.png --arrow "My note"
```

How long cards are handled over multiple US-sized pages:

- if it fits on one US Letter page, output is one Letter page
- if it does not fit Letter but fits one US Legal page, the script will ask whether you want one Legal page or multiple Letter pages
- if it does not fit one Legal page, it automatically splits to multiple Letter pages

How long cards are handled for A4 pages:

- if it does not fit one A4 page, it automatically splits to multiple A4 pages

## 7) Double-bed jacquard (DBJ)

the 'DBJ' option automatically converts a 2-color chart into a punchcard to be used as Doulbe-Bed-Jacquard, also called Multicolored Rib

Use built-in conversion:

```bash
python3 punchcard-generator.py design.png --chart-mode dbj
```

Invert the colors if needed by setting which color is row 1:

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

### DBJ does not look correct: 

Double-bed Jacquard only works on 2-color charts

## Next step 🌟

After you confirm output looks right, open the `.punch.svg` in your diecutting software and cut. If you chose to have numbering in your SVG the numbering will need to be 


