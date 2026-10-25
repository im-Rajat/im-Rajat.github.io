"""Bundle the Prompt Library's markdown files into prompts.json for the website.

Every file in categories/ is one category, named after the file (work.md -> "work").
To add a category, add a file. Inside a file, each prompt looks like this:

    ## Prompt title
    Optional note shown under the title, e.g. what to upload.
    #optional #tags

    ```
    The prompt text, exactly as it should be copied.
    Put fill-in parts in [square brackets].
    ```

- Prompts appear on the site in the same order as in the file.
- Anything before the first "##" (like the "# Title") is ignored, as are <!-- comments -->
  and anything between a prompt's code block and the next "##".
- If the prompt itself contains ``` use a longer fence (````) around it.
- A prompt's link is made from its title, so renaming a prompt changes its link.

Usage: python build.py [output_path]   (default: prompts.json next to this file)
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "categories"
CATEGORY_ORDER = ["personal", "work", "learning", "image"]  # any other files follow, A-Z
FENCE = re.compile(r"^(`{3,}|~{3,})")
TAGS = re.compile(r"^#[\w-]+(\s+#[\w-]+)*$")
COMMENT = re.compile(r"<!--.*?-->", re.S)


def warn(message):
    print(f"  warning: {message}", file=sys.stderr)


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "prompt"


def is_closing(line, fence):
    line = line.strip()
    return len(line) >= len(fence) and set(line) == {fence[0]}


def parse(path):
    """Yield (line_number, title, note, tags, prompt) for each "## " section of a category file."""
    text = path.read_text(encoding="utf-8")
    # Blank out <!-- comments --> but keep their line breaks so warnings point at the right line
    text = COMMENT.sub(lambda m: "\n" * m[0].count("\n"), text)
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        if not lines[i].startswith("## "):
            i += 1
            continue
        title, start = lines[i][3:].strip(), i + 1
        notes, tags, prompt = [], [], None
        i += 1
        while i < len(lines) and not lines[i].startswith("## "):
            line = lines[i].strip()
            fence = FENCE.match(line)
            if prompt is not None:
                pass
            elif fence:
                body = []
                i += 1
                while i < len(lines) and not is_closing(lines[i], fence[1]):
                    body.append(lines[i])
                    i += 1
                if i == len(lines):
                    warn(f"{path.name}:{start} '{title}': code block is never closed")
                prompt = "\n".join(body).strip("\n")
            elif TAGS.match(line):
                tags += [tag[1:] for tag in line.split()]
            elif line:
                notes.append(line)
            i += 1
        yield start, title, " ".join(notes), tags, prompt


def category_files():
    def order(path):
        key = path.stem.lower()
        return (CATEGORY_ORDER.index(key) if key in CATEGORY_ORDER else len(CATEGORY_ORDER), key)
    return sorted(SOURCE.glob("*.md"), key=order)


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "prompts.json"
    prompts, ids = [], set()
    for path in category_files():
        for line, title, note, tags, prompt in parse(path):
            if not prompt:
                warn(f"{path.name}:{line} '{title}': skipped, no ``` code block with the prompt")
                continue
            base = pid = slug(title)
            n = 2
            while pid in ids:
                pid, n = f"{base}-{n}", n + 1
            ids.add(pid)
            prompts.append({
                "id": pid,
                "title": title,
                "category": path.stem.lower(),
                "tags": tags,
                "description": note,
                "prompt": prompt,
            })
    out.write_text(json.dumps({"prompts": prompts}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Wrote {len(prompts)} prompts to {out}")


if __name__ == "__main__":
    main()
