"""Turn README.md into websites.json for the Useful Websites page (index.html).

README.md stays the only file to edit. The parser is forgiving, so keep writing it as usual:

    ### Category name :
    - Site name: what it does    -    <https://example.com>
    - What it does    →    https://example.com | <https://mirror.example.com>
    - A tip with no link, `code` is shown as code
        - indented lines are kept as part of the item above

- "### " starts a category. Anything before the first one (the "# Title", intro) is ignored.
- Every https:// link in an item is picked up, with or without <angle brackets>.
- Text before the first link is the label. "Name: description" is split into the two parts.
- Items without a link are shown as tips.
- <hr>, blank lines and other lines are ignored.

Usage: python build.py [output_path]   (default: websites.json next to this file)
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SECTION = re.compile(r"^#{2,3}\s+(.*?)[\s:]*$")
ITEM = re.compile(r"^[-*]\s+(.*)$")
SUB_ITEM = re.compile(r"^\s+[-*]\s+(.*)$")
URL = re.compile(r"https?://[^\s<>|]+")
SEPARATOR = re.compile(r"\s+(?:-|→|–|—)\s+|\t+-?\t*")
NAME_MAX = 40  # "Name: description" only splits when the name part is short


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "section"


def tidy(text):
    """Collapse runs of spaces/tabs and treat ```code``` like `code`."""
    return re.sub(r"\s{2,}", " ", text.replace("```", "`")).strip()


def tidy_label(text):
    """Also turn the README's mixed separators ("  -  ", tabs, "→") into one " — "."""
    return tidy(SEPARATOR.sub(" — ", text)).strip(" —")


def make_item(line, extra):
    links = [url.rstrip(".,;") for url in URL.findall(line)]
    if not links:
        # Tips keep their text as written: a "-" in a tip can be part of the trick itself
        text = "\n".join([tidy(line)] + extra)
        return {"title": "", "desc": text, "links": []}

    label = tidy_label(line[: line.find(links[0])].rstrip(" \t<"))
    label = label.rstrip(" -→–—|&:")
    title, desc = label, ""
    name, sep, rest = label.partition(": ")
    if sep and rest and len(name) <= NAME_MAX:
        title, desc = name.strip(), rest.strip()
    if extra:
        desc = " ".join([desc] + extra).strip()
    return {"title": title, "desc": desc, "links": links}


def parse(text):
    sections, ids = [], set()
    pending = None  # (line, extra lines) of the item being read

    def flush():
        nonlocal pending
        if pending and sections:
            sections[-1]["items"].append(make_item(*pending))
        pending = None

    for raw in text.replace("\r\n", "\n").split("\n"):
        line = raw.rstrip()
        if heading := SECTION.match(line):
            flush()
            name = heading[1].strip()
            base = sid = slug(name)
            n = 2
            while sid in ids:
                sid, n = f"{base}-{n}", n + 1
            ids.add(sid)
            sections.append({"id": sid, "name": name, "items": []})
        elif item := ITEM.match(line):
            flush()
            pending = (item[1], [])
        elif pending and (sub := SUB_ITEM.match(line)):
            pending[1].append("• " + tidy(sub[1]))
        elif pending and line[:1] in (" ", "\t") and line.strip():
            pending[1].append(tidy(line))
    flush()
    return [s for s in sections if s["items"]]


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "websites.json"
    sections = parse((HERE / "README.md").read_text(encoding="utf-8"))
    out.write_text(json.dumps({"sections": sections}, ensure_ascii=False, indent=1), encoding="utf-8")
    total = sum(len(s["items"]) for s in sections)
    print(f"Wrote {total} items in {len(sections)} sections to {out}")


if __name__ == "__main__":
    main()
