#!/usr/bin/env python3
import sys
import os
import argparse
from PIL import Image

try:
    import cairosvg
except ImportError:
    cairosvg = None


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

PAPER_SIZES_MM = {
    "letter": (215.9, 279.4),
    "a4": (210.0, 297.0),
    "legal": (215.9, 355.6),
}

TEMPLATE_MARGINS_MM = {
    "left": 14.0,
    "right": 10.0,
    "top": 12.0,
    "bottom": 12.0,
}

TEMPLATE_ROW_NUMBER_GUTTER_MM = 10.0
TEMPLATE_HEADER_MM = 10.0
TEMPLATE_FOOTER_MM = 8.0

TEMPLATE_MACHINE_ROW_SHIFT = {
    "brother": 7,
    "silverreed": 5,
}

BLANK_INDEXING_HOLE_DIAMETER_MM = 0.9

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


def invert_row(row):
    return "".join("-" if ch == "x" else "x" for ch in row)


def apply_double_bed_jacquard_chart(rows, start_color="background"):
    """
    Convert a standard 2-color chart into DBJ punch selection rows.

    - process rows bottom-up
    - alternate pair order by parity
    - emit two rows for each input row
    - flip stack back to top-down for output
    """
    if start_color not in ("background", "foreground"):
        raise ValueError("DBJ start color must be 'background' or 'foreground'")

    bottom_up_rows = rows[::-1]
    final_stack = []

    for i, row in enumerate(bottom_up_rows):
        row_num = i + 1
        inverted = invert_row(row)
        odd_row = row_num % 2 != 0

        if start_color == "background":
            if odd_row:
                final_stack.append(row)
                final_stack.append(inverted)
            else:
                final_stack.append(inverted)
                final_stack.append(row)
        else:
            if odd_row:
                final_stack.append(inverted)
                final_stack.append(row)
            else:
                final_stack.append(row)
                final_stack.append(inverted)

    return final_stack[::-1]


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
    machine_type=None,
    indexing_hole_diameter=None,
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
    row_number_shift = TEMPLATE_MACHINE_ROW_SHIFT.get(machine_type)

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

    def add_pattern_row(row_text, y, row_number=None):
        x = pattern_hole_xoffset
        for ch in row_text:
            if ch == "x":
                radius = pattern_hole_diameter / 2.0
                parts.append(
                    f'  <circle cx="{x}" cy="{y}" r="{radius}" fill="white" stroke="black" stroke-width="0.1"/>'
                )
            elif indexing_hole_diameter is not None:
                radius = indexing_hole_diameter / 2.0
                parts.append(
                    f'  <circle cx="{x}" cy="{y}" r="{radius}" fill="white" stroke="black" stroke-width="0.1"/>'
                )
            x += stitch_width

        if row_number is not None:
            label_x = pattern_hole_xoffset - 2.0
            parts.append(
                f'  <text x="{label_x}" y="{y}" text-anchor="end" dominant-baseline="middle" font-family="sans-serif" font-size="2.2" fill="#222">{row_number}</text>'
            )

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
    for row_index, row in enumerate(rows, start=1):
        row_number = None
        if row_number_shift is not None:
            absolute_row_from_bottom = card_rows - row_index + 1
            row_number = ((absolute_row_from_bottom - row_number_shift - 1) % card_rows) + 1
        add_pattern_row(row, y, row_number=row_number)
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


def chunk_rows(rows, chunk_size):
    if chunk_size < 1:
        raise ValueError("Chunk size must be at least 1")
    return [rows[i:i + chunk_size] for i in range(0, len(rows), chunk_size)]


