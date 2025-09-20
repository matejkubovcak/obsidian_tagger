#!/usr/bin/env python3

import json
import re
import sys
from pathlib import Path
from typing import List
import requests

# Use the same functions from the main script
def extract_frontmatter(text: str) -> tuple[str, str]:
    frontmatter_re = re.compile(r"^---\n([\s\S]*?)\n---\n?", re.MULTILINE)
    match = frontmatter_re.match(text)
    if match:
        return match.group(0), text[match.end():]
    return "", text

def parse_existing_tags(frontmatter: str) -> List[str]:
    if not frontmatter:
        return []
    tags_line_re = re.compile(r"^tags:\s*(.*)$", re.MULTILINE)
    list_item_re = re.compile(r"^-\s*(.+)$")
    
    tags: List[str] = []
    tag_line_match = tags_line_re.search(frontmatter)
    if not tag_line_match:
        return []
    after = frontmatter[tag_line_match.end():]
    for line in after.splitlines():
        if line.strip() == "":
            continue
        if line.startswith("-"):
            m = list_item_re.match(line.strip())
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

def query_local_llm(content: str, existing_tags: List[str]) -> List[str]:
    existing_tags_str = ", ".join(existing_tags) if existing_tags else "none"
    
    prompt = f"""Analyze this note and suggest 3-5 relevant tags. Return ONLY a JSON array.

Guidelines:
- Use hierarchical tags with "/" (e.g., "tech/python", "wellness/meditation")  
- Common categories: tech, ml, finance, wellness, productivity, personal, work, learning
- Keep tags concise and lowercase
- Existing tags: {existing_tags_str}

Note content:
{content[:500]}...

Return only the JSON array:"""

    payload = {
        "model": "llama3.2",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_predict": 100,
        }
    }

    try:
        print(f"Querying LLM...")
        response = requests.post("http://localhost:11434/api/generate", json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        llm_response = result.get("response", "").strip()
        print(f"LLM response: {llm_response}")
        
        # Extract JSON array from response
        json_match = re.search(r'\[.*?\]', llm_response, re.DOTALL)
        if json_match:
            tags = json.loads(json_match.group())
            return [tag.strip() for tag in tags if isinstance(tag, str)]
        else:
            print("No JSON array found")
            return []
            
    except Exception as e:
        print(f"Error querying LLM: {e}")
        return []

def main():
    file_path = Path("obsidian_vault/001_daily_note.md")
    
    print(f"Processing: {file_path}")
    content = file_path.read_text()
    frontmatter, body = extract_frontmatter(content)
    existing_tags = parse_existing_tags(frontmatter)
    
    print(f"Existing tags: {existing_tags}")
    print(f"Content length: {len(body)} chars")
    
    llm_tags = query_local_llm(body, existing_tags)
    print(f"LLM suggested tags: {llm_tags}")

if __name__ == "__main__":
    main()