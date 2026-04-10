#!/usr/bin/env python
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from contextlib import ExitStack
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

import requests
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field
from pypdf import PdfReader

DEFAULT_MODEL = os.getenv("METANOTE_OPENAI_MODEL", "gpt-4o")
DEFAULT_MAX_LOCAL_REFS = 5
PDF_EXTENSIONS = {".pdf"}
REFERENCE_EXTENSIONS = {".pdf", ".md", ".tex", ".txt"}
STOP_WORDS = {
    "a",
    "an",
    "and",
    "for",
    "from",
    "in",
    "is",
    "lecture",
    "note",
    "notes",
    "of",
    "on",
    "the",
    "theorem",
    "to",
    "with",
}
TAG_ALIASES = {
    "chapter": "chapter",
    "lecture": "lecture",
    "sec": "sec",
    "section": "sec",
    "subsec": "subsec",
    "subsection": "subsec",
    "def": "def",
    "definition": "def",
    "thm": "thm",
    "theorem": "thm",
    "lemma": "lemma",
    "lem": "lemma",
    "prop": "prop",
    "proposition": "prop",
    "cor": "cor",
    "corollary": "cor",
    "pf": "pf",
    "proof": "pf",
    "rmk": "rmk",
    "remark": "rmk",
    "ex": "ex",
    "example": "ex",
    "topic": "topic",
}
ENV_BY_TAG = {
    "def": "definition",
    "thm": "theorem",
    "lemma": "lemma",
    "prop": "proposition",
    "cor": "corollary",
    "rmk": "remark",
    "ex": "example",
    "topic": "topic",
}


@dataclass
class MetaBlock:
    tag: str
    text: str
    order: int


@dataclass
class StyleProfile:
    sectioning_command: str
    lecture_heading_command: str
    lecture_heading_prefix: str
    available_envs: list[str]
    macros: list[str]
    sample_lines: list[str]
    summary: str


@dataclass
class PDFFacts:
    page_count: int
    extracted_characters: int
    sample_excerpt: str


class GeneratedSource(BaseModel):
    kind: Literal["web", "local", "target_style", "source_pdf", "mathpix"]
    title: str
    locator: str = ""
    note: str = ""


class GeneratedConflict(BaseModel):
    tag: str
    metanote_text: str
    reason: str
    page_numbers: list[int] = Field(default_factory=list)
    resolution_hint: str = ""
    severity: Literal["blocking", "warning"] = "blocking"


class GenerationResult(BaseModel):
    lecture_title: str
    latex_body: str
    run_summary: str
    should_write: bool
    confidence_notes: str = ""
    conflicts: list[GeneratedConflict] = Field(default_factory=list)
    sources: list[GeneratedSource] = Field(default_factory=list)
    mathpix_page_candidates: list[int] = Field(default_factory=list)


def eprint(message: str) -> None:
    print(message, file=sys.stderr)


def normalize_tag(raw: str) -> str:
    return TAG_ALIASES.get(raw.strip().lower(), raw.strip().lower())


def discover_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    return start


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return slug or "run"


