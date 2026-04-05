#!/usr/bin/env python3
import sys
import os
import argparse
from PIL import Image


BROTHER_CARD_PROFILES = {
    24: {
        "card_width": 142.0,
        "row_height": 5.0,
        "stitch_width": 4.5,
        "pattern_hole_diameter": 3.5,
        "pattern_hole_xoffset": 19.25,
        "pattern_hole_yoffset": 12.5,
        "clip_hole_diameter": 3.5,
        "clip_hole_xoffset": 6.75,
        "clip_hole_yoffset": 5.0,
        "tractor_hole_diameter": 3.0,
        "tractor_hole_xoffset": 13.5,
        "tractor_hole_yoffset": 2.5,
        "overlapping_rows": 2,
        "overlapping_row_xoffset": 19.25,
        "overlapping_row_yoffset": 2.5,
        "corner_offset": 2.0,
        "half_hole_at_bottom": False,
    },
    12: {
        "card_width": 142.0,
        "row_height": 5.0,
        "stitch_width": 9.0,
        "pattern_hole_diameter": 3.5,
        "pattern_hole_xoffset": 24.25,
        "pattern_hole_yoffset": 12.5,
        "clip_hole_diameter": 3.5,
        "clip_hole_xoffset": 6.75,
        "clip_hole_yoffset": 5.0,
        "tractor_hole_diameter": 3.0,
        "tractor_hole_xoffset": 14.0,
        "tractor_hole_yoffset": 2.5,
        "overlapping_rows": 2,
        "overlapping_row_xoffset": 24.25,
        "overlapping_row_yoffset": 2.5,
        "corner_offset": 2.0,
        "half_hole_at_bottom": False,
    },
}

def determine_output_base(root_path, output_dir=None, recreate_dirs=None):
    if recreate_dirs:
        rel_path = os.path.relpath(root_path)
        output_base = os.path.join(recreate_dirs, rel_path)
        os.makedirs(os.path.dirname(output_base), exist_ok=True)
        return output_base

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        return os.path.join(output_dir, os.path.basename(root_path))

    return root_path


def open_flattened_rgb_image(input_path):
    with Image.open(input_path) as img:
        # Flatten transparent images to white so punch output is deterministic.
        if img.mode in ("RGBA", "LA"):
            img = img.convert("RGBA")
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[-1])
            return bg

        return img.convert("RGB")


def build_punch_rows(img, threshold=255, invert=False):
    gray = img.convert("L")
    width, height = gray.size
    rows = []

    for y in range(height):
        chars = []
        for x in range(width):
            is_punch = gray.getpixel((x, y)) < threshold
            if invert:
                is_punch = not is_punch
            chars.append("x" if is_punch else "-")
        rows.append("".join(chars))

    return rows, width, height


def write_punch_text(path, rows):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(rows))
        handle.write("\n")


def write_punch_svg(path, rows, width_cells, height_cells, cell_size=10, margin=12, hole_ratio=0.55):
    hole_diameter = max(1.0, cell_size * hole_ratio)
    hole_radius = hole_diameter / 2.0
    canvas_w = margin * 2 + width_cells * cell_size
    canvas_h = margin * 2 + height_cells * cell_size

    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{canvas_h}" viewBox="0 0 {canvas_w} {canvas_h}">')
    parts.append(f'  <rect x="0" y="0" width="{canvas_w}" height="{canvas_h}" fill="white"/>')
    parts.append(f'  <rect x="{margin}" y="{margin}" width="{width_cells * cell_size}" height="{height_cells * cell_size}" fill="none" stroke="black" stroke-width="1"/>')

    for row_index, row in enumerate(rows):
        cy = margin + row_index * cell_size + cell_size / 2.0
        for col_index, ch in enumerate(row):
            if ch != "x":
                continue
            cx = margin + col_index * cell_size + cell_size / 2.0
            parts.append(f'  <circle cx="{cx}" cy="{cy}" r="{hole_radius}" fill="none" stroke="black" stroke-width="1"/>')

    parts.append("</svg>")

    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(parts))
        handle.write("\n")


def resolve_card_layout(input_width, card_stitches, requested_layout):
    if requested_layout == "auto":
        if input_width == card_stitches:
            return "motif"
        if input_width < card_stitches and card_stitches % input_width == 0:
            return "repeat"
        return "motif"
    return requested_layout


