from __future__ import annotations

import argparse
import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "tools" / "metanote_to_tex.py"
TEMPLATE_TEX = REPO_ROOT / "template.tex"
TEMPLATE_PDF = REPO_ROOT / "template.pdf"


def load_module():
    spec = importlib.util.spec_from_file_location("metanote_to_tex_test_module", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load metanote_to_tex module for tests.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class MetanoteToTexCliTests(unittest.TestCase):
    def test_run_pipeline_auto_falls_back_to_local_backend_without_openai_key(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            target = tmp / "template_copy.tex"
            shutil.copy2(TEMPLATE_TEX, target)
            metanote = tmp / "lecture.txt"
            metanote.write_text(
                "[lecture]: Auto Local\n"
                "[def]: A finitely generated module has a radical quotient.\n"
                "[pf]: 用归纳法.\n",
                encoding="utf-8",
            )
            run_dir = tmp / "run"
            run_dir.mkdir()
            captured: dict[str, object] = {}
            original_generate = module.LocalFallbackBackend.generate

            def fake_make_run_dir(repo_root: Path, title: str, run_id: str) -> Path:
                return run_dir

            def fake_run_mpx_convert(source: Path, destination: Path) -> tuple[bool, str]:
                destination.write_text("# local fallback OCR\n\nNakayama lemma and radicals.\n", encoding="utf-8")
                return True, "mock local fallback mpx ok"

            def fake_compile_candidate(candidate_text: str, target_tex_path: Path, actual_run_dir: Path) -> tuple[bool, Path]:
                log_path = actual_run_dir / "compile.log"
                log_path.write_text("compile skipped in unit test\n", encoding="utf-8")
                return True, log_path

            def spy_generate(self, **kwargs):
                captured["reference_files"] = [str(path) for path in kwargs["reference_files"]]
                return original_generate(self, **kwargs)

            args = argparse.Namespace(
                command="dry-run",
                pdf=str(TEMPLATE_PDF),
                metanote=str(metanote),
                target_tex=str(target),
                title=None,
                backend=None,
                model=None,
                max_local_refs=0,
                no_web=False,
                enable_mathpix=False,
                use_mpx_cli=False,
                force=False,
            )
            with (
                mock.patch.object(module, "load_dotenv", return_value=None),
                mock.patch.object(module, "load_mpx_env", return_value=None),
                mock.patch.object(module, "is_mpx_cli_available", return_value=True),
                mock.patch.object(module, "make_run_dir", side_effect=fake_make_run_dir),
                mock.patch.object(module, "run_mpx_convert", side_effect=fake_run_mpx_convert),
                mock.patch.object(module, "compile_candidate", side_effect=fake_compile_candidate),
                mock.patch.object(module.LocalFallbackBackend, "generate", spy_generate),
                mock.patch.dict(module.os.environ, {"OPENAI_API_KEY": ""}, clear=False),
            ):
                module.os.environ.pop("OPENAI_API_KEY", None)
                result = module.run_pipeline(args)

            self.assertEqual(result, 0)
            self.assertTrue(any(path.endswith(".mpx.mmd") for path in captured["reference_files"]))
            manifest = (run_dir / "manifest.json").read_text(encoding="utf-8")
            self.assertIn('"backend": "local"', manifest)
            self.assertIn('"auto_local_fallback": true', manifest)
            self.assertIn('"auto_enabled": true', manifest)

    def test_run_pipeline_uses_mpx_cli_output_as_reference(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            target = tmp / "template_copy.tex"
            shutil.copy2(TEMPLATE_TEX, target)
            metanote = tmp / "lecture.txt"
            metanote.write_text(
                "[lecture]: MPX Test\n"
                "[sec]: Section A\n"
                "[def]: A mock definition.\n",
                encoding="utf-8",
            )
            run_dir = tmp / "run"
            run_dir.mkdir()
            captured: dict[str, object] = {}
            original_generate = module.MockBackend.generate

            def fake_make_run_dir(repo_root: Path, title: str, run_id: str) -> Path:
                return run_dir

            def fake_run_mpx_convert(source: Path, destination: Path) -> tuple[bool, str]:
                destination.write_text("# mock mpx output\n\nSome OCR text.\n", encoding="utf-8")
                return True, "mock mpx ok"

            def fake_compile_candidate(candidate_text: str, target_tex_path: Path, actual_run_dir: Path) -> tuple[bool, Path]:
                log_path = actual_run_dir / "compile.log"
                log_path.write_text("compile skipped in unit test\n", encoding="utf-8")
                return True, log_path

            def spy_generate(self, **kwargs):
                captured["reference_files"] = [str(path) for path in kwargs["reference_files"]]
                return original_generate(self, **kwargs)

            args = argparse.Namespace(
                command="dry-run",
                pdf=str(TEMPLATE_PDF),
                metanote=str(metanote),
                target_tex=str(target),
                title=None,
                backend="mock",
                model=None,
                max_local_refs=0,
                no_web=False,
                enable_mathpix=False,
                use_mpx_cli=True,
                force=False,
            )
            with (
                mock.patch.object(module, "make_run_dir", side_effect=fake_make_run_dir),
                mock.patch.object(module, "run_mpx_convert", side_effect=fake_run_mpx_convert),
                mock.patch.object(module, "compile_candidate", side_effect=fake_compile_candidate),
                mock.patch.object(module.MockBackend, "generate", spy_generate),
            ):
                result = module.run_pipeline(args)

            self.assertEqual(result, 0)
            self.assertIn(str(target), captured["reference_files"])
            self.assertTrue(any(path.endswith(".mpx.mmd") for path in captured["reference_files"]))
            manifest = (run_dir / "manifest.json").read_text(encoding="utf-8")
            self.assertIn('"use_mpx_cli": true', manifest)
            self.assertTrue(any(path.name.endswith(".mpx.mmd") for path in run_dir.iterdir()))

    @unittest.skipUnless(shutil.which("latexmk"), "latexmk is required for smoke tests")
    def test_dry_run_mock_backend_compiles_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            target = tmp / "template_copy.tex"
            shutil.copy2(TEMPLATE_TEX, target)
            metanote = tmp / "weyl.txt"
            metanote.write_text(
                "[lecture]: Smoke Lecture\n"
                "[sec]: Weyl's theorem\n"
                "[thm]: Every finite-dimensional representation of a semisimple Lie algebra is completely reducible.\n"
                "[pf]: Use a splitting short exact sequence argument.\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "dry-run",
                    "--backend",
                    "mock",
                    "--pdf",
                    str(TEMPLATE_PDF),
                    "--metanote",
                    str(metanote),
                    "--target-tex",
                    str(target),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr + "\n" + result.stdout)
            self.assertNotIn("METANOTE-AUTO-RUN-ID", target.read_text(encoding="utf-8"))

    @unittest.skipUnless(shutil.which("latexmk"), "latexmk is required for smoke tests")
    def test_run_mock_backend_blocks_duplicate_insertions(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            target = tmp / "template_copy.tex"
            shutil.copy2(TEMPLATE_TEX, target)
            metanote = tmp / "lecture.txt"
            metanote.write_text(
                "[lecture]: Duplicate Test\n"
                "[sec]: Section A\n"
                "[def]: A mock definition.\n",
                encoding="utf-8",
            )
            base_command = [
                sys.executable,
                str(SCRIPT),
                "run",
                "--backend",
                "mock",
                "--pdf",
                str(TEMPLATE_PDF),
                "--metanote",
                str(metanote),
                "--target-tex",
                str(target),
            ]
            first = subprocess.run(base_command, cwd=REPO_ROOT, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, msg=first.stderr + "\n" + first.stdout)
            second = subprocess.run(base_command, cwd=REPO_ROOT, capture_output=True, text=True)
            self.assertEqual(second.returncode, 2, msg=second.stderr + "\n" + second.stdout)
            self.assertIn("METANOTE-AUTO-RUN-ID", target.read_text(encoding="utf-8"))

    def test_run_pipeline_inserts_into_existing_empty_lecture_slot(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            target = tmp / "course.tex"
            target.write_text(
                "\\documentclass{book}\n"
                "\\begin{document}\n"
                "\\chapter{Lecture 6}\n\n"
                "\\chapter{Homework}\n"
                "\\end{document}\n",
                encoding="utf-8",
            )
            metanote = tmp / "lecture.md"
            metanote.write_text(
                "[lecture]: Lecture 6\n"
                "[sec]: Main Results\n"
                "[def]: A mock definition.\n",
                encoding="utf-8",
            )
            run_dir = tmp / "run"
            run_dir.mkdir()

            def fake_make_run_dir(repo_root: Path, title: str, run_id: str) -> Path:
                return run_dir

            def fake_compile_candidate(candidate_text: str, target_tex_path: Path, actual_run_dir: Path) -> tuple[bool, Path]:
                log_path = actual_run_dir / "compile.log"
                log_path.write_text("compile skipped in unit test\n", encoding="utf-8")
                return True, log_path

            args = argparse.Namespace(
                command="run",
                pdf=str(TEMPLATE_PDF),
                metanote=str(metanote),
                target_tex=str(target),
                title=None,
                backend="mock",
                model=None,
                max_local_refs=0,
                no_web=False,
                enable_mathpix=False,
                use_mpx_cli=False,
                force=False,
            )
            with (
                mock.patch.object(module, "make_run_dir", side_effect=fake_make_run_dir),
                mock.patch.object(module, "compile_candidate", side_effect=fake_compile_candidate),
            ):
                result = module.run_pipeline(args)

            self.assertEqual(result, 0)
            updated = target.read_text(encoding="utf-8")
            self.assertEqual(updated.count(r"\chapter{Lecture 6}"), 1)
            self.assertIn("% >>> METANOTE-AUTO-START", updated)
            self.assertLess(updated.index("% >>> METANOTE-AUTO-START"), updated.index(r"\chapter{Homework}"))

    def test_run_pipeline_blocks_non_empty_existing_lecture_slot(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            target = tmp / "course.tex"
            target.write_text(
                "\\documentclass{book}\n"
                "\\begin{document}\n"
                "\\chapter{Lecture 6}\n"
                "\\section{Existing Notes}\n"
                "Already filled.\n"
                "\\end{document}\n",
                encoding="utf-8",
            )
            metanote = tmp / "lecture.md"
            metanote.write_text(
                "[lecture]: Lecture 6\n"
                "[def]: A mock definition.\n",
                encoding="utf-8",
            )
            args = argparse.Namespace(
                command="run",
                pdf=str(TEMPLATE_PDF),
                metanote=str(metanote),
                target_tex=str(target),
                title=None,
                backend="mock",
                model=None,
                max_local_refs=0,
                no_web=False,
                enable_mathpix=False,
                use_mpx_cli=False,
                force=False,
            )
            result = module.run_pipeline(args)
            self.assertEqual(result, 2)

    def test_local_fallback_omits_editorial_notes_from_latex_body(self) -> None:
        module = load_module()
        metanote_text = (
            "[lecture]: Lecture 6\n"
            "[topic]: Source PDF: note.pdf\n"
            "OCR 基本能恢复 lecture skeleton.\n"
            "[thm]: A finitely generated projective module is determined by its radical quotient.\n"
            "请复核 exact statement.\n"
            "[pf]: 用归纳法\n"
            "请补充。\n"
            "[rmk]: Please verify the exact left/right convention in the notes.\n"
        )
        blocks = module.parse_metanote(metanote_text)
        style_profile = module.StyleProfile(
            sectioning_command="chapter",
            lecture_heading_command="chapter",
            lecture_heading_prefix="Lecture",
            available_envs=[],
            macros=[],
            sample_lines=[],
            summary="",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            result = module.LocalFallbackBackend().generate(
                pdf_path=TEMPLATE_PDF,
                metanote_text=metanote_text,
                blocks=blocks,
                style_profile=style_profile,
                title="Lecture 6",
                reference_files=[],
                run_dir=Path(tmpdir),
            )

        self.assertIn("Use induction.", result.latex_body)
        self.assertNotIn("Source PDF", result.latex_body)
        self.assertNotIn("OCR", result.latex_body)
        self.assertNotIn("Please verify", result.latex_body)
        self.assertNotIn("请补充", result.latex_body)
        self.assertNotIn("We follow the standard argument", result.latex_body)
        self.assertNotIn("The OCR transcript supports", result.latex_body)


if __name__ == "__main__":
    unittest.main()
