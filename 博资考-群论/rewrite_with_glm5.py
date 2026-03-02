import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path


WEEK_RE = re.compile(r"^\s*(?:##\s*)?Week\s+\d+", re.IGNORECASE)
CODE_FENCE_RE = re.compile(r"^```(?:latex)?\s*|\s*```$", re.IGNORECASE | re.DOTALL)


def post_chat(base_url, api_key, payload, timeout=120):
    url = base_url.rstrip("/") + "/chat/completions"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        return resp.status, json.loads(body)


def normalize_model_output(text):
    text = text.strip()
    if text.startswith("```"):
        text = CODE_FENCE_RE.sub("", text).strip()
    return text


def split_by_weeks(lines):
    starts = []
    for i, line in enumerate(lines):
        if WEEK_RE.match(line):
            starts.append(i)
    if not starts or starts[0] != 0:
        starts = [0] + starts
    starts = sorted(set(starts))

    chunks = []
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(lines)
        chunk_lines = lines[start:end]
        if any(s.strip() for s in chunk_lines):
            chunks.append((start + 1, end, chunk_lines))
    return chunks


def split_large_chunk(chunk_lines, max_lines=90):
    if len(chunk_lines) <= max_lines:
        return [chunk_lines]
    out = []
    i = 0
    while i < len(chunk_lines):
        j = min(i + max_lines, len(chunk_lines))
        out.append(chunk_lines[i:j])
        i = j
    return out


def detect_title(chunk_lines, fallback):
    for line in chunk_lines[:8]:
        s = line.strip().lstrip("#").strip()
        if s:
            return s
    return fallback


def build_messages(chunk_text, title):
    system = (
        "You are cleaning noisy OCR/Markdown group theory lecture notes into valid LaTeX body text. "
        "Output only LaTeX content, no markdown fences, no explanations."
    )
    user = (
        "Task: Rewrite the following OCR notes into clean LaTeX for an existing report file.\n"
        "Rules:\n"
        "1) Do NOT output preamble, \\begin{document}, \\end{document}, \\chapter, or \\section.\n"
        "2) Use environments already defined in target file when suitable: theorem, lemma, proposition, corollary, definition, example, remark, exercise, topic.\n"
        "3) Prefer wrapping the chunk with \\begin{topic}[<title>] ... \\end{topic}.\n"
        "4) Keep and correct mathematics. Use $...$ and \\[...\\] consistently.\n"
        "5) Remove OCR garbage and duplicated fragments.\n"
        "6) If text is unreadable, keep a short placeholder comment like % [OCR unclear].\n"
        "7) Keep meaning conservative; do not invent results.\n\n"
        f"Suggested title: {title}\n\n"
        "Input chunk:\n"
        "-----\n"
        f"{chunk_text}\n"
        "-----\n"
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def call_clean_chunk(base_url, api_key, model, chunk_text, title, max_tokens=2400, retries=2):
    messages = build_messages(chunk_text, title)
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0,
        "enable_thinking": False,
        "max_tokens": max_tokens,
    }
    attempt = 0
    last_err = None
    while attempt <= retries:
        try:
            status, data = post_chat(base_url, api_key, payload)
            if status != 200:
                raise RuntimeError(f"HTTP {status}")
            choice = data["choices"][0]
            msg = choice.get("message", {})
            content = normalize_model_output(msg.get("content", ""))
            finish = choice.get("finish_reason")
            if content:
                return content, finish
            if finish == "length":
                payload["max_tokens"] = int(payload["max_tokens"] * 1.4)
            else:
                payload["enable_thinking"] = False
                payload["max_tokens"] = max(payload["max_tokens"], 2000)
        except (urllib.error.HTTPError, urllib.error.URLError, RuntimeError, KeyError, json.JSONDecodeError) as exc:
            last_err = exc
            time.sleep(1.2)
        attempt += 1
    raise RuntimeError(f"Chunk clean failed after retries: {last_err}")


def insert_at_line(tex_path, latex_block, line_no):
    tex_lines = tex_path.read_text(encoding="utf-8").splitlines()
    if line_no < 1 or line_no > len(tex_lines) + 1:
        raise ValueError(f"Invalid insertion line: {line_no}")

    try:
        end_doc_idx = next(i for i, line in enumerate(tex_lines) if line.strip() == r"\end{document}")
    except StopIteration:
        raise ValueError("Target .tex has no \\end{document}")

    insert_idx = line_no - 1
    if insert_idx > end_doc_idx:
        insert_idx = end_doc_idx

    # Rewrite mode: replace everything from insertion line up to \end{document}.
    new_lines = tex_lines[:insert_idx] + latex_block.splitlines() + [""] + tex_lines[end_doc_idx:]
    tex_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Rewrite noisy OCR markdown into LaTeX via GLM-5 and insert into target tex.")
    parser.add_argument("--md", required=True)
    parser.add_argument("--tex", required=True)
    parser.add_argument("--line", type=int, required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model", default="GLM-5")
    parser.add_argument("--out-frag", required=True)
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY")
    parser.add_argument("--max-lines", type=int, default=90)
    parser.add_argument("--max-tokens", type=int, default=2400)
    args = parser.parse_args()

    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        raise RuntimeError(f"Environment variable {args.api_key_env} is required")

    md_path = Path(args.md)
    tex_path = Path(args.tex)
    out_frag = Path(args.out_frag)

    lines = md_path.read_text(encoding="utf-8", errors="replace").splitlines()
    week_chunks = split_by_weeks(lines)
    if not week_chunks:
        week_chunks = [(1, len(lines), lines)]

    results = []
    total_calls = 0
    for cidx, (start, end, chunk_lines) in enumerate(week_chunks, start=1):
        title = detect_title(chunk_lines, f"Notes {cidx}")
        subchunks = split_large_chunk(chunk_lines, max_lines=args.max_lines)
        for sidx, sub in enumerate(subchunks, start=1):
            sub_title = title if len(subchunks) == 1 else f"{title} (part {sidx})"
            text = "\n".join(sub).strip()
            if not text:
                continue
            total_calls += 1
            print(f"[clean] chunk {cidx}.{sidx} lines {start}-{end}", flush=True)
            cleaned, finish = call_clean_chunk(
                args.base_url,
                api_key,
                args.model,
                text,
                sub_title,
                max_tokens=args.max_tokens,
            )
            if finish == "length":
                cleaned += "\n% [truncated by model: consider rerun with higher max_tokens]"
            results.append(cleaned.strip())

    final_block = "\n\n".join(x for x in results if x)
    out_frag.write_text(final_block + "\n", encoding="utf-8")
    insert_at_line(tex_path, final_block, args.line)

    print(
        json.dumps(
            {
                "chunks": len(week_chunks),
                "calls": total_calls,
                "fragment": str(out_frag),
                "target": str(tex_path),
                "insert_line": args.line,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