def compose_card_rows(rows, card_stitches, card_layout, repeat_height):
    if not rows:
        raise ValueError("Input image has no rows")

    motif_width = len(rows[0])
    if motif_width == 0:
        raise ValueError("Input image has zero width")

    layout = resolve_card_layout(motif_width, card_stitches, card_layout)

    if layout == "motif":
        if motif_width > card_stitches:
            raise ValueError(
                f"Motif width {motif_width}px is wider than card width {card_stitches}px"
            )

        if repeat_height < 1:
            raise ValueError("Repeat height must be at least 1")

        pad_total = card_stitches - motif_width
        pad_left = pad_total // 2
        pad_right = pad_total - pad_left  # Odd padding favors extra pixel on the right.
        padded_rows = ["-" * pad_left + row + "-" * pad_right for row in rows]

        card_rows = []
        for _ in range(repeat_height):
            card_rows.extend(padded_rows)
        return card_rows, "motif"

    if layout == "repeat":
        if repeat_height < 1:
            raise ValueError("Repeat height must be at least 1")

        if motif_width > card_stitches:
            raise ValueError(
                f"Repeat source width {motif_width}px cannot exceed card width {card_stitches}px"
            )

        if card_stitches % motif_width != 0:
            raise ValueError(
                f"Repeat source width {motif_width}px must evenly divide card width {card_stitches}px"
            )

        horizontal_repeats = card_stitches // motif_width
        repeated_once = [row * horizontal_repeats for row in rows]
        card_rows = []
        for _ in range(repeat_height):
            card_rows.extend(repeated_once)
        return card_rows, "repeat"

    raise ValueError(f"Unsupported card layout '{layout}'")


def write_brother_style_svg(
    path,
    rows,
    card_stitches,
    hole_ratio=0.55,
):
    if not rows:
        raise ValueError("No card rows to render")

    config = BROTHER_CARD_PROFILES.get(card_stitches)
    if config is None:
        raise ValueError(f"Unsupported Brother/Silverreed/Studio stitch width: {card_stitches}")

    card_rows = len(rows)
    card_width = config["card_width"]
    row_height = config["row_height"]
    stitch_width = config["stitch_width"]
    pattern_hole_diameter = config["pattern_hole_diameter"] * (hole_ratio / 0.55)
    pattern_hole_xoffset = config["pattern_hole_xoffset"]
    pattern_hole_yoffset = config["pattern_hole_yoffset"]
    clip_hole_diameter = config["clip_hole_diameter"]
    clip_hole_xoffset = config["clip_hole_xoffset"]
    clip_hole_yoffset = config["clip_hole_yoffset"]
    tractor_hole_diameter = config["tractor_hole_diameter"]
    tractor_hole_xoffset = config["tractor_hole_xoffset"]
    tractor_hole_yoffset = config["tractor_hole_yoffset"]
    overlapping_rows = config["overlapping_rows"]
    overlapping_row_xoffset = config["overlapping_row_xoffset"]
    overlapping_row_yoffset = config["overlapping_row_yoffset"]
    corner_offset = config["corner_offset"]
    half_hole_at_bottom = config["half_hole_at_bottom"]

    card_height = (pattern_hole_yoffset * 2) + ((card_rows - 1) * row_height)

    corner_diameter = corner_offset + 1
    shape_points = [
        (corner_diameter, 0),
        (card_width - corner_diameter, 0),
        (card_width - corner_offset, 1),
        (card_width - corner_offset, 20),
        (card_width, 22),
        (card_width, card_height - 22),
        (card_width - corner_offset, card_height - 20),
        (card_width - corner_offset, card_height - 1),
        (card_width - corner_diameter, card_height),
        (corner_diameter, card_height),
        (corner_offset, card_height - 1),
        (corner_offset, card_height - 20),
        (0, card_height - 22),
        (0, 22),
        (corner_offset, 20),
        (corner_offset, 1),
    ]

    points_attr = " ".join(f"{x},{y}" for x, y in shape_points)

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" baseProfile="full" width="{card_width}mm" height="{card_height}mm" viewBox="0 0 {card_width} {card_height}" preserveAspectRatio="none">'
    )
    parts.append(
        f'  <polygon points="{points_attr}" fill="white" stroke="black" stroke-width="0.1"/>'
    )

    def add_side_holes(xoffset, yoffset, diameter):
        left_x = xoffset
        right_x = card_width - xoffset
        y = yoffset
        while y <= card_height:
            radius = diameter / 2.0
            parts.append(
                f'  <circle cx="{left_x}" cy="{y}" r="{radius}" fill="white" stroke="black" stroke-width="0.1"/>'
            )
            parts.append(
                f'  <circle cx="{right_x}" cy="{y}" r="{radius}" fill="white" stroke="black" stroke-width="0.1"/>'
            )
            y += row_height
            if y >= card_height and not half_hole_at_bottom:
                break

    def add_pattern_row(row_text, y):
        x = pattern_hole_xoffset
        for ch in row_text:
            if ch == "x":
                radius = pattern_hole_diameter / 2.0
                parts.append(
                    f'  <circle cx="{x}" cy="{y}" r="{radius}" fill="white" stroke="black" stroke-width="0.1"/>'
                )
            x += stitch_width

    # Top overlapping rows
    y = overlapping_row_yoffset
    for _ in range(overlapping_rows):
        x = overlapping_row_xoffset
        for _ in range(card_stitches):
            radius = pattern_hole_diameter / 2.0
            parts.append(
                f'  <circle cx="{x}" cy="{y}" r="{radius}" fill="white" stroke="black" stroke-width="0.1"/>'
            )
            x += stitch_width
        y += row_height

    add_side_holes(clip_hole_xoffset, clip_hole_yoffset, clip_hole_diameter)
    add_side_holes(tractor_hole_xoffset, tractor_hole_yoffset, tractor_hole_diameter)

    # Main pattern rows
    y = pattern_hole_yoffset
    for row in rows:
        add_pattern_row(row, y)
        y += row_height

    # Bottom overlapping rows
    y = card_height - overlapping_row_yoffset
    for _ in range(overlapping_rows):
        x = overlapping_row_xoffset
        for _ in range(card_stitches):
            radius = pattern_hole_diameter / 2.0
            parts.append(
                f'  <circle cx="{x}" cy="{y}" r="{radius}" fill="white" stroke="black" stroke-width="0.1"/>'
            )
            x += stitch_width
        y -= row_height

    parts.append("</svg>")

    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(parts))
        handle.write("\n")


