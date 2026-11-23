"""Move the publication key under the Peer-Reviewed Publications heading, then build the PDF.

RenderCV only allows one entry type per section, so prepare_pdf.py emits the key as its
own temporary section. This edits RenderCV's Typst output to drop that heading and place
the key text directly under "== Peer-Reviewed Publications", then compiles the PDF with
RenderCV's own Typst compiler setup (same fonts and bundled template).

Usage: python scripts/finalize_pdf.py _build/rendercv_output/<name>.typ assets/cv.pdf
Relies on RenderCV internals; the workflow pins the RenderCV version for that reason.
"""
import re
import sys
from pathlib import Path

from rendercv.renderer.pdf_png import get_typst_compiler

KEY_SECTION = "PUBLICATIONKEYPLACEHOLDER"  # must match scripts/prepare_pdf.py
TARGET = "== Peer-Reviewed Publications\n\n"

typ_path, pdf_path = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
src = typ_path.read_text(encoding="utf-8")

m = re.search(rf"== {KEY_SECTION}\n\n(.*?)\n\n(?===)", src, flags=re.S)
if not m or src.count(TARGET) != 1:
    sys.exit("finalize_pdf: could not find the key section or the Peer-Reviewed Publications "
             "heading in the Typst output; RenderCV's output format may have changed.")
key = m.group(1).strip()
src = src[:m.start()] + src[m.end():]
side = re.search(r"entries-side-space:\s*([\d.]+\w+)", src)  # align with entry text
src = src.replace(TARGET, TARGET + f"#pad(left: {side.group(1) if side else '0.2cm'})[{key}]\n\n#v(0.5em)\n\n")
typ_path.write_text(src, encoding="utf-8")

pdf_path.parent.mkdir(parents=True, exist_ok=True)
get_typst_compiler(None, typ_path.parent).compile(input=typ_path, format="pdf", output=pdf_path)
print(f"finalize_pdf: key moved under Peer-Reviewed Publications -> {pdf_path.name}")
