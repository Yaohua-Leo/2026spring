---
name: metanote-to-latex
description: Convert a handwritten lecture PDF plus a metanote text file into appended course-note LaTeX in a target .tex file. Use when the user provides or mentions a PDF/scan of handwritten math notes, a metanote .txt file, and a target .tex file to update, especially requests like "把这个 pdf 和 metanote 写进 Lie_Theory.tex", "append lecture notes from handwritten notes", or "run the metanote pipeline". The skill validates the three required inputs, runs the repo-local CLI in run or dry-run mode, and surfaces conflict reports when the source PDF, metanote, and references disagree.
---

# Metanote To LaTeX

Use this skill when the user wants the handwritten-notes workflow, not for generic OCR.

## Required inputs

- A lecture PDF or scan file
- A `metanote.txt` file
- A target `.tex` file

`--title` is optional. If omitted, the CLI uses `[lecture]: ...` from the metanote or falls back to the PDF stem.

## Default command

Run from repo root:

```powershell
python .agents/skills/metanote-to-latex/scripts/run_workflow.py run --pdf "<pdf>" --metanote "<metanote.txt>" --target-tex "<target.tex>"
```

The CLI now resolves the backend automatically:

- If `OPENAI_API_KEY` is present, it uses the OpenAI backend.
- If `OPENAI_API_KEY` is missing, it falls back to the local backend.
- During local fallback, it will automatically try `mpx-cli` first when `mpx-cli` is installed and already logged in.

If `mpx-cli` is installed and already logged in, add `--use-mpx-cli` to pre-convert the PDF into `.mmd` and feed that OCR result back into the generator:

```powershell
python .agents/skills/metanote-to-latex/scripts/run_workflow.py run --pdf "<pdf>" --metanote "<metanote.txt>" --target-tex "<target.tex>" --use-mpx-cli
```

Use `dry-run` when the user wants a preview or when you need a safe first pass:

```powershell
python .agents/skills/metanote-to-latex/scripts/run_workflow.py dry-run --pdf "<pdf>" --metanote "<metanote.txt>" --target-tex "<target.tex>"
```

## Behavior

- The CLI appends before `\end{document}`.
- It compile-checks a temporary candidate before any write.
- It writes a sidecar sources log next to the target `.tex`.
- If the metanote, source PDF, and supporting sources conflict, it does not write the target `.tex`; instead it writes a sidecar conflict report.
- If `OPENAI_API_KEY` is unavailable, it automatically degrades to the local fallback backend. That backend is deterministic, uses the metanote as the primary structure, and prefers `mpx-cli` OCR when available.

## Environment

- `OPENAI_API_KEY` is optional. When absent, the CLI falls back to the local backend.
- `OPENAI_BASE_URL` is optional.
- `MATHPIX_APP_ID` and `MATHPIX_APP_KEY` are optional and only used with `--enable-mathpix`.
- `mpx-cli` login state is reused automatically when `--use-mpx-cli` is enabled.

## References

- Metanote grammar and tag expectations: [references/metanote-format.md](references/metanote-format.md)
- Runtime behavior and artifacts: [references/runtime-behavior.md](references/runtime-behavior.md)