def generate_punchcard(
    input_path,
    output_base,
    threshold=255,
    invert=False,
    punchcard_mode="both",
    cell_size=10,
    margin=12,
    hole_ratio=0.55,
    card_stitches=None,
    card_layout="auto",
    card_repeat_height=1,
):
    img = open_flattened_rgb_image(input_path)
    rows, width_cells, height_cells = build_punch_rows(img, threshold=threshold, invert=invert)

    if card_stitches is None:
        card_stitches = 24

    output_rows = rows
    output_width = width_cells
    layout_used = None

    if card_stitches is not None:
        output_rows, layout_used = compose_card_rows(
            rows,
            card_stitches=card_stitches,
            card_layout=card_layout,
            repeat_height=card_repeat_height,
        )
        output_width = card_stitches

    if punchcard_mode in ("text", "both"):
        txt_path = output_base + ".punch.txt"
        write_punch_text(txt_path, output_rows)
        print(f"Created: {txt_path}")

    if punchcard_mode in ("svg", "both"):
        svg_path = output_base + ".punch.svg"
        if card_stitches is not None:
            write_brother_style_svg(
                svg_path,
                output_rows,
                card_stitches=card_stitches,
                hole_ratio=hole_ratio,
            )
        else:
            write_punch_svg(
                svg_path,
                output_rows,
                output_width,
                len(output_rows),
                cell_size=cell_size,
                margin=margin,
                hole_ratio=hole_ratio,
            )
        print(f"Created: {svg_path}")

    if layout_used is not None:
        print(f"Card layout: {layout_used}, width: {card_stitches}, rows: {len(output_rows)}")


