# Split LaTeX Template

This is a reusable split-file LaTeX template based on the course-note style in
the current workspace.

## Compile

Run from this directory:

```powershell
latexmk -xelatex -interaction=nonstopmode -halt-on-error main.tex
```

The output PDF is `main.pdf`.

## Structure

- `main.tex` is the only compile entry point.
- Add chapter files with `\include{chapterN}` in `main.tex`.
- Add section files with `\input{chapterN/NN-section-slug}` in each chapter file.
- Keep packages, colors, theorem declarations, macros, and title metadata in
  `main.tex`.

## Example

```tex
% main.tex
\include{chapter1}
\include{chapter2}

% chapter2.tex
\chapter{Second Chapter}
\input{chapter2/01-first-section}
```
