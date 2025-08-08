import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional
import requests

# Local LLM configuration
LLM_CONFIG = {
    "url": "http://localhost:11437/api/generate",  # Ollama default
    "model": "llama3.2",  # Change to your preferred model
    "temperature": 0.3,
}

FRONTMATTER_RE = re.compile(r"^---\n([\s\S]*?)\n---\n?", re.MULTILINE)
TAGS_LINE_RE = re.compile(r"^tags:\s*(.*)$", re.MULTILINE)
LIST_ITEM_RE = re.compile(r"^-\s*(.+)$")


def extract_frontmatter(text: str) -> tuple[str, str]:
    match = FRONTMATTER_RE.match(text)
    if match:
        return match.group(0), text[match.end():]
    return "", text


def parse_existing_tags(frontmatter: str) -> List[str]:
    if not frontmatter:
        return []
    tags: List[str] = []
    tag_line_match = TAGS_LINE_RE.search(frontmatter)
    if not tag_line_match:
        return []
    after = frontmatter[tag_line_match.end():]
    for line in after.splitlines():
        if line.strip() == "":
            continue
        if line.startswith("-"):
            m = LIST_ITEM_RE.match(line.strip())
            if m:
                tags.append(m.group(1).strip())
        else:
            inline = tag_line_match.group(1).strip()
            if inline:
                inline = inline.strip("[]")
                tags += [t.strip() for t in inline.split(',') if t.strip()]
            break
    if not tags:
        inline = tag_line_match.group(1).strip()
        if inline:
            inline = inline.strip("[]")
            tags += [t.strip() for t in inline.split(',') if t.strip()]
    return tags


def render_frontmatter(updated_tags: List[str], existing_frontmatter: str) -> str:
    body = existing_frontmatter
    if body:
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
    tags_block = "tags:\n" + "\n".join([f"- {t}" for t in updated_tags]) + "\n"
    return f"---\n{tags_block}{body}---\n"


def query_local_llm(content: str, existing_tags: List[str]) -> List[str]:
    """Query local LLM for tag suggestions"""
    
    existing_tags_str = ", ".join(existing_tags) if existing_tags else "none"
    
    # Truncate content to avoid huge prompts
    content_snippet = content[:800] if len(content) > 800 else content
    
    prompt = f"""Analyze this note and suggest 3-5 tags. Return only JSON array.

Categories: tech, ml, finance, wellness, productivity, personal, work, learning
Use "/" for hierarchy: tech/python, wellness/meditation

Existing: {existing_tags_str}

Content: {content_snippet}

JSON array only:"""

    payload = {
        "model": LLM_CONFIG["model"],
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": LLM_CONFIG["temperature"],
            "num_predict": 80,
        }
    }

    try:
        print(f"Querying LLM for {len(content)} characters...")
        response = requests.post(LLM_CONFIG["url"], json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        llm_response = result.get("response", "").strip()
        
        # Extract JSON array from response
        try:
            # Try to find JSON array in the response
            import re
            json_match = re.search(r'\[.*?\]', llm_response, re.DOTALL)
            if json_match:
                tags = json.loads(json_match.group())
                return [tag.strip() for tag in tags if isinstance(tag, str)]
            else:
                # Fallback: try to parse the entire response as JSON
                tags = json.loads(llm_response)
                return [tag.strip() for tag in tags if isinstance(tag, str)]
        except json.JSONDecodeError:
            print(f"Failed to parse LLM response as JSON: {llm_response}")
            return []
            
    except requests.exceptions.RequestException as e:
        print(f"Error querying local LLM: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []


def process_markdown_file(path: Path) -> None:
    try:
        print(f"Processing: {path.name}")
        original = path.read_text(encoding="utf-8")
        frontmatter, content = extract_frontmatter(original)
        existing_tags = parse_existing_tags(frontmatter)
        
        print(f"  Existing tags: {len(existing_tags)} found")
        
        # Get LLM suggestions
        llm_tags = query_local_llm(content, existing_tags)
        
        if llm_tags:
            print(f"  LLM suggested: {llm_tags}")
            # Merge existing and LLM-suggested tags
            merged: List[str] = sorted(set(existing_tags) | set(llm_tags))
            
            new_frontmatter = render_frontmatter(merged, frontmatter)
            updated = new_frontmatter + content
            
            if updated != original:
                path.write_text(updated, encoding="utf-8")
                print(f"  ✓ Updated: {path.name}")
            else:
                print(f"  - No change: {path.name}")
        else:
            print(f"  ! No LLM tags generated for {path.name}")
    except Exception as e:
        print(f"  ✗ Error processing {path.name}: {e}")


def tag_vault(vault_dir: Path) -> None:
    md_files = sorted(vault_dir.rglob("*.md"))
    if not md_files:
        print("No markdown files found.")
        return
    
    print(f"Using LLM: {LLM_CONFIG['model']} at {LLM_CONFIG['url']}")
    
    for md in md_files:
        process_markdown_file(md)


if __name__ == "__main__":
    vault_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("obsidian_vault")
    if not vault_path.exists():
        print(f"Vault path not found: {vault_path}")
        sys.exit(1)
    tag_vault(vault_path)