def process_file(
    input_path,
    output_dir=None,
    recreate_dirs=None,
    output_mode="svg",
    threshold=255,
    invert=False,
    cell_size=10,
    margin=12,
    hole_ratio=0.55,
    stitches=24,
    layout="auto",
    repeat_height=1,
):
    input_path = input_path.strip()
    if not input_path or not os.path.exists(input_path):
        return

    root_path, ext = os.path.splitext(input_path)
    ext_lower = ext.lower()

    if ext_lower not in (".pcx", ".png"):
        print(f"Error on {input_path}: Unsupported file format '{ext}'", file=sys.stderr)
        return

    output_base = determine_output_base(root_path, output_dir, recreate_dirs)

    try:
        generate_punchcard(
            input_path,
            output_base,
            threshold=threshold,
            invert=invert,
            punchcard_mode=output_mode,
            cell_size=cell_size,
            margin=margin,
            hole_ratio=hole_ratio,
            card_stitches=stitches,
            card_layout=layout,
            card_repeat_height=repeat_height,
        )
    except Exception as e:
        print(f"Error on {input_path}: {e}", file=sys.stderr)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="punchcard",
        description="Generate knitting machine punchcards from PNG or PCX images.",
        epilog="Example: punchcard motif.pcx 24 motif 6",
        add_help=True
    )
    parser.add_argument("-o", metavar="OUTPUT PATH", help="Output directory for generated file(s).")
    parser.add_argument("-d", metavar="RECREATE DIRECTORIES", help="Output directory root when recreating input folder structure.")
    parser.add_argument(
        "--format",
        choices=["text", "svg", "both"],
        default="svg",
        help="Output format. Options: text (x/-), svg, both. Default: svg.",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=255,
        help="Threshold (0-255). Pixels below threshold are punched (x). Default: 255 (anything not pure white).",
    )
    parser.add_argument(
        "--invert",
        action="store_true",
        help="Invert punch logic (bright pixels become x, dark pixels become -).",
    )
    parser.add_argument(
        "--cell-size",
        type=float,
        default=10.0,
        help="SVG only: cell size in SVG units. Default: 10.",
    )
    parser.add_argument(
        "--margin",
        type=float,
        default=12.0,
        help="SVG only: margin around punch grid in SVG units. Default: 12.",
    )
    parser.add_argument(
        "--hole-ratio",
        type=float,
        default=0.55,
        help="SVG only: hole diameter ratio relative to cell size (0-1). Default: 0.55.",
    )
    parser.add_argument(
        "--stitches",
        type=int,
        choices=[12, 24],
        default=24,
        help="Card width in stitches (12 or 24). Default: 24.",
    )
    parser.add_argument(
        "--layout",
        choices=["auto", "motif", "repeat"],
        default="auto",
        help="Card layout mode. auto picks motif when width matches; otherwise repeat when width tiles card width.",
    )
    parser.add_argument(
        "--repeat-height",
        type=int,
        default=1,
        help="Number of vertical repeats for card pattern. Default: 1.",
    )
    parser.add_argument("-help", action="help", help="Show this help message and exit.")

    parser.add_argument(
        "inputs",
        nargs="*",
        help="Input image file(s). Supports trailing shorthand: [12|24] [auto|motif|repeat] [repeat_height].",
    )
    
    args = parser.parse_args()

    if not 0 <= args.threshold <= 255:
        parser.error("--threshold must be between 0 and 255")

    if args.cell_size <= 0:
        parser.error("--cell-size must be greater than 0")

    if args.margin < 0:
        parser.error("--margin must be 0 or greater")

    if not 0 < args.hole_ratio <= 1:
        parser.error("--hole-ratio must be greater than 0 and at most 1")

    if args.repeat_height < 1:
        parser.error("--repeat-height must be at least 1")

    input_files = list(args.inputs)
    pos_stitches = None
    pos_layout = None
    pos_repeat_height = None

    # Trailing shorthand parsing for batch-friendly invocation:
    # punchcard file1.pcx file2.pcx 24 motif 6
    if len(input_files) >= 3 and input_files[-3] in ("12", "24") and input_files[-2] in ("auto", "motif", "repeat"):
        try:
            parsed_repeat = int(input_files[-1])
        except ValueError:
            parser.error("Positional repeat height must be an integer")
        if parsed_repeat < 1:
            parser.error("Positional repeat height must be at least 1")

        pos_stitches = int(input_files[-3])
        pos_layout = input_files[-2]
        pos_repeat_height = parsed_repeat
        input_files = input_files[:-3]
    elif len(input_files) >= 2 and input_files[-2] in ("12", "24") and input_files[-1] in ("auto", "motif", "repeat"):
        pos_stitches = int(input_files[-2])
        pos_layout = input_files[-1]
        input_files = input_files[:-2]
    elif len(input_files) >= 1 and input_files[-1] in ("12", "24"):
        pos_stitches = int(input_files[-1])
        input_files = input_files[:-1]

    stitches = pos_stitches if pos_stitches is not None else args.stitches
    layout = pos_layout if pos_layout is not None else args.layout
    repeat_height = pos_repeat_height if pos_repeat_height is not None else args.repeat_height

    if repeat_height < 1:
        parser.error("repeat height must be at least 1")

    if not input_files and args.inputs and sys.stdin.isatty():
        parser.error("No input files provided before positional shorthand")

    # 1. Process direct input files (e.g., punchcard *.pcx 24 motif 6)
    if input_files:
        for input_file in input_files:
            process_file(
                input_file,
                args.o,
                args.d,
                output_mode=args.format,
                threshold=args.threshold,
                invert=args.invert,
                cell_size=args.cell_size,
                margin=args.margin,
                hole_ratio=args.hole_ratio,
                stitches=stitches,
                layout=layout,
                repeat_height=repeat_height,
            )

    # 2. Process files passed via pipe (e.g., find . -name '*.pcx' | punchcard)
    if not sys.stdin.isatty():
        for line in sys.stdin:
            process_file(
                line,
                args.o,
                args.d,
                output_mode=args.format,
                threshold=args.threshold,
                invert=args.invert,
                cell_size=args.cell_size,
                margin=args.margin,
                hole_ratio=args.hole_ratio,
                stitches=stitches,
                layout=layout,
                repeat_height=repeat_height,
            )

    # 3. If no input was provided via either method, show the help
    if not input_files and sys.stdin.isatty():
        parser.print_help()

