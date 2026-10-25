"""Bundle the Prompt Library's markdown files into prompts.json for the website.

Each file in prompts/ is one prompt: YAML frontmatter (title, category, tags,
description) followed by the prompt text. Pages CMS edits those files; the
publish workflow runs this script before `mkdocs build` so the site always
shows the latest prompts.

Usage: python build.py [output_path]   (default: prompts.json next to this file)
Needs PyYAML (already installed alongside mkdocs): pip install pyyaml
"""
import json
import re
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "prompts"
KNOWN_CATEGORIES = {"personal", "work", "learning", "image"}
FRONTMATTER = re.compile(r"^---\n(.*?)\n?---[ \t]*\n?(.*)$", re.S)


def load(path):
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    match = FRONTMATTER.match(text)
    meta, body = (yaml.safe_load(match[1]) or {}, match[2]) if match else ({}, text)

    title = str(meta.get("title") or "").strip()
    if not title:
        print(f"  skipped {path.name}: missing title", file=sys.stderr)
        return None

    category = str(meta.get("category") or "").strip().lower()
    if category not in KNOWN_CATEGORIES:
        print(f"  warning {path.name}: unknown category {category!r}", file=sys.stderr)

    tags = meta.get("tags") or []
    if isinstance(tags, str):
        tags = tags.split(",")

    return {
        "id": path.stem,
        "title": title,
        "category": category,
        "tags": [str(t).strip() for t in tags if str(t).strip()],
        "description": str(meta.get("description") or "").strip(),
        "prompt": body.strip("\n"),
    }


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "prompts.json"
    prompts = [p for p in map(load, sorted(SOURCE.glob("*.md"))) if p]
    prompts.sort(key=lambda p: p["title"].casefold())
    out.write_text(json.dumps({"prompts": prompts}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Wrote {len(prompts)} prompts to {out}")


if __name__ == "__main__":
    main()