def calculate_template_rows_per_page(card_stitches, paper_size, multi_page=False, include_row_numbers=False):
    if paper_size not in PAPER_SIZES_MM:
        raise ValueError(f"Unsupported paper size '{paper_size}'")

    config = BROTHER_CARD_PROFILES.get(card_stitches)
    if config is None:
        raise ValueError(f"Unsupported stitch width for templates: {card_stitches}")

    paper_width, paper_height = PAPER_SIZES_MM[paper_size]
    usable_width = paper_width - TEMPLATE_MARGINS_MM["left"] - TEMPLATE_MARGINS_MM["right"]
    row_number_gutter = TEMPLATE_ROW_NUMBER_GUTTER_MM if include_row_numbers else 0.0
    required_width = (config["stitch_width"] * card_stitches) + row_number_gutter
    if required_width > usable_width:
        raise ValueError(
            f"Template width {required_width:.1f}mm exceeds printable width {usable_width:.1f}mm on {paper_size}"
        )

    usable_height = paper_height - TEMPLATE_MARGINS_MM["top"] - TEMPLATE_MARGINS_MM["bottom"] - TEMPLATE_HEADER_MM
    if multi_page:
        usable_height -= TEMPLATE_FOOTER_MM

    rows_per_page = int(usable_height // config["row_height"])
    if rows_per_page < 1:
        raise ValueError(f"No rows fit on {paper_size} with current template settings")
    return rows_per_page


def prompt_letter_template_choice(total_rows, letter_rows_per_page):
    print(
        "Template can be generated as a single Legal page or split across multiple Letter pages."
    )
    print(
        f"Rows: {total_rows}. Letter capacity/page: {letter_rows_per_page}."
    )

    while True:
        choice = input("Choose [L]egal single page or [M]ultiple Letter pages [M]: ").strip().lower()
        if choice in ("", "m", "multi", "multiple", "letter"):
            return "letter-split"
        if choice in ("l", "legal"):
            return "legal-single"
        print("Please enter 'L' for Legal or 'M' for multiple Letter pages.")


def choose_template_pagination(total_rows, card_stitches, template_size, allow_prompt, include_row_numbers=False):
    if template_size == "a4":
        a4_rows = calculate_template_rows_per_page(
            card_stitches,
            "a4",
            multi_page=True,
            include_row_numbers=include_row_numbers,
        )
        if total_rows <= a4_rows:
            return "a4", total_rows
        return "a4", a4_rows

    letter_rows = calculate_template_rows_per_page(
        card_stitches,
        "letter",
        multi_page=True,
        include_row_numbers=include_row_numbers,
    )
    if total_rows <= letter_rows:
        return "letter", total_rows

    legal_rows = calculate_template_rows_per_page(
        card_stitches,
        "legal",
        multi_page=False,
        include_row_numbers=include_row_numbers,
    )
    if total_rows <= legal_rows:
        if allow_prompt:
            template_choice = prompt_letter_template_choice(total_rows, letter_rows)
            if template_choice == "legal-single":
                return "legal", total_rows
        return "letter", letter_rows

    return "letter", letter_rows


def render_template_svg_page(
    rows,
    card_stitches,
    paper_size,
    row_start_index,
    page_index,
    total_pages,
    total_card_rows,
    row_number_shift=None,
    hole_ratio=0.55,
):
    config = BROTHER_CARD_PROFILES.get(card_stitches)
    if config is None:
        raise ValueError(f"Unsupported stitch width for templates: {card_stitches}")

    paper_width, paper_height = PAPER_SIZES_MM[paper_size]
    row_height = config["row_height"]
    stitch_width = config["stitch_width"]
    pattern_hole_diameter = config["pattern_hole_diameter"] * (hole_ratio / 0.55)

    template_width = stitch_width * card_stitches
    template_height = row_height * len(rows)
    include_row_numbers = row_number_shift is not None
    row_number_gutter = TEMPLATE_ROW_NUMBER_GUTTER_MM if include_row_numbers else 0.0
    x0 = TEMPLATE_MARGINS_MM["left"] + row_number_gutter
    y0 = TEMPLATE_MARGINS_MM["top"] + TEMPLATE_HEADER_MM

    row_end_index = row_start_index + len(rows) - 1
    multi_page = total_pages > 1

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" baseProfile="full" width="{paper_width}mm" height="{paper_height}mm" viewBox="0 0 {paper_width} {paper_height}" preserveAspectRatio="none">'
    )
    parts.append(f'  <rect x="0" y="0" width="{paper_width}" height="{paper_height}" fill="white"/>')

    if multi_page:
        header_text = (
            f"Punchcard Template ({paper_size.upper()}) - Page {page_index}/{total_pages} - Rows {row_start_index}-{row_end_index}"
        )
    else:
        header_text = f"Punchcard Template ({paper_size.upper()}) - {card_stitches} stitch"
    parts.append(
        f'  <text x="{TEMPLATE_MARGINS_MM["left"]}" y="{TEMPLATE_MARGINS_MM["top"] + 6}" font-family="sans-serif" font-size="4" fill="#111">{header_text}</text>'
    )

    parts.append(
        f'  <rect x="{x0}" y="{y0}" width="{template_width}" height="{template_height}" fill="none" stroke="#111" stroke-width="0.2"/>'
    )

    # Light alignment grid for easier visual matching while hand punching.
    for col in range(card_stitches + 1):
        x = x0 + col * stitch_width
        parts.append(
            f'  <line x1="{x}" y1="{y0}" x2="{x}" y2="{y0 + template_height}" stroke="#ddd" stroke-width="0.12"/>'
        )
    for row_idx in range(len(rows) + 1):
        y = y0 + row_idx * row_height
        parts.append(
            f'  <line x1="{x0}" y1="{y}" x2="{x0 + template_width}" y2="{y}" stroke="#ddd" stroke-width="0.12"/>'
        )

    radius = pattern_hole_diameter / 2.0
    for row_idx, row_text in enumerate(rows):
        cy = y0 + row_idx * row_height + (row_height / 2.0)
        absolute_row_from_top = row_start_index + row_idx
        absolute_row_from_bottom = total_card_rows - absolute_row_from_top + 1
        if include_row_numbers:
            row_number = ((absolute_row_from_bottom - row_number_shift - 1) % total_card_rows) + 1
            parts.append(
                f'  <text x="{x0 - 1.0}" y="{cy}" text-anchor="end" dominant-baseline="middle" font-family="sans-serif" font-size="2.8" fill="#444">{row_number}</text>'
            )
        for col_idx, ch in enumerate(row_text):
            cx = x0 + col_idx * stitch_width + (stitch_width / 2.0)
            if ch == "x":
                parts.append(
                    f'  <circle cx="{cx}" cy="{cy}" r="{radius}" fill="black" stroke="black" stroke-width="0.12"/>'
                )
            else:
                parts.append(
                    f'  <circle cx="{cx}" cy="{cy}" r="{radius}" fill="white" stroke="#888" stroke-width="0.1"/>'
                )

    if multi_page:
        footer_bits = []
        if page_index > 1:
            footer_bits.append(f"continued from page {page_index - 1}")
        if page_index < total_pages:
            footer_bits.append(f"continues on page {page_index + 1}")
        footer_text = " | ".join(footer_bits)
        parts.append(
            f'  <text x="{TEMPLATE_MARGINS_MM["left"]}" y="{paper_height - 4.0}" font-family="sans-serif" font-size="3" fill="#333">{footer_text}</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def convert_svg_to_pdf(svg_text, pdf_path):
    if cairosvg is None:
        raise RuntimeError(
            "PDF template output requires CairoSVG. Install with: python3 -m pip install cairosvg"
        )
    cairosvg.svg2pdf(bytestring=svg_text.encode("utf-8"), write_to=pdf_path)


def write_template_output(
    output_base,
    rows,
    card_stitches,
    template_size,
    template_machine=None,
    hole_ratio=0.55,
):
    allow_prompt = sys.stdin.isatty() and sys.stdout.isatty()
    row_number_shift = TEMPLATE_MACHINE_ROW_SHIFT.get(template_machine)
    paper_size, rows_per_page = choose_template_pagination(
        total_rows=len(rows),
        card_stitches=card_stitches,
        template_size=template_size,
        allow_prompt=allow_prompt,
        include_row_numbers=row_number_shift is not None,
    )

    page_rows = chunk_rows(rows, rows_per_page)
    total_pages = len(page_rows)
    row_start = 1

    for idx, rows_chunk in enumerate(page_rows, start=1):
        svg_text = render_template_svg_page(
            rows_chunk,
            card_stitches=card_stitches,
            paper_size=paper_size,
            row_start_index=row_start,
            page_index=idx,
            total_pages=total_pages,
            total_card_rows=len(rows),
            row_number_shift=row_number_shift,
            hole_ratio=hole_ratio,
        )

        single_page = total_pages == 1
        if single_page:
            pdf_path = output_base + ".template.pdf"
        else:
            pdf_path = output_base + f".template-p{idx}.pdf"

        convert_svg_to_pdf(svg_text, pdf_path)
        print(f"Created: {pdf_path}")

        row_start += len(rows_chunk)

    mode = "single-page" if total_pages == 1 else "multi-page"
    print(
        f"Template layout: {mode}, paper: {paper_size}, pages: {total_pages}, rows: {len(rows)}"
    )


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
    chart_mode="normal",
    dbj_start_color="background",
    template_size=None,
    template_machine=None,
):
    img = open_flattened_rgb_image(input_path)
    rows, width_cells, height_cells = build_punch_rows(img, threshold=threshold, invert=invert)

    if chart_mode == "dbj":
        rows = apply_double_bed_jacquard_chart(rows, start_color=dbj_start_color)

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

    if punchcard_mode == "template":
        write_template_output(
            output_base=output_base,
            rows=output_rows,
            card_stitches=card_stitches,
            template_size=template_size or "letter",
            template_machine=template_machine,
            hole_ratio=hole_ratio,
        )
        if layout_used is not None:
            print(f"Card layout: {layout_used}, width: {card_stitches}, rows: {len(output_rows)}")
        return

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
                machine_type=template_machine,
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


