# Metanote Format

The parser expects repeated tagged entries like:

```text
[lecture]: Lecture 7 Weyl's theorem
[sec]: Weyl's theorem
[thm]: Weyl theorem
[pf]: Use induction and split the short exact sequence.
[rmk]: Explain why one-dimensional modules are trivial.
```

Supported tags in v1:

- `[lecture]`, `[chapter]`
- `[sec]`, `[subsec]`
- `[def]`
- `[thm]`
- `[lemma]`
- `[prop]`
- `[cor]`
- `[pf]`
- `[rmk]`
- `[ex]`
- `[topic]`

Notes:

- `[pf]` attaches to the most recent theorem-like block conceptually; the model is told to interpret it that way.
- Multi-line bodies are allowed. The next `[tag]:` starts a new block.
- Unknown tags are preserved as comments by the mock backend and described to the model by the real backend.