def read_utf8(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_utf8(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def parse_metanote(text: str) -> list[MetaBlock]:
    pattern = re.compile(r"\[(?P<tag>[A-Za-z0-9_-]+)\]\s*[:：]\s*", re.MULTILINE)
    matches = list(pattern.finditer(text))
    if not matches:
        raise ValueError("No metanote tags found. Expected entries like [thm]: ...")
    blocks: list[MetaBlock] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if body:
            blocks.append(MetaBlock(tag=normalize_tag(match.group("tag")), text=body, order=index + 1))
    if not blocks:
        raise ValueError("Parsed metanote was empty after removing blank blocks.")
    return blocks


def resolve_title(provided_title: str | None, blocks: list[MetaBlock], pdf_path: Path) -> str:
    if provided_title:
        return provided_title.strip()
    for block in blocks:
        if block.tag in {"lecture", "chapter"}:
            return block.text.splitlines()[0].strip()
    return pdf_path.stem


def guess_course_root(target_tex_path: Path) -> Path:
    for candidate in [target_tex_path.parent, *target_tex_path.parents]:
        if (candidate / "reference").is_dir():
            return candidate
        if candidate.name.lower() in {"notes", "note"}:
            return candidate.parent
    return target_tex_path.parent


def tokenize(text: str) -> set[str]:
    return {token for token in re.findall(r"[A-Za-z0-9]+", text.lower()) if token not in STOP_WORDS}


def score_reference(path: Path, query_tokens: set[str]) -> tuple[int, int]:
    path_tokens = tokenize(path.stem + " " + " ".join(path.parts[-3:]))
    overlap = len(path_tokens & query_tokens)
    tie_breaker = 1 if "reference" in {part.lower() for part in path.parts} else 0
    return overlap, tie_breaker


def select_reference_files(
    course_root: Path,
    target_tex_path: Path,
    pdf_path: Path,
    title: str,
    blocks: list[MetaBlock],
    max_files: int,
) -> list[Path]:
    query_tokens = tokenize(title)
    for block in blocks[:8]:
        query_tokens.update(tokenize(block.text))
    candidates: dict[Path, tuple[int, int]] = {}
    search_dirs = [course_root / "reference", course_root]
    for folder in search_dirs:
        if not folder.exists():
            continue
        for path in folder.iterdir():
            if not path.is_file():
                continue
            if path.suffix.lower() not in REFERENCE_EXTENSIONS:
                continue
            if path.resolve() in {target_tex_path.resolve(), pdf_path.resolve()}:
                continue
            score = score_reference(path, query_tokens)
            if score[0] > 0 or "reference" in {part.lower() for part in path.parts}:
                candidates[path] = max(candidates.get(path, (0, 0)), score)
    ranked = sorted(candidates.items(), key=lambda item: (item[1][0], item[1][1], item[0].name.lower()), reverse=True)
    return [path for path, _ in ranked[:max_files]]


def extract_style_profile(target_tex_path: Path) -> StyleProfile:
    text = read_utf8(target_tex_path)
    envs = sorted(set(re.findall(r"\\begin\{([A-Za-z*]+)\}", text)))
    macros = re.findall(r"\\newcommand\{\\([^}]+)\}", text)
    sectioning_command = "subsection"
    if r"\chapter{" in text:
        sectioning_command = "chapter"
    elif r"\section{" in text:
        sectioning_command = "section"
    lecture_heading_prefix = ""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(r"\chapter{Lecture"):
            lecture_heading_prefix = "Lecture"
            break
        if stripped.startswith(r"\section{Lecture"):
            lecture_heading_prefix = "Lecture"
            sectioning_command = "section"
            break
    sample_lines: list[str] = []
    for raw_line in text.splitlines():
        stripped = raw_line.rstrip()
        if stripped.strip().startswith((r"\chapter{", r"\section{", r"\subsection{", r"\begin{theorem}", r"\begin{definition}", r"\begin{proof}")):
            sample_lines.append(stripped)
        if len(sample_lines) >= 10:
            break
    summary = (
        f"Target TeX uses {sectioning_command} headings, lecture prefix "
        f"{lecture_heading_prefix or 'none'}, environments {', '.join(envs[:12]) or 'none'}, "
        f"and macros {', '.join(macros[:12]) or 'none'}."
    )
    return StyleProfile(
        sectioning_command=sectioning_command,
        lecture_heading_command=sectioning_command,
        lecture_heading_prefix=lecture_heading_prefix,
        available_envs=envs,
        macros=macros,
        sample_lines=sample_lines,
        summary=summary,
    )


def extract_pdf_facts(pdf_path: Path) -> PDFFacts:
    reader = PdfReader(str(pdf_path))
    snippets: list[str] = []
    total_characters = 0
    for page in reader.pages[: min(len(reader.pages), 8)]:
        text = (page.extract_text() or "").strip()
        total_characters += len(text)
        if text:
            snippets.append(re.sub(r"\s+", " ", text)[:700])
    excerpt = "\n\n".join(snippets[:4])[:2400]
    return PDFFacts(page_count=len(reader.pages), extracted_characters=total_characters, sample_excerpt=excerpt)


def format_metanote_blocks(blocks: list[MetaBlock]) -> str:
    payload = [{"order": block.order, "tag": block.tag, "text": block.text} for block in blocks]
    return json.dumps(payload, ensure_ascii=False, indent=2)


def dedupe_marker(run_id: str) -> str:
    return f"METANOTE-AUTO-RUN-ID: {run_id}"


def has_existing_run(target_tex_path: Path, run_id: str) -> bool:
    return dedupe_marker(run_id) in read_utf8(target_tex_path)


def sanitize_latex_body(latex_body: str) -> str:
    body = latex_body.strip()
    body = re.sub(r"^```(?:latex)?\s*", "", body)
    body = re.sub(r"\s*```$", "", body)
    for token in (r"\documentclass", r"\begin{document}", r"\end{document}"):
        body = body.replace(token, f"% stripped: {token}")
    return body.strip()


def build_insertion_block(
    run_id: str,
    lecture_title: str,
    latex_body: str,
    metanote_path: Path,
    pdf_path: Path,
    *,
    style_profile: StyleProfile | None = None,
    omit_heading: bool = False,
) -> str:
    sanitized = sanitize_latex_body(latex_body)
    if omit_heading and style_profile is not None:
        rendered_heading = render_heading(style_profile, lecture_title)
        if sanitized.startswith(rendered_heading):
            sanitized = sanitized[len(rendered_heading) :].lstrip()
    return (
        f"% >>> METANOTE-AUTO-START\n"
        f"% {dedupe_marker(run_id)}\n"
        f"% METANOTE-SOURCE-PDF: {pdf_path.name}\n"
        f"% METANOTE-SOURCE-TXT: {metanote_path.name}\n"
        f"% METANOTE-LECTURE-TITLE: {lecture_title}\n\n"
        f"{sanitized.rstrip()}\n\n"
        f"% <<< METANOTE-AUTO-END\n"
    )


def resolved_heading_text(style_profile: StyleProfile, title: str) -> str:
    if style_profile.lecture_heading_prefix and not title.startswith(style_profile.lecture_heading_prefix):
        return f"{style_profile.lecture_heading_prefix}: {title}"
    return title


def find_existing_heading_match(target_text: str, style_profile: StyleProfile, title: str) -> re.Match[str] | None:
    command = style_profile.lecture_heading_command or "chapter"
    heading = resolved_heading_text(style_profile, title)
    pattern = re.compile(rf"^[ \t]*\\{command}\{{{re.escape(heading)}\}}[ \t]*\r?\n?", re.MULTILINE)
    return pattern.search(target_text)


def has_existing_heading(target_tex_path: Path, style_profile: StyleProfile, title: str) -> bool:
    return find_existing_heading_match(read_utf8(target_tex_path), style_profile, title) is not None


def insert_before_end_document(target_text: str, block: str) -> str:
    marker = r"\end{document}"
    index = target_text.rfind(marker)
    if index == -1:
        raise ValueError("Target TeX does not contain \\end{document}.")
    prefix = target_text[:index].rstrip()
    suffix = target_text[index:]
    return prefix + "\n\n" + block.rstrip() + "\n\n" + suffix


def find_existing_heading_slot(target_text: str, style_profile: StyleProfile, title: str) -> tuple[re.Match[str] | None, int | None]:
    match = find_existing_heading_match(target_text, style_profile, title)
    if not match:
        return None, None
    command = style_profile.lecture_heading_command or "chapter"
    if command == "chapter":
        next_heading_pattern = re.compile(r"^[ \t]*\\chapter\{[^}]+\}[ \t]*\r?\n?", re.MULTILINE)
    elif style_profile.lecture_heading_prefix:
        next_heading_pattern = re.compile(
            rf"^[ \t]*\\{command}\{{{re.escape(style_profile.lecture_heading_prefix)}[^}}]*\}}[ \t]*\r?\n?",
            re.MULTILINE,
        )
    else:
        return match, None
    next_match = next_heading_pattern.search(target_text, match.end())
    end_index = next_match.start() if next_match else target_text.rfind(r"\end{document}")
    if end_index == -1:
        raise ValueError("Target TeX does not contain \\end{document}.")
    between = target_text[match.end() : end_index]
    if between.strip():
        return match, None
    return match, match.end()


def insert_at_heading_slot(target_text: str, block: str, insertion_index: int) -> str:
    prefix = target_text[:insertion_index].rstrip()
    suffix = target_text[insertion_index:].lstrip("\r\n")
    if suffix:
        return prefix + "\n\n" + block.rstrip() + "\n\n" + suffix
    return prefix + "\n\n" + block.rstrip() + "\n"


def insert_lecture_block(target_text: str, block: str, style_profile: StyleProfile, title: str) -> str:
    _, insertion_index = find_existing_heading_slot(target_text, style_profile, title)
    if insertion_index is not None:
        return insert_at_heading_slot(target_text, block, insertion_index)
    return insert_before_end_document(target_text, block)


def write_sources_log(path: Path, title: str, sources: list[GeneratedSource], summary: str) -> None:
    lines = [f"# Sources for {title}", "", summary.strip(), ""]
    if not sources:
        lines.append("No external sources were recorded.")
    else:
        for source in sources:
            lines.append(f"- [{source.kind}] {source.title}")
            if source.locator:
                lines.append(f"  locator: {source.locator}")
            if source.note:
                lines.append(f"  note: {source.note}")
    write_utf8(path, "\n".join(lines).rstrip() + "\n")


def write_conflict_log(path: Path, title: str, conflicts: list[GeneratedConflict], summary: str) -> None:
    lines = [f"# Conflict report for {title}", "", summary.strip(), ""]
    if not conflicts:
        lines.append("No conflicts.")
    else:
        for index, conflict in enumerate(conflicts, start=1):
            lines.append(f"## Conflict {index}")
            lines.append(f"- tag: {conflict.tag}")
            lines.append(f"- metanote: {conflict.metanote_text}")
            if conflict.page_numbers:
                lines.append(f"- pages: {', '.join(str(page) for page in conflict.page_numbers)}")
            lines.append(f"- reason: {conflict.reason}")
            if conflict.resolution_hint:
                lines.append(f"- hint: {conflict.resolution_hint}")
            lines.append("")
    write_utf8(path, "\n".join(lines).rstrip() + "\n")


def load_client(api_key: str | None, base_url: str | None) -> OpenAI:
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required unless --backend mock is used.")
    kwargs: dict[str, str] = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    return OpenAI(**kwargs)


def load_mpx_env() -> None:
    mpx_config = Path.home() / ".mpx" / "config"
    if mpx_config.exists():
        load_dotenv(dotenv_path=mpx_config, override=False)


def has_openai_credentials() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def has_mpx_credentials() -> bool:
    return bool(
        os.getenv("MATHPIX_SNIP_AUTH_TOKEN")
        or os.getenv("MATHPIX_OCR_API_KEY")
        or (os.getenv("MATHPIX_APP_ID") and os.getenv("MATHPIX_APP_KEY"))
    )


def is_mpx_cli_available() -> bool:
    wrapper = discover_repo_root(Path(__file__).resolve().parent) / "tools" / "mpx_cli_wrapper.js"
    return wrapper.exists() and bool(shutil.which("node")) and has_mpx_credentials()


def run_mpx_convert(source: Path, destination: Path) -> tuple[bool, str]:
    wrapper = discover_repo_root(Path(__file__).resolve().parent) / "tools" / "mpx_cli_wrapper.js"
    node = shutil.which("node")
    if not node:
        return False, "node was not found on PATH."
    command = [node, str(wrapper), "convert", str(source), str(destination)]
    completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800)
    output = (completed.stdout or "") + "\n" + (completed.stderr or "")
    return completed.returncode == 0, output.strip()


def normalize_block_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_sentence(text: str) -> str:
    cleaned = normalize_block_text(text)
    if not cleaned:
        return ""
    if cleaned[-1] not in ".!?。！？:$}]":
        cleaned += "."
    return cleaned


EDITORIAL_LINE_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"\bsource pdf\b",
        r"\bocr\b",
        r"\bplease verify\b",
        r"\bplease restore\b",
        r"\bworkflow\b",
        r"\bmetanote\b",
        r"\bthe source then\b",
        r"\bthe source appears to\b",
        r"\bthe handwritten note\b",
        r"\bhandwritten notes\b",
        r"\btranscript supports\b",
        r"\bexact statement\b",
        r"\bleft/right convention\b",
        r"\bplease restore the exact\b",
    ]
]