def calculate_blank_rows_for_paper(card_stitches, paper_size="letter"):
    if paper_size not in PAPER_SIZES_MM:
        raise ValueError(f"Unsupported paper size '{paper_size}'")

    config = BROTHER_CARD_PROFILES.get(card_stitches)
    if config is None:
        raise ValueError(f"Unsupported stitch width for blank card mode: {card_stitches}")

    _, paper_height = PAPER_SIZES_MM[paper_size]
    pattern_hole_yoffset = config["pattern_hole_yoffset"]
    row_height = config["row_height"]

    # Card height = 2*y_offset + (rows-1)*row_height
    max_rows = int(((paper_height - (2.0 * pattern_hole_yoffset)) / row_height) + 1)
    return max(1, max_rows)


def generate_blank_punchcard(
    output_base,
    row_count,
    output_mode="svg",
    hole_ratio=0.55,
    template_size=None,
    template_machine=None,
    include_indexing=True,
):
    if row_count < 1:
        raise ValueError("Blank row count must be at least 1")

    rows = ["-" * 24 for _ in range(row_count)]

    if output_mode == "template":
        write_template_output(
            output_base=output_base,
            rows=rows,
            card_stitches=24,
            template_size=template_size or "letter",
            template_machine=template_machine,
            hole_ratio=hole_ratio,
        )
        print(f"Blank card: width: 24, rows: {len(rows)}")
        return

    if output_mode in ("text", "both"):
        txt_path = output_base + ".punch.txt"
        write_punch_text(txt_path, rows)
        print(f"Created: {txt_path}")

    if output_mode in ("svg", "both"):
        svg_path = output_base + ".punch.svg"
        indexing_hole_diameter = BLANK_INDEXING_HOLE_DIAMETER_MM if include_indexing else None
        write_brother_style_svg(
            svg_path,
            rows,
            card_stitches=24,
            hole_ratio=hole_ratio,
            machine_type=template_machine,
            indexing_hole_diameter=indexing_hole_diameter,
        )
        print(f"Created: {svg_path}")

    print(f"Blank card: width: 24, rows: {len(rows)}, indexing: {'on' if include_indexing else 'off'}")


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
    chart_mode="normal",
    dbj_start_color="background",
    template_size=None,
    template_machine=None,
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
            chart_mode=chart_mode,
            dbj_start_color=dbj_start_color,
            template_size=template_size,
            template_machine=template_machine,
        )
    except Exception as e:
        print(f"Error on {input_path}: {e}", file=sys.stderr)


