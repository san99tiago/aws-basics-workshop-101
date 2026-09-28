#!/usr/bin/env bash
# Export a .pptx to PDF headlessly with LibreOffice (macOS: brew install --cask libreoffice).
# Usage: scripts/export_slides_pdf.sh slides/AWS_Services_Basics_101_SantiGarcia.pptx
set -euo pipefail
PPTX="$1"
OUT_DIR="$(dirname "$PPTX")"
SOFFICE="${SOFFICE:-/Applications/LibreOffice.app/Contents/MacOS/soffice}"
command -v soffice >/dev/null 2>&1 && SOFFICE="$(command -v soffice)"
"$SOFFICE" --headless --norestore --convert-to pdf --outdir "$OUT_DIR" "$PPTX"
echo "PDF -> ${PPTX%.pptx}.pdf"
