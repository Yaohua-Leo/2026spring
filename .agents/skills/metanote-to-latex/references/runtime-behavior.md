# Runtime Behavior

The workflow is implemented by `tools/metanote_to_tex.py`.

Subcommands:

- `run`: generate, compile-check, then write into the target `.tex`
- `dry-run`: generate and compile-check without writing
- `resume-conflict`: rerun a previous failed job with a revised metanote

Backend resolution:

- `--backend openai`: force the OpenAI backend
- `--backend local`: force the deterministic local fallback backend
- `--backend mock`: force the smoke-test backend
- no `--backend`: use OpenAI when `OPENAI_API_KEY` is present, otherwise degrade automatically to the local fallback backend

Artifacts:

- `tmp/metanote_pipeline/<timestamp>-<title>-<runid>/`
- `<target>.<runid>.sources.md`
- `<target>.<runid>.conflicts.md` when conflicts exist

Safety defaults:

- Duplicate runs are blocked unless `--force` is used.
- Writes only happen after a successful temporary compile.
- Conflict runs never write the target `.tex`.

Optional OCR assist:

- `--use-mpx-cli` runs the locally installed `mpx-cli` first and stores its `.mmd` output in the run directory.
- The generated `.mmd` is then added to the local reference set so the main generation pass can use it alongside the PDF, metanote, target `.tex`, and course references.
- If `mpx-cli` is requested but fails, the run stops before any write and records `mpx_convert.log` in the run directory.
- During automatic local fallback, the CLI also tries to enable `mpx-cli` on its own when the local environment already has usable `mpx-cli` credentials. If that automatic OCR attempt fails, the run continues with metanote-only local generation and records the failure in the manifest and `mpx_convert.log`.