def parse_shorthand_tokens(tokens):
    input_files = []
    unknown_tokens = []

    shorthand = {
        "stitches": None,
        "layout": None,
        "repeat_height": None,
        "chart_mode": None,
        "dbj_start_color": None,
        "output_mode": None,
        "template_requested": False,
        "template_size": None,
        "template_machine": None,
        "blank_requested": False,
    }

    for token in tokens:
        lowered = token.lower()
        ext = os.path.splitext(token)[1].lower()

        # Positional 'blank' is intentionally unsupported; use --blank.
        if lowered == "blank":
            unknown_tokens.append("blank")
            continue

        # Preserve common file-like tokens first to avoid false shorthand matches.
        if ext in (".pcx", ".png") or os.path.sep in token or os.path.exists(token):
            input_files.append(token)
            continue

        if lowered in ("12", "24"):
            shorthand["stitches"] = int(lowered)
            continue

        if lowered in ("auto", "motif", "repeat"):
            shorthand["layout"] = lowered
            continue

        if lowered.isdigit() and int(lowered) >= 1:
            shorthand["repeat_height"] = int(lowered)
            continue

        if lowered in ("normal", "dbj"):
            shorthand["chart_mode"] = lowered
            continue

        if lowered in ("background", "foreground"):
            shorthand["dbj_start_color"] = lowered
            continue

        if lowered == "template":
            shorthand["template_requested"] = True
            continue

        if lowered in ("letter", "a4"):
            shorthand["template_requested"] = True
            shorthand["template_size"] = lowered
            continue

        if lowered in ("brother", "silverreed"):
            shorthand["template_machine"] = lowered
            continue

        if lowered in ("svg", "text", "both"):
            shorthand["output_mode"] = lowered
            continue

        unknown_tokens.append(token)

    return input_files, shorthand, unknown_tokens

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
        "--template",
        nargs="?",
        const="letter",
        choices=["letter", "a4"],
        help="Generate printable template pages. Optional size: letter (default) or a4.",
    )
    parser.add_argument(
        "--machine",
        "--template-machine",
        dest="machine_type",
        choices=["brother", "silverreed"],
        help="Machine profile for shifted row numbering on SVG or template PDF output.",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=255,
        help=argparse.SUPPRESS, 
    )
    parser.add_argument(
        "--invert",
        action="store_true",
        help="Invert the punchcard, often used for tuck stitch patterns",
    )
    parser.add_argument(
        "--cell-size",
        type=float,
        default=10.0,
        help=argparse.SUPPRESS, 
    )
    parser.add_argument(
        "--margin",
        type=float,
        default=12.0,
        help=argparse.SUPPRESS, 
    )
    parser.add_argument(
        "--hole-ratio",
        type=float,
        default=0.55,
        help=argparse.SUPPRESS, 
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
        help="Card layout: Motif centers the design on the card, repeat tiles it across the card, auto picks whichever fits.",
    )
    parser.add_argument(
        "--repeat-height",
        type=int,
        default=1,
        help="Number of vertical repeats for card pattern. Default: 1.",
    )
    parser.add_argument(
        "--chart-mode",
        choices=["normal", "dbj"],
        default="normal",
        help="Chart conversion mode. normal keeps rows unchanged; dbj applies double-bed jacquard conversion (2-color designs).",
    )
    parser.add_argument(
        "--dbj-start-color",
        choices=["background", "foreground"],
        default="background",
        help="When --chart-mode dbj is used, first knitted row color. Default: background.",
    )
    parser.add_argument(
        "--blank",
        nargs="?",
        const=-1,
        default=None,
        type=int,
        metavar="ROWS",
        help="Generate a blank 24-stitch punch card. Optional ROWS value sets row count (e.g. --blank 35).",
    )
    parser.add_argument(
        "--omit-index",
        "--omit-indexing",
        dest="omit_indexing",
        action="store_true",
        help="Blank mode only: omit tiny indexing holes in stitch positions.",
    )
    parser.add_argument("-help", action="help", help="Show this help message and exit.")

    parser.add_argument(
        "inputs",
        nargs="*",
        help="Input image file(s). Also accepts free-order shorthand tokens (e.g. 24, motif, dbj, template, letter, brother, svg).",
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

    if args.blank is not None and args.blank != -1 and args.blank < 1:
        parser.error("--blank ROWS must be at least 1")

    input_files, shorthand, unknown_tokens = parse_shorthand_tokens(args.inputs)

    if unknown_tokens:
        if len(unknown_tokens) == 1 and unknown_tokens[0] == "blank":
            parser.error("Positional 'blank' is no longer supported. Use --blank instead.")
        parser.error(
            "Unrecognized shorthand token(s): "
            + ", ".join(unknown_tokens)
            + ". Use explicit flags for these values."
        )

    stitches = shorthand["stitches"] if shorthand["stitches"] is not None else args.stitches
    layout = shorthand["layout"] if shorthand["layout"] is not None else args.layout
    repeat_height = shorthand["repeat_height"] if shorthand["repeat_height"] is not None else args.repeat_height
    chart_mode = shorthand["chart_mode"] if shorthand["chart_mode"] is not None else args.chart_mode
    dbj_start_color = (
        shorthand["dbj_start_color"]
        if shorthand["dbj_start_color"] is not None
        else args.dbj_start_color
    )

    template_size = args.template
    if template_size is None and shorthand["template_requested"]:
        template_size = shorthand["template_size"] or "letter"

    template_machine = args.machine_type if args.machine_type is not None else shorthand["template_machine"]
    blank_requested = args.blank is not None

    if template_size is not None:
        output_mode = "template"
    elif shorthand["output_mode"] is not None:
        output_mode = shorthand["output_mode"]
    else:
        output_mode = args.format

    if template_machine is not None and output_mode == "text":
        parser.error("Machine numbering requires SVG output (svg, both, or template mode)")

    if blank_requested and input_files:
        parser.error("Use either image input file(s) or blank mode (--blank), not both")

    if args.omit_indexing and input_files:
        parser.error("--omit-index/--omit-indexing cannot be combined with image input file(s)")

    if args.omit_indexing and not blank_requested:
        parser.error("--omit-index/--omit-indexing is only valid when using blank card mode (--blank)")

    if repeat_height < 1:
        parser.error("repeat height must be at least 1")

    if not input_files and args.inputs and sys.stdin.isatty():
        parser.error("No input files provided")

    # 1. Blank mode (e.g., punchcard --blank 60)
    if blank_requested:
        blank_rows = args.blank if args.blank != -1 else None
        if blank_rows is None:
            blank_rows = calculate_blank_rows_for_paper(24, paper_size="letter")

        output_base = determine_output_base("blank", args.o, args.d)
        generate_blank_punchcard(
            output_base=output_base,
            row_count=blank_rows,
            output_mode=output_mode,
            hole_ratio=args.hole_ratio,
            template_size=template_size,
            template_machine=template_machine,
            include_indexing=not args.omit_indexing,
        )

    # 2. Process direct input files (e.g., punchcard *.pcx 24 motif 6)
    if input_files:
        for input_file in input_files:
            process_file(
                input_file,
                args.o,
                args.d,
                output_mode=output_mode,
                threshold=args.threshold,
                invert=args.invert,
                cell_size=args.cell_size,
                margin=args.margin,
                hole_ratio=args.hole_ratio,
                stitches=stitches,
                layout=layout,
                repeat_height=repeat_height,
                chart_mode=chart_mode,
                dbj_start_color=dbj_start_color,
                template_size=template_size,
                template_machine=template_machine,
            )

    # 3. Process files passed via pipe (e.g., find . -name '*.pcx' | punchcard)
    if not blank_requested and not sys.stdin.isatty():
        for line in sys.stdin:
            process_file(
                line,
                args.o,
                args.d,
                output_mode=output_mode,
                threshold=args.threshold,
                invert=args.invert,
                cell_size=args.cell_size,
                margin=args.margin,
                hole_ratio=args.hole_ratio,
                stitches=stitches,
                layout=layout,
                repeat_height=repeat_height,
                chart_mode=chart_mode,
                dbj_start_color=dbj_start_color,
                template_size=template_size,
                template_machine=template_machine,
            )

    # 4. If no input was provided via either method, show the help
    if not blank_requested and not input_files and sys.stdin.isatty():
        parser.print_help()