def is_editorial_line(text: str) -> bool:
    cleaned = normalize_block_text(text)
    if not cleaned:
        return False
    lowered = cleaned.lower()
    if any(pattern.search(cleaned) for pattern in EDITORIAL_LINE_PATTERNS):
        return True
    return any(
        marker in lowered
        for marker in [
            "请复核",
            "请补充",
            "源笔记",
            "草稿",
            "待核",
            "恢复 exact",
            "恢复原笔记",
        ]
    )


def strip_editorial_lines(text: str) -> str:
    kept_lines: list[str] = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if stripped and is_editorial_line(stripped):
            continue
        kept_lines.append(raw_line.rstrip())
    cleaned = "\n".join(kept_lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned


def translate_common_hint_phrases(text: str) -> str:
    replacements = {
        "用归纳法": "Use induction",
        "归纳法": "Use induction",
        "短正合列分裂": "show that the relevant short exact sequence splits",
        "短正合列": "use the short exact sequence under consideration",
        "极大子模": "maximal submodules",
        "根基": "the radical",
        "本质满射": "an essential epimorphism",
        "直和分解": "a direct sum decomposition",
        "商模": "the quotient module",
        "由定义": "By definition",
        "容易验证": "It is straightforward to verify",
    }
    translated = text
    for source, target in replacements.items():
        translated = translated.replace(source, target)
    return normalize_sentence(translated)


def load_local_reference_text(reference_files: list[Path]) -> tuple[str, list[Path]]:
    text_chunks: list[str] = []
    text_paths: list[Path] = []
    for path in reference_files:
        if path.suffix.lower() not in {".mmd", ".md", ".txt"}:
            continue
        try:
            text = read_utf8(path).strip()
        except Exception:
            continue
        if not text:
            continue
        cleaned = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
        if not cleaned:
            continue
        text_paths.append(path)
        text_chunks.append(f"[{path.name}]\n{cleaned}")
    return "\n\n".join(text_chunks), text_paths


class OpenAIBackend:
    def __init__(
        self,
        client: OpenAI,
        model: str,
        enable_web: bool,
        use_mathpix: bool,
        mathpix_app_id: str | None,
        mathpix_app_key: str | None,
    ) -> None:
        self.client = client
        self.model = model
        self.enable_web = enable_web
        self.use_mathpix = use_mathpix
        self.mathpix_app_id = mathpix_app_id
        self.mathpix_app_key = mathpix_app_key

    def generate(
        self,
        *,
        pdf_path: Path,
        metanote_text: str,
        blocks: list[MetaBlock],
        style_profile: StyleProfile,
        title: str,
        reference_files: list[Path],
        run_dir: Path,
    ) -> GenerationResult:
        first_pass = self._generate_once(
            pdf_path=pdf_path,
            metanote_text=metanote_text,
            blocks=blocks,
            style_profile=style_profile,
            title=title,
            reference_files=reference_files,
            supplemental_ocr=None,
        )
        if not self.use_mathpix or not first_pass.conflicts or not first_pass.mathpix_page_candidates:
            return first_pass
        if not (self.mathpix_app_id and self.mathpix_app_key):
            return first_pass
        pages = sorted({page for page in first_pass.mathpix_page_candidates if page >= 1})[:4]
        if not pages:
            return first_pass
        ocr_payload = self._run_mathpix(pdf_path, pages, run_dir)
        if not ocr_payload.strip():
            return first_pass
        return self._generate_once(
            pdf_path=pdf_path,
            metanote_text=metanote_text,
            blocks=blocks,
            style_profile=style_profile,
            title=title,
            reference_files=reference_files,
            supplemental_ocr=ocr_payload,
        )

    def _generate_once(
        self,
        *,
        pdf_path: Path,
        metanote_text: str,
        blocks: list[MetaBlock],
        style_profile: StyleProfile,
        title: str,
        reference_files: list[Path],
        supplemental_ocr: str | None,
    ) -> GenerationResult:
        tools: list[dict[str, object]] = []
        remote_files: list[str] = []
        vector_store_id: str | None = None
        try:
            if reference_files:
                vector_store_id = self._create_vector_store(reference_files)
                tools.append(
                    {
                        "type": "file_search",
                        "vector_store_ids": [vector_store_id],
                        "max_num_results": min(8, len(reference_files) + 2),
                    }
                )
            if self.enable_web:
                tools.append({"type": "web_search_preview", "search_context_size": "medium"})

            with pdf_path.open("rb") as handle:
                source_pdf = self.client.files.create(file=handle, purpose="user_data")
            remote_files.append(source_pdf.id)

            pdf_facts = extract_pdf_facts(pdf_path)
            response = self.client.responses.parse(
                model=self.model,
                instructions=self._system_prompt(style_profile),
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": self._user_prompt(
                                    title=title,
                                    metanote_text=metanote_text,
                                    blocks=blocks,
                                    style_profile=style_profile,
                                    pdf_facts=pdf_facts,
                                    reference_files=reference_files,
                                    supplemental_ocr=supplemental_ocr,
                                ),
                            },
                            {"type": "input_file", "file_id": source_pdf.id},
                        ],
                    }
                ],
                tools=tools or None,
                text_format=GenerationResult,
                temperature=0.1,
                max_output_tokens=6000,
                verbosity="medium",
            )
            parsed = response.output_parsed
            if not parsed:
                raise RuntimeError("Model response did not contain parsed output.")
            return parsed
        finally:
            for file_id in remote_files:
                try:
                    self.client.files.delete(file_id)
                except Exception:
                    pass
            if vector_store_id:
                try:
                    self.client.vector_stores.delete(vector_store_id)
                except Exception:
                    pass

    def _system_prompt(self, style_profile: StyleProfile) -> str:
        return (
            "You are converting handwritten graduate-level mathematics lecture notes into compile-safe LaTeX. "
            "Use the metanote as the lecture skeleton. Use the source PDF as the primary evidence. "
            "Use target style and local references before web results. "
            "If the metanote, source PDF, and supporting sources materially disagree, do not smooth over the difference. "
            "Return blocking conflicts, leave should_write false, and keep latex_body empty or partial. "
            "Write body-only LaTeX: no preamble, no \\documentclass, no \\begin{document}, no \\end{document}. "
            f"Stay consistent with the target file style summary: {style_profile.summary} "
            "Only use theorem-like environments that exist in the target style. "
            "Keep mathematical claims conservative and textbook-safe. "
            "Do not copy editorial metanote notes into latex_body: omit workflow notes, source-tracking text, OCR comments, "
            "verification reminders, and Chinese annotations that are only for the editor. "
            "If you use web search, cite precise URLs in the sources array. "
            "The final LaTeX should be ready to append before \\end{document}."
        )

    def _user_prompt(
        self,
        *,
        title: str,
        metanote_text: str,
        blocks: list[MetaBlock],
        style_profile: StyleProfile,
        pdf_facts: PDFFacts,
        reference_files: list[Path],
        supplemental_ocr: str | None,
    ) -> str:
        refs = "\n".join(f"- {path.name}" for path in reference_files) or "- none"
        samples = "\n".join(f"- {line}" for line in style_profile.sample_lines) or "- none"
        parts = [
            f"Resolved lecture title: {title}",
            "",
            "Metanote, verbatim:",
            metanote_text.strip(),
            "",
            "Parsed metanote blocks:",
            format_metanote_blocks(blocks),
            "",
            "Target style sample lines:",
            samples,
            "",
            f"PDF facts: {pdf_facts.page_count} pages, extracted text characters={pdf_facts.extracted_characters}.",
            "Sample extracted text from the PDF (may be sparse if the PDF is image-only):",
            pdf_facts.sample_excerpt or "[no machine-readable text extracted locally]",
            "",
            "Local references available through file search:",
            refs,
            "",
            "Required behavior:",
            "1. Produce a top-level lecture heading consistent with the target style.",
            "2. Expand the metanote into polished lecture-note LaTeX.",
            "3. Use proof hints from [pf] blocks and standard results only when safely justified.",
            "4. Keep notation consistent with the target file.",
            "5. If evidence is insufficient or contradictory, emit blocking conflicts.",
            "6. Populate sources with enough detail for a sidecar log.",
            "7. Suggest Mathpix candidate pages only when the PDF looks ambiguous and page-level OCR would help.",
        ]
        if supplemental_ocr:
            parts.extend(["", "Supplemental OCR from Mathpix for ambiguous pages:", supplemental_ocr])
        return "\n".join(parts)

    def _create_vector_store(self, files: list[Path]) -> str:
        vector_store = self.client.vector_stores.create(
            name=f"metanote-to-tex-{int(time.time())}",
            expires_after={"anchor": "last_active_at", "days": 1},
        )
        with ExitStack() as stack:
            handles = [stack.enter_context(path.open("rb")) for path in files]
            self.client.vector_stores.file_batches.upload_and_poll(vector_store.id, files=handles)
        return vector_store.id

    def _run_mathpix(self, pdf_path: Path, page_numbers: list[int], run_dir: Path) -> str:
        snippets: list[str] = []
        render_dir = run_dir / "mathpix_pages"
        render_dir.mkdir(parents=True, exist_ok=True)
        for page in page_numbers:
            png_path = render_pdf_page(pdf_path, page, render_dir)
            if not png_path:
                continue
            response = requests.post(
                "https://api.mathpix.com/v3/text",
                headers={
                    "app_id": self.mathpix_app_id or "",
                    "app_key": self.mathpix_app_key or "",
                    "Content-Type": "application/json",
                },
                json=encode_mathpix_request(png_path),
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()
            text = (data.get("text") or data.get("latex_styled") or "").strip()
            if text:
                snippets.append(f"Page {page}\n{text}")
        return "\n\n".join(snippets)


class LocalFallbackBackend:
    def generate(
        self,
        *,
        pdf_path: Path,
        metanote_text: str,
        blocks: list[MetaBlock],
        style_profile: StyleProfile,
        title: str,
        reference_files: list[Path],
        run_dir: Path,
    ) -> GenerationResult:
        ocr_text, text_reference_paths = load_local_reference_text(reference_files)
        lines = [render_heading(style_profile, title), ""]
        has_section = False
        inserted_default_section = False
        previous_statement = ""
        for block in blocks:
            if block.tag in {"lecture", "chapter"}:
                continue
            if block.tag == "topic":
                continue
            if block.tag == "sec":
                has_section = True
                lines.extend([rf"\section{{{normalize_block_text(block.text)}}}", ""])
                continue
            if block.tag == "subsec":
                has_section = True
                lines.extend([rf"\subsection{{{normalize_block_text(block.text)}}}", ""])
                continue
            if not has_section and not inserted_default_section:
                lines.extend([r"\section{Main Results}", ""])
                inserted_default_section = True
                has_section = True
            if block.tag == "pf":
                lines.extend(self._render_proof(block.text, previous_statement, bool(ocr_text)))
                continue
            env = ENV_BY_TAG.get(block.tag)
            normalized_text = normalize_block_text(strip_editorial_lines(block.text))
            if not normalized_text:
                continue
            if env:
                lines.extend([rf"\begin{{{env}}}", normalized_text, rf"\end{{{env}}}", ""])
                if block.tag in {"thm", "lemma", "prop", "cor"}:
                    previous_statement = normalized_text
            else:
                lines.extend([f"% [metanote:{block.tag}] {normalized_text}", ""])

        sources = [
            GeneratedSource(
                kind="source_pdf",
                title=pdf_path.name,
                locator=str(pdf_path),
                note="Local fallback used the handwritten PDF as the primary lecture source.",
            )
        ]
        for path in text_reference_paths:
            kind = "mathpix" if path.name.endswith(".mpx.mmd") else "local"
            note = "mpx-cli OCR transcript used by the local fallback backend." if kind == "mathpix" else "Local text reference used by the local fallback backend."
            sources.append(
                GeneratedSource(
                    kind=kind,
                    title=path.name,
                    locator=str(path),
                    note=note,
                )
            )
        target_style_path = next((path for path in reference_files if path.suffix.lower() == ".tex"), None)
        if target_style_path:
            sources.append(
                GeneratedSource(
                    kind="target_style",
                    title=target_style_path.name,
                    locator=str(target_style_path),
                    note="Target TeX style guided the local fallback output.",
                )
            )

        summary_parts = ["Local fallback backend generated LaTeX from the metanote"]
        if any(path.name.endswith(".mpx.mmd") for path in text_reference_paths):
            summary_parts.append("with mpx-cli OCR support")
        if len(text_reference_paths) > 1:
            summary_parts.append(f"and {len(text_reference_paths) - 1} additional local text reference(s)")
        return GenerationResult(
            lecture_title=title,
            latex_body="\n".join(lines).strip() + "\n",
            run_summary=" ".join(summary_parts).strip() + ".",
            should_write=True,
            confidence_notes=(
                "Local fallback is deterministic and conservative. It relies on the metanote plus local OCR/reference files, "
                "so proofs may remain outline-level when no richer machine assistance is available."
            ),
            conflicts=[],
            sources=sources,
            mathpix_page_candidates=[],
        )

    @staticmethod
    def _render_proof(hint: str, previous_statement: str, has_ocr_support: bool) -> list[str]:
        cleaned_hint = strip_editorial_lines(hint)
        translated_hint = translate_common_hint_phrases(cleaned_hint) if cleaned_hint else ""
        if not translated_hint:
            return []
        return [r"\begin{proof}", translated_hint, r"\end{proof}", ""]


class MockBackend:
    def generate(
        self,
        *,
        pdf_path: Path,
        metanote_text: str,
        blocks: list[MetaBlock],
        style_profile: StyleProfile,
        title: str,
        reference_files: list[Path],
        run_dir: Path,
    ) -> GenerationResult:
        lines = [self._heading(style_profile, title), ""]
        for block in blocks:
            if block.tag in {"lecture", "chapter"}:
                continue
            if block.tag == "sec":
                lines.extend([rf"\section{{{block.text}}}", ""])
                continue
            if block.tag == "subsec":
                lines.extend([rf"\subsection{{{block.text}}}", ""])
                continue
            if block.tag == "pf":
                lines.extend([r"\begin{proof}", f"Metanote proof hint: {block.text}", r"\end{proof}", ""])
                continue
            env = ENV_BY_TAG.get(block.tag)
            if env:
                lines.extend([rf"\begin{{{env}}}", block.text, rf"\end{{{env}}}", ""])
            else:
                lines.extend([f"% [metanote:{block.tag}] {block.text}", ""])
        return GenerationResult(
            lecture_title=title,
            latex_body="\n".join(lines).strip() + "\n",
            run_summary=f"Mock backend generated LaTeX from {len(blocks)} metanote blocks.",
            should_write=True,
            confidence_notes="Mock backend does not inspect the PDF.",
            conflicts=[],
            sources=[
                GeneratedSource(
                    kind="source_pdf",
                    title=pdf_path.name,
                    locator=str(pdf_path),
                    note="Mock backend used the supplied PDF path only for existence checks.",
                )
            ],
            mathpix_page_candidates=[],
        )

    @staticmethod
    def _heading(style_profile: StyleProfile, title: str) -> str:
        return render_heading(style_profile, title)


def render_pdf_page(pdf_path: Path, page_number: int, output_dir: Path) -> Path | None:
    pdftoppm = shutil.which("pdftoppm")
    if not pdftoppm:
        return None
    prefix = output_dir / f"page-{page_number}"
    command = [
        pdftoppm,
        "-png",
        "-singlefile",
        "-f",
        str(page_number),
        "-l",
        str(page_number),
        str(pdf_path),
        str(prefix),
    ]
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode != 0:
        return None
    png_path = prefix.with_suffix(".png")
    return png_path if png_path.exists() else None


def encode_mathpix_request(image_path: Path) -> dict[str, object]:
    import base64

    data = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return {"src": f"data:image/png;base64,{data}", "formats": ["text", "latex_styled"]}


def render_heading(style_profile: StyleProfile, title: str) -> str:
    command = style_profile.lecture_heading_command or "chapter"
    heading = resolved_heading_text(style_profile, title)
    return rf"\{command}{{{heading}}}"


def compile_candidate(candidate_text: str, target_tex_path: Path, run_dir: Path) -> tuple[bool, Path]:
    candidate_path = target_tex_path.with_name(f"{target_tex_path.stem}.__metanote_candidate__.tex")
    write_utf8(candidate_path, candidate_text)
    compile_log_path = run_dir / "compile.log"
    latexmk = shutil.which("latexmk")
    if not latexmk:
        compile_log_path.write_text("latexmk not found on PATH.\n", encoding="utf-8")
        candidate_path.unlink(missing_ok=True)
        return False, compile_log_path
    command = [
        latexmk,
        "-xelatex",
        "-interaction=nonstopmode",
        "-halt-on-error",
        f"-outdir={run_dir}",
        candidate_path.name,
    ]
    completed = subprocess.run(
        command,
        cwd=target_tex_path.parent,
        capture_output=True,
        text=True,
        timeout=600,
    )
    compile_log_path.write_text(completed.stdout + "\n" + completed.stderr, encoding="utf-8")
    candidate_path.unlink(missing_ok=True)
    return completed.returncode == 0, compile_log_path


def write_target_tex(target_tex_path: Path, insertion_block: str, style_profile: StyleProfile, title: str) -> None:
    updated = insert_lecture_block(read_utf8(target_tex_path), insertion_block, style_profile, title)
    write_utf8(target_tex_path, updated)


def choose_backend(args: argparse.Namespace) -> Literal["mock", "local", "openai"]:
    if args.backend == "mock":
        return "mock"
    if args.backend == "local":
        return "local"
    if has_openai_credentials():
        return "openai"
    return "local"


def build_run_id(pdf_path: Path, metanote_text: str, target_tex_path: Path, title: str) -> str:
    digest = hashlib.sha256()
    digest.update(sha256_file(pdf_path).encode("ascii"))
    digest.update(sha256_text(metanote_text).encode("ascii"))
    digest.update(str(target_tex_path.resolve()).encode("utf-8"))
    digest.update(title.encode("utf-8"))
    return digest.hexdigest()[:16]


def make_run_dir(repo_root: Path, title: str, run_id: str) -> Path:
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    run_dir = repo_root / "tmp" / "metanote_pipeline" / f"{timestamp}-{slugify(title)}-{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def load_inputs(pdf_path: Path, metanote_path: Path, target_tex_path: Path) -> tuple[str, list[MetaBlock], StyleProfile]:
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    if not metanote_path.exists():
        raise FileNotFoundError(f"Metanote file not found: {metanote_path}")
    if not target_tex_path.exists():
        raise FileNotFoundError(f"Target TeX not found: {target_tex_path}")
    if pdf_path.suffix.lower() not in PDF_EXTENSIONS:
        raise ValueError("Source PDF must be a .pdf file.")
    metanote_text = read_utf8(metanote_path)
    blocks = parse_metanote(metanote_text)
    style_profile = extract_style_profile(target_tex_path)
    return metanote_text, blocks, style_profile


def persist_manifest(run_dir: Path, manifest: dict[str, object]) -> None:
    write_utf8(run_dir / "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")


def run_pipeline(args: argparse.Namespace) -> int:
    load_dotenv()
    load_mpx_env()
    pdf_path = Path(args.pdf).resolve()
    metanote_path = Path(args.metanote).resolve()
    target_tex_path = Path(args.target_tex).resolve()
    repo_root = discover_repo_root(Path(__file__).resolve().parent)
    metanote_text, blocks, style_profile = load_inputs(pdf_path, metanote_path, target_tex_path)
    title = resolve_title(args.title, blocks, pdf_path)
    backend_name = choose_backend(args)
    auto_local_fallback = backend_name == "local" and args.backend is None and not has_openai_credentials()
    requested_use_mpx_cli = bool(getattr(args, "use_mpx_cli", False))
    auto_use_mpx_cli = backend_name == "local" and is_mpx_cli_available()
    effective_use_mpx_cli = requested_use_mpx_cli or auto_use_mpx_cli
    run_id = build_run_id(pdf_path, metanote_text, target_tex_path, title)
    if not args.force and has_existing_run(target_tex_path, run_id):
        eprint(f"Duplicate run detected in target TeX for run id {run_id}. Use --force to override.")
        return 2
    target_text = read_utf8(target_tex_path)
    heading_match, heading_slot = find_existing_heading_slot(target_text, style_profile, title)
    if not args.force and heading_match and heading_slot is None:
        eprint(
            f"Target TeX already has a non-empty lecture block for "
            f"'{resolved_heading_text(style_profile, title)}'. Use --force to append anyway."
        )
        return 2
    run_dir = make_run_dir(repo_root, title, run_id)
    course_root = guess_course_root(target_tex_path)
    reference_files = select_reference_files(
        course_root=course_root,
        target_tex_path=target_tex_path,
        pdf_path=pdf_path,
        title=title,
        blocks=blocks,
        max_files=args.max_local_refs,
    )
    manifest: dict[str, object] = {
        "run_id": run_id,
        "mode": args.command,
        "pdf": str(pdf_path),
        "metanote": str(metanote_path),
        "target_tex": str(target_tex_path),
        "title": title,
        "backend_requested": args.backend or "auto",
        "backend": backend_name,
        "auto_local_fallback": auto_local_fallback,
        "no_web": bool(args.no_web),
        "enable_mathpix": bool(args.enable_mathpix),
        "use_mpx_cli": effective_use_mpx_cli,
    }
    if auto_local_fallback:
        if effective_use_mpx_cli:
            eprint("OPENAI_API_KEY is missing; falling back to the local backend and attempting mpx-cli OCR first.")
        else:
            eprint("OPENAI_API_KEY is missing; falling back to the local backend without mpx-cli OCR because it is not available in this environment.")
    if effective_use_mpx_cli:
        mpx_output_path = run_dir / f"{slugify(title)}.mpx.mmd"
        mpx_log_path = run_dir / "mpx_convert.log"
        success, output = run_mpx_convert(pdf_path, mpx_output_path)
        write_utf8(mpx_log_path, (output.strip() + "\n") if output.strip() else "")
        manifest["mpx_cli"] = {
            "requested": requested_use_mpx_cli,
            "auto_enabled": auto_use_mpx_cli and not requested_use_mpx_cli,
            "success": success,
            "output_path": str(mpx_output_path),
            "log_path": str(mpx_log_path),
        }
        if not success:
            if backend_name == "local" and not requested_use_mpx_cli:
                manifest["mpx_cli"]["continued_without_ocr"] = True
                manifest["reference_files"] = [str(path) for path in reference_files]
                persist_manifest(run_dir, manifest)
                eprint(f"mpx-cli conversion failed during automatic local fallback. Continuing with metanote-only local generation. See {mpx_log_path}")
            else:
                manifest["reference_files"] = [str(path) for path in reference_files]
                persist_manifest(run_dir, manifest)
                eprint(f"mpx-cli conversion failed. See {mpx_log_path}")
                return 6
        elif not mpx_output_path.exists():
            manifest["reference_files"] = [str(path) for path in reference_files]
            persist_manifest(run_dir, manifest)
            eprint(f"mpx-cli reported success but produced no output file at {mpx_output_path}")
            return 6
        else:
            reference_files = [mpx_output_path, *reference_files]
    manifest["reference_files"] = [str(path) for path in reference_files]
    persist_manifest(run_dir, manifest)
    write_utf8(run_dir / "parsed_metanote.json", format_metanote_blocks(blocks) + "\n")
    write_utf8(run_dir / "style_profile.json", json.dumps(asdict(style_profile), ensure_ascii=False, indent=2) + "\n")
    if backend_name == "mock":
        backend = MockBackend()
    elif backend_name == "local":
        backend = LocalFallbackBackend()
    else:
        backend = OpenAIBackend(
            client=load_client(os.getenv("OPENAI_API_KEY"), os.getenv("OPENAI_BASE_URL")),
            model=args.model or DEFAULT_MODEL,
            enable_web=not args.no_web,
            use_mathpix=args.enable_mathpix,
            mathpix_app_id=os.getenv("MATHPIX_APP_ID"),
            mathpix_app_key=os.getenv("MATHPIX_APP_KEY"),
        )
    result = backend.generate(
        pdf_path=pdf_path,
        metanote_text=metanote_text,
        blocks=blocks,
        style_profile=style_profile,
        title=title,
        reference_files=[target_tex_path, *reference_files],
        run_dir=run_dir,
    )
    write_utf8(run_dir / "generation.json", json.dumps(result.model_dump(), ensure_ascii=False, indent=2) + "\n")
    if not result.should_write and not result.conflicts:
        result.conflicts = [
            GeneratedConflict(
                tag="pipeline",
                metanote_text=title,
                reason="The model declined to mark this lecture as safe to write.",
                resolution_hint="Inspect generation.json and rerun with a clarified metanote or --force after review.",
            )
        ]
    sources_log = target_tex_path.with_name(f"{target_tex_path.stem}.{run_id}.sources.md")
    conflicts_log = target_tex_path.with_name(f"{target_tex_path.stem}.{run_id}.conflicts.md")
    write_sources_log(sources_log, title, result.sources, result.run_summary)
    if result.conflicts:
        write_conflict_log(conflicts_log, title, result.conflicts, result.run_summary)
        eprint(f"Blocked by {len(result.conflicts)} conflict(s). See {conflicts_log}")
        return 3
    if not result.latex_body.strip():
        eprint("Generation returned no LaTeX body.")
        return 4
    insertion_block = build_insertion_block(
        run_id,
        result.lecture_title or title,
        result.latex_body,
        metanote_path,
        pdf_path,
        style_profile=style_profile,
        omit_heading=heading_slot is not None,
    )
    candidate_text = insert_lecture_block(target_text, insertion_block, style_profile, title)
    write_utf8(run_dir / "candidate_fragment.texfrag", sanitize_latex_body(result.latex_body) + "\n")
    compile_ok, compile_log_path = compile_candidate(candidate_text, target_tex_path, run_dir)
    manifest["compile_log"] = str(compile_log_path)
    persist_manifest(run_dir, manifest)
    if not compile_ok:
        eprint(f"Candidate compile failed. See {compile_log_path}")
        return 5
    if args.command == "dry-run":
        eprint(f"Dry-run succeeded. Candidate artifacts are in {run_dir}")
        return 0
    write_target_tex(target_tex_path, insertion_block, style_profile, title)
    eprint(f"Wrote lecture block into {target_tex_path}")
    return 0


def resume_conflict(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).resolve()
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    manifest = json.loads(read_utf8(manifest_path))
    no_web = args.no_web if args.no_web is not None else bool(manifest.get("no_web", False))
    enable_mathpix = args.enable_mathpix if args.enable_mathpix is not None else bool(manifest.get("enable_mathpix", False))
    use_mpx_cli = args.use_mpx_cli if args.use_mpx_cli is not None else bool(manifest.get("use_mpx_cli", False))
    namespace = argparse.Namespace(
        command="run",
        pdf=manifest["pdf"],
        metanote=args.metanote or manifest["metanote"],
        target_tex=manifest["target_tex"],
        title=args.title or manifest.get("title"),
        backend=args.backend or manifest.get("backend") or "openai",
        model=args.model,
        max_local_refs=args.max_local_refs,
        no_web=no_web,
        enable_mathpix=enable_mathpix,
        use_mpx_cli=use_mpx_cli,
        force=args.force,
    )
    return run_pipeline(namespace)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Turn a lecture PDF and a metanote txt file into appended LaTeX.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_common_arguments(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("--pdf", required=True, help="Path to the handwritten notes PDF.")
        subparser.add_argument("--metanote", required=True, help="Path to the metanote .txt file.")
        subparser.add_argument("--target-tex", required=True, help="Target .tex file to update.")
        subparser.add_argument("--title", help="Optional lecture title override.")
        subparser.add_argument("--backend", choices=["openai", "local", "mock"], help="Generation backend. Default: auto (OpenAI if configured, otherwise local fallback).")
        subparser.add_argument("--model", help=f"OpenAI model name. Default: {DEFAULT_MODEL}")
        subparser.add_argument("--max-local-refs", type=int, default=DEFAULT_MAX_LOCAL_REFS, help="Number of local reference files to expose.")
        subparser.add_argument("--no-web", action="store_true", help="Disable web search during generation.")
        subparser.add_argument("--enable-mathpix", action="store_true", help="Allow Mathpix OCR fallback for ambiguous pages.")
        subparser.add_argument("--use-mpx-cli", action="store_true", help="Pre-convert the PDF with mpx-cli and feed the resulting .mmd into generation.")
        subparser.add_argument("--force", action="store_true", help="Ignore duplicate run detection.")

    add_common_arguments(subparsers.add_parser("run", help="Generate, compile-check, and write into the target TeX."))
    add_common_arguments(subparsers.add_parser("dry-run", help="Generate and compile-check without writing the target TeX."))
    resume_parser = subparsers.add_parser("resume-conflict", help="Resume a failed conflict run with a revised metanote.")
    resume_parser.add_argument("--run-dir", required=True, help="Previous tmp/metanote_pipeline run directory.")
    resume_parser.add_argument("--metanote", help="Replacement metanote .txt file.")
    resume_parser.add_argument("--title", help="Optional lecture title override.")
    resume_parser.add_argument("--backend", choices=["openai", "local", "mock"], help="Generation backend override.")
    resume_parser.add_argument("--model", help=f"OpenAI model name. Default: {DEFAULT_MODEL}")
    resume_parser.add_argument("--max-local-refs", type=int, default=DEFAULT_MAX_LOCAL_REFS, help="Number of local reference files to expose.")
    resume_parser.add_argument("--no-web", action="store_true", default=None, help="Disable web search during generation.")
    resume_parser.add_argument("--enable-mathpix", action="store_true", default=None, help="Allow Mathpix OCR fallback for ambiguous pages.")
    resume_parser.add_argument("--use-mpx-cli", action="store_true", default=None, help="Pre-convert the PDF with mpx-cli and feed the resulting .mmd into generation.")
    resume_parser.add_argument("--force", action="store_true", help="Ignore duplicate run detection.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        if args.command == "resume-conflict":
            return resume_conflict(args)
        return run_pipeline(args)
    except Exception as exc:
        eprint(f"metanote_to_tex failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
