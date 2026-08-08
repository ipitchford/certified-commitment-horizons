# PDF visual and structural inspection

**File:** `paper/main.pdf`

**Inspection date:** 5 August 2026

**SHA-256:** `c567e179ab4fea728c20b536770004ef823121b13ceff9517110be18a2cff2f9`

**Method:** rendered all 23 A4 pages at 150 dpi with the repository PDF renderer; inspected six contact sheets covering every page; checked the title page, contribution table, theorem pages, every figure, the illustrative-case table, the scope table, appendices and references at page scale.

## Result

- No clipped text, overlapping objects, black squares or broken glyphs observed.
- Tables remain inside the text block; the contribution-boundary and audit tables are dense but legible at normal page zoom.
- All five figures render with labels and legends intact.
- Page numbering, running heads, contents and cross-references are coherent.
- The final reference page has intentional white space rather than a missing block.
- `pdfinfo` reports 23 A4 pages, unencrypted and text-based.
- `pdffonts` reports 21 embedded font subsets and no Type 3 fonts.
- `pdftotext` extracts the title and manuscript text without replacement characters.
- The final LaTeX log contains no overfull or underfull boxes, oversized floats, undefined references, undefined citations or forced float-placement warnings.

## Evidence files

- `quality/pdfinfo.txt`
- `quality/pdffonts.txt`
- `quality/preflight.txt`

Rendered page images and contact sheets were inspection intermediates and are excluded from the release archive.
