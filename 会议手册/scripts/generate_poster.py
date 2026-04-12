from __future__ import annotations

import argparse
import html
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
DOCX_PATH = ROOT / "List-0205(3).docx"
CSS_PATH = ROOT / "templates" / "poster.css"
OUTPUT_HTML = ROOT / "output" / "pdf" / "iccm_2026_poster_a4.html"

ASSET_PATHS = {
    "sustech_logo": ROOT / "assets" / "logos" / "sustech" / "sustech_combo3_english_horizontal.png",
    "sicm_logo": ROOT / "assets" / "logos" / "sicm-logo.png",
    "nsfc_logo": ROOT / "assets" / "logos" / "nsfc-eng-logo.jpg",
}

XML_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def normalize_text(value: str) -> str:
    return re.sub(r"[ \t]+", " ", value.replace("\xa0", " ").strip())


def path_uri(path: Path) -> str:
    return path.resolve().as_uri()


def extract_docx_paragraphs(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as archive:
        xml_bytes = archive.read("word/document.xml")

    root = ET.fromstring(xml_bytes)
    body = root.find("w:body", XML_NS)
    if body is None:
        raise ValueError(f"Could not find document body in {path}")

    lines: list[str] = []
    for paragraph in body.findall("w:p", XML_NS):
        text = "".join(
            node.text for node in paragraph.findall(".//w:t", XML_NS) if node.text
        )
        text = normalize_text(text)
        if text:
            lines.append(text)
    return lines


def parse_date_display(raw: str) -> str:
    compact = raw.split(":", 1)[-1].strip()
    match = re.fullmatch(r"(\d{4})\.(\d{1,2})\.(\d{1,2})-(\d{1,2})\.(\d{1,2})", compact)
    if not match:
        return compact

    year = int(match.group(1))
    start_month = int(match.group(2))
    start_day = int(match.group(3))
    end_month = int(match.group(4))
    end_day = int(match.group(5))

    month_names = {
        1: "January",
        2: "February",
        3: "March",
        4: "April",
        5: "May",
        6: "June",
        7: "July",
        8: "August",
        9: "September",
        10: "October",
        11: "November",
        12: "December",
    }

    if start_month == end_month:
        return f"{month_names[start_month]} {start_day}-{end_day}, {year}"

    return (
        f"{month_names[start_month]} {start_day} - "
        f"{month_names[end_month]} {end_day}, {year}"
    )


def parse_poster_content(lines: list[str]) -> dict[str, object]:
    try:
        organizers_index = lines.index("Organizers:")
        speakers_index = lines.index("Speakers:")
    except ValueError as exc:
        raise ValueError("Could not locate Organizers/Speakers markers in DOCX content") from exc

    title = lines[0]
    date_line = lines[1]
    organizers = lines[organizers_index + 1 : speakers_index]
    speakers = lines[speakers_index + 1 :]

    if not organizers or not speakers:
        raise ValueError("Poster content is missing organizers or speakers")

    return {
        "title": title,
        "date_label": date_line,
        "date_display": parse_date_display(date_line),
        "organizers": organizers,
        "speakers": speakers,
    }


def speaker_card(entry: str) -> str:
    name, _, affiliation = entry.partition(",")
    name = html.escape(normalize_text(name))
    affiliation = html.escape(normalize_text(affiliation))
    return (
        '<article class="speaker-item">'
        f'<h3 class="speaker-name">{name}</h3>'
        f'<p class="speaker-affiliation">{affiliation}</p>'
        "</article>"
    )


def organizer_line(entry: str) -> str:
    name, _, affiliation = entry.partition(",")
    name = html.escape(normalize_text(name))
    affiliation = html.escape(normalize_text(affiliation))
    return (
        '<div class="organizer-item">'
        f'<span class="organizer-name">{name}</span>'
        f'<span class="organizer-affiliation">{affiliation}</span>'
        "</div>"
    )


def render_html(content: dict[str, object], styles: str) -> str:
    logos = {key: path_uri(path) for key, path in ASSET_PATHS.items()}
    title = html.escape(str(content["title"]))

    organizers_html = "".join(organizer_line(item) for item in content["organizers"])
    speakers_html = "".join(speaker_card(item) for item in content["speakers"])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ICCM 2026 A4 Poster</title>
  <style>
{styles}
  </style>
  <script>
    window.__HANDBOOK_READY__ = true;
  </script>
</head>
<body>
  <main class="poster-page">
    <div class="poster-fill" aria-hidden="true"></div>
    <svg class="orbit-svg" viewBox="0 0 1000 1414" aria-hidden="true">
      <g fill="none" stroke="rgba(255,255,255,0.13)" stroke-width="2">
        <ellipse cx="680" cy="330" rx="270" ry="132" />
        <ellipse cx="695" cy="372" rx="348" ry="198" transform="rotate(-16 695 372)" />
        <ellipse cx="620" cy="426" rx="430" ry="252" transform="rotate(24 620 426)" />
        <ellipse cx="140" cy="1200" rx="350" ry="220" transform="rotate(38 140 1200)" />
      </g>
      <g fill="rgba(240,217,166,0.88)">
        <circle cx="706" cy="408" r="10" />
        <circle cx="870" cy="1120" r="4.5" />
        <circle cx="276" cy="1160" r="6" />
      </g>
    </svg>

    <section class="poster-shell">
      <div class="logo-band">
        <div class="logo-chip"><img src="{logos['sustech_logo']}" alt="SUSTech logo"></div>
        <div class="logo-chip sicm"><img src="{logos['sicm_logo']}" alt="SICM logo"></div>
        <div class="logo-chip"><img src="{logos['nsfc_logo']}" alt="NSFC logo"></div>
      </div>

      <header class="hero">
        <p class="hero-kicker">Conference Poster</p>
        <p class="hero-series">ICCM 2026</p>
        <h1 class="hero-title">{title}</h1>
        <p class="hero-date">{html.escape(str(content["date_display"]))}</p>
      </header>

      <section class="info-grid">
        <article class="info-panel info-panel-date">
          <div class="section-ribbon">Conference Date</div>
          <p class="date-large">{html.escape(str(content["date_display"]))}</p>
          <p class="date-raw">{html.escape(str(content["date_label"]))}</p>
        </article>

        <article class="info-panel info-panel-organizers">
          <div class="section-ribbon">Organizers</div>
          <div class="organizer-list">
            {organizers_html}
          </div>
        </article>
      </section>

      <section class="speakers-panel">
        <div class="section-ribbon speakers-ribbon">Invited Speakers</div>
        <div class="speaker-grid">
          {speakers_html}
        </div>
      </section>
    </section>
  </main>
</body>
</html>
"""


def build_poster(docx_path: Path, output_html: Path) -> Path:
    lines = extract_docx_paragraphs(docx_path)
    content = parse_poster_content(lines)
    styles = CSS_PATH.read_text(encoding="utf-8")
    html_text = render_html(content, styles)
    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_html.write_text(html_text, encoding="utf-8")
    return output_html


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate ICCM 2026 poster HTML from DOCX content.")
    parser.add_argument("--docx", type=Path, default=DOCX_PATH)
    parser.add_argument("--output-html", type=Path, default=OUTPUT_HTML)
    args = parser.parse_args()

    html_path = build_poster(args.docx, args.output_html)
    print(f"Wrote {html_path}")


if __name__ == "__main__":
    main()
