import re
import sys
from pathlib import Path
from typing import Dict, List, Set

# Simple keyword -> tag mapping (extend as needed)
KEYWORD_TAG_MAP: Dict[str, str] = {
    # wellness
    r"\bmeditat(e|ion|ing)\b": "wellness/meditation",
    r"\bmindful(ness)?\b": "wellness/mindfulness",
    r"\bgratitude\b": "wellness/gratitude",
    r"\brun(ning)?\b": "fitness/running",
    r"\bjournal(ing)?\b": "productivity/journaling",
    r"\bto-?do|task(s)?\b": "productivity/tasks",

    # finance / project
    r"\bbudget(ing)?\b": "finance/budgeting",
    r"\bexpense(s| tracking)?\b": "finance/expenses",
    r"\bsaving(s)?\b": "finance/saving",
    r"\binvest(ing|ment|ments)?\b": "finance/investing",
    r"\bbill(s)?\b": "finance/bills",
    r"\bportfolio\b": "finance/portfolio",

    # tech stack
    r"\bpython\b": "tech/python",
    r"\breact\b": "tech/react",
    r"\bpostgres(q|ql)?\b": "tech/postgres",
    r"\b(scikit-?learn|sklearn)\b": "ml/scikit-learn",
    r"\bpandas\b": "ml/pandas",
    r"\bnumpy\b": "ml/numpy",

    # ml concepts
    r"\bclassification\b": "ml/classification",
    r"\bregression\b": "ml/regression",
    r"\bclustering\b": "ml/clustering",
    r"\bdimensionality reduction\b": "ml/dimensionality-reduction",
    r"\bcross-?validation\b": "ml/cross-validation",
}

FRONTMATTER_RE = re.compile(r"^---\n([\s\S]*?)\n---\n?", re.MULTILINE)
TAGS_LINE_RE = re.compile(r"^tags:\s*(.*)$", re.MULTILINE)
LIST_ITEM_RE = re.compile(r"^-\s*(.+)$")


def extract_frontmatter(text: str) -> (str, str):
    match = FRONTMATTER_RE.match(text)
    if match:
        return match.group(0), text[match.end():]
    return "", text


def parse_existing_tags(frontmatter: str) -> List[str]:
    if not frontmatter:
        return []
    # naive parse: find 'tags:' section; supports inline or list
    tags: List[str] = []
    tag_line_match = TAGS_LINE_RE.search(frontmatter)
    if not tag_line_match:
        return []
    after = frontmatter[tag_line_match.end():]
    # collect list items until next non-list/non-indented line or end of fm
    for line in after.splitlines():
        if line.strip() == "":
            continue
        if line.startswith("-"):
            m = LIST_ITEM_RE.match(line.strip())
            if m:
                tags.append(m.group(1).strip())
        else:
            # inline YAML like: tags: [a, b]
            inline = tag_line_match.group(1).strip()
            if inline:
                inline = inline.strip("[]")
                tags += [t.strip() for t in inline.split(',') if t.strip()]
            break
    # fallback: if we had inline tags and no list items
    if not tags:
        inline = tag_line_match.group(1).strip()
        if inline:
            inline = inline.strip("[]")
            tags += [t.strip() for t in inline.split(',') if t.strip()]
    return tags


def render_frontmatter(updated_tags: List[str], existing_frontmatter: str) -> str:
    # Preserve other frontmatter fields naively by removing existing tags block
    body = existing_frontmatter
    if body:
        # remove entire tags line + following list items
        body_lines = body.splitlines()
        new_lines: List[str] = []
        skipping = False
        for line in body_lines:
            if not skipping and line.startswith("tags:"):
                skipping = True
                continue
            if skipping:
                if line.startswith("-") or line.strip() == "":
                    continue
                skipping = False
            if not skipping:
                new_lines.append(line)
        body = "\n".join(new_lines).strip()
        if body:
            body += "\n"
    # render tags list
    tags_block = "tags:\n" + "\n".join([f"- {t}" for t in updated_tags]) + "\n"
    return f"---\n{tags_block}{body}---\n"


def predict_tags(text: str) -> List[str]:
    text_lower = text.lower()
    matched: Set[str] = set()
    for pattern, tag in KEYWORD_TAG_MAP.items():
        if re.search(pattern, text_lower):
            matched.add(tag)
    # Optional: derive parent tags (e.g., ml/* -> ml)
    parents = {t.split('/')[0] for t in matched if '/' in t}
    matched |= parents
    return sorted(matched)


def process_markdown_file(path: Path) -> None:
    original = path.read_text(encoding="utf-8")
    frontmatter, content = extract_frontmatter(original)
    existing_tags = parse_existing_tags(frontmatter)
    predicted = predict_tags(content)
    merged: List[str] = sorted(set(existing_tags) | set(predicted))

    new_frontmatter = render_frontmatter(merged, frontmatter)
    updated = new_frontmatter + content
    if updated != original:
        path.write_text(updated, encoding="utf-8")
        print(f"Updated: {path}")
    else:
        print(f"No change: {path}")


def tag_vault(vault_dir: Path) -> None:
    md_files = sorted(vault_dir.rglob("*.md"))
    if not md_files:
        print("No markdown files found.")
        return
    for md in md_files:
        process_markdown_file(md)


if __name__ == "__main__":
    vault_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("obsidian_vault")
    if not vault_path.exists():
        print(f"Vault path not found: {vault_path}")
        sys.exit(1)
    tag_vault(vault_path)
