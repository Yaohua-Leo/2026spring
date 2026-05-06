# AGENTS.md

## Cursor Cloud specific instructions

### Overview

This is a **metanote-to-LaTeX pipeline** repository. The main tool is `tools/metanote_to_tex.py` — a CLI that converts handwritten lecture PDFs + structured "metanote" text files into compile-safe LaTeX course notes.

### Running tests

```bash
python3 -m unittest tests/test_metanote_to_tex.py -v
```

All tests (including compile-check smoke tests) require `latexmk` and `xelatex` on PATH.

### Running the pipeline

The pipeline has three backends: `openai` (requires `OPENAI_API_KEY`), `local` (deterministic fallback), and `mock` (for testing). Without `OPENAI_API_KEY`, the pipeline auto-falls back to the `local` backend.

```bash
# Dry-run with mock backend (no external API needed):
python3 tools/metanote_to_tex.py dry-run --backend mock \
  --pdf <source.pdf> --metanote <notes.txt> --target-tex <target.tex>

# Full run that writes into target TeX:
python3 tools/metanote_to_tex.py run --backend mock \
  --pdf <source.pdf> --metanote <notes.txt> --target-tex <target.tex>
```

### Key gotchas

- The pipeline **refuses to write** unless the candidate LaTeX compiles successfully with `latexmk -xelatex`. If TeX Live is missing or misconfigured, all tests that require compilation will be skipped.
- `template.tex` and `template.pdf` in the repo root are test fixtures used by the test suite. Do not delete them.
- Run artifacts are written to `tmp/metanote_pipeline/` — this directory is gitignored.
- The `texlive-science` package is required for `ytableau.sty` used in `template.tex`.

### System dependencies

Already installed in the VM environment via the update script:
- Python 3.12 with: `openai`, `pydantic`, `pypdf`, `requests`, `python-dotenv`
- TeX Live: `texlive-xetex`, `texlive-latex-extra`, `texlive-fonts-recommended`, `texlive-science`, `latexmk`
