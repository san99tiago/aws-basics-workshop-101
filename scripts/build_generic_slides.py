"""
Build a GENERIC (customer-agnostic) copy of the original AWS Services Basics deck.

- Replaces every "Wenia" reference (title, Terraform example, speaker notes, file properties).
- Paints over the "WeniaOps" branding inside the "DEMOS EN VIVO" illustration with a generic label.

Usage:
    python scripts/build_generic_slides.py <original.pptx> <output.pptx>
"""
import io
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from pptx import Presentation

GENERIC_ORG = "tu organización"

NOTE_REPLACEMENTS = [
    (r"Ejemplo para Wenia:", "Ejemplo:"),
    (r"Ejemplo Wenia:", "Ejemplo:"),
    (r"\(clave para Wenia\)", "(clave para cualquier organización)"),
    (r"muy relevante para Wenia como plataforma de activos digitales", "muy relevante para plataformas financieras y de activos digitales"),
    (r"Si Wenia ya usa", f"Si {GENERIC_ORG} ya usa"),
    (r"aterrizar a Wenia", f"aterrizar a {GENERIC_ORG}"),
    (r"Para Wenia:", f"Para {GENERIC_ORG}:"),
    (r"en Wenia", f"en {GENERIC_ORG}"),
    (r"a Wenia", f"a {GENERIC_ORG}"),
    (r"Wenia", GENERIC_ORG),
]


def replace_in_text_frame(text_frame, run_level: dict, paragraph_level: list):
    """Run-level exact replacements first (keeps formatting), then paragraph-level regex."""
    for paragraph in text_frame.paragraphs:
        for run in paragraph.runs:
            if run.text in run_level:
                run.text = run_level[run.text]
        full = "".join(r.text for r in paragraph.runs)
        if re.search("wenia", full, re.IGNORECASE):
            new = full
            for pattern, repl in paragraph_level:
                new = re.sub(pattern, repl, new)
            if paragraph.runs:
                paragraph.runs[0].text = new
                for r in paragraph.runs[1:]:
                    r.text = ""


def patch_branding_image(blob: bytes) -> bytes:
    """Cover the 'WeniaOps' labels (robot chest + bottle) with a generic 'CloudOps' label."""
    im = Image.open(io.BytesIO(blob)).convert("RGB")
    draw = ImageDraw.Draw(im)
    regions = [  # (box, text size) -> measured on the 1536x1024 illustration
        ((432, 540, 576, 588), 30),
        ((168, 720, 280, 754), 22),
    ]
    for (x0, y0, x1, y1), size in regions:
        # Median of the dark pixels in the box (ignores the bright letters being covered).
        px = [im.getpixel((x, y)) for x in range(x0, x1, 2) for y in range(y0, y1, 2)]
        dark = sorted(c for c in px if sum(c) < 260) or px
        fill = dark[len(dark) // 2]
        draw.rounded_rectangle((x0, y0, x1, y1), radius=8, fill=fill)
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", size)
        except OSError:
            font = ImageFont.load_default()
        label = "CloudOps"
        tw, th = draw.textbbox((0, 0), label, font=font)[2:]
        draw.text(((x0 + x1 - tw) / 2, (y0 + y1 - th) / 2 - 3), label, font=font, fill=(255, 255, 255))
    out = io.BytesIO()
    im.save(out, format="PNG", optimize=True)
    return out.getvalue()


def scrub_app_properties(path: str):
    """docProps/app.xml caches slide titles (TitlesOfParts); python-pptx does not touch it, so rewrite the zip."""
    import shutil
    import tempfile
    import zipfile

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pptx").name
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "docProps/app.xml":
                data = re.sub(rb"Wenia", GENERIC_ORG.encode("utf-8"), data)
            zout.writestr(item, data)
    shutil.move(tmp, path)


def main(src: str, dst: str):
    prs = Presentation(src)
    run_level = {"Wenia": "", "wenia": "mi-empresa"}
    for idx, slide in enumerate(prs.slides, start=1):
        for shape in slide.shapes:
            if shape.has_text_frame:
                replace_in_text_frame(shape.text_frame, run_level, NOTE_REPLACEMENTS)
            if shape.shape_type == 13 and shape.name == "Picture 38" and idx == 112:
                part = shape.part.related_part(shape._element.blip_rId)
                part._blob = patch_branding_image(part.blob)
                print(f"  patched branding illustration on slide {idx}")
        if slide.has_notes_slide:
            replace_in_text_frame(slide.notes_slide.notes_text_frame, {}, NOTE_REPLACEMENTS)

    core = prs.core_properties
    core.title = "AWS Services Basics 101 - Fundamentos en AWS (Español)"
    core.subject = "Introduccion a AWS, Lambda, S3, DynamoDB, Aurora, Athena, QuickSight e IaC con Terraform"
    core.keywords = "AWS, workshop, basics, serverless, S3, DynamoDB, Lambda, Athena"
    core.comments = "Deck generico para sesiones introductorias de AWS. Copyright Santiago Garcia Arango."
    prs.save(dst)
    scrub_app_properties(dst)

    # Final sanity check: no "wenia" left anywhere in the package (XML + metadata).
    import zipfile
    leftovers = [n for n in zipfile.ZipFile(dst).namelist() if b"wenia" in zipfile.ZipFile(dst).read(n).lower() and n.endswith(".xml")]
    print("  leftovers:", leftovers or "none")
    print(f"OK -> {dst}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
